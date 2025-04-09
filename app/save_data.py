from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, expr, lit, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

def main():
    spark = SparkSession.builder \
        .appName("KafkaToHiveConsumer") \
        .enableHiveSupport() \
        .config("hive.metastore.uris", "thrift://hive-metastore:9083") \
        .config("spark.sql.session.timeZone", "UTC") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Schémas
    user_schema = StructType([
        StructField("user_id", IntegerType(), True),
        StructField("nom", StringType(), True),
        StructField("email", StringType(), True),
        StructField("date_inscription", TimestampType(), True)
    ])

    message_schema = StructType([
        StructField("id", StringType(), True),
        StructField("message", StringType(), True),
        StructField("Created_At", StringType(), True),
        StructField("user_id", StringType(), True),
        StructField("chat_id", StringType(), True),
        StructField("type", StringType(), True)
    ])

    # Lecture Kafka
    def read_kafka(topic):
        return spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("subscribe", topic) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load() \
            .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING) AS raw_data")

    users_df = read_kafka("topic2")
    messages_df = read_kafka("message_ia")

    # Fonctions de traitement par batch
    def process_batch(df, schema, table_name, error_table, partitioned=False):
        def process(df, batch_id):
            try:
                if df.isEmpty():
                    print(f"\n--- BATCH {batch_id} {table_name.upper()} VIDE ---")
                    return

                parsed = df.select(
                    col("raw_data"),
                    from_json(col("raw_data"), schema, {"mode": "PERMISSIVE", "columnNameOfCorruptRecord": "corrupt_record"}).alias("data"),
                    current_timestamp().alias("processed_time")
                )

                final = parsed.select("data.*", when(col("data.*").isNull(), col("raw_data")).alias("corrupt_record"), col("processed_time"))

                valid = final.filter(col(final.columns[0]).isNotNull())
                invalid = final.filter(col(final.columns[0]).isNull())

                if valid.count() > 0:
                    spark.sql(f"""
                        CREATE TABLE IF NOT EXISTS default.{table_name} (
                            {', '.join([f'{f.name} {f.dataType.simpleString()}' for f in schema.fields])}
                        ) {'PARTITIONED BY (year INT, month INT, day INT)' if partitioned else ''}
                        USING hive
                    """)

                    if partitioned:
                        valid = valid.withColumn("year", expr("year(processed_time)")) \
                                     .withColumn("month", expr("month(processed_time)")) \
                                     .withColumn("day", expr("dayofmonth(processed_time)"))
                        valid.write.format("hive").mode("append").partitionBy("year", "month", "day").insertInto(f"default.{table_name}")
                    else:
                        valid.write.format("hive").mode("append").insertInto(f"default.{table_name}")

                    print(f"✓ {valid.count()} enregistrements insérés dans {table_name}")

                if invalid.count() > 0:
                    spark.sql(f"""
                        CREATE TABLE IF NOT EXISTS default.{error_table} (
                            corrupt_record STRING,
                            processed_time TIMESTAMP
                        )
                        USING hive
                    """)
                    invalid.select("corrupt_record", "processed_time").write \
                        .format("hive") \
                        .mode("append") \
                        .insertInto(f"default.{error_table}")
                    print(f"✓ {invalid.count()} erreurs insérées dans {error_table}")

            except Exception as e:
                import traceback
                print(f"Erreur batch {table_name}: {str(e)}")
                print(traceback.format_exc())
        return process

    # Streams
    users_stream = users_df.writeStream.foreachBatch(
        process_batch(users_df, user_schema, "users", "users_errors", partitioned=True)
    ).outputMode("append").option("checkpointLocation", "/tmp/checkpoints/users").trigger(processingTime="30 seconds").start()

    messages_stream = messages_df.writeStream.foreachBatch(
        process_batch(messages_df, message_schema, "messages", "messages_errors")
    ).outputMode("append").option("checkpointLocation", "/tmp/checkpoints/messages").trigger(processingTime="30 seconds").start()

    print("\n=== Spark Kafka -> Hive pipeline lancé ===")
    print("- topic2 => users")
    print("- message_ia => messages")

    try:
        spark.streams.awaitAnyTermination()
    except KeyboardInterrupt:
        users_stream.stop()
        messages_stream.stop()
        print("\nArrêt des streams Spark.")
    finally:
        spark.stop()
        print("Session Spark arrêtée.")

if __name__ == "__main__":
    main()
