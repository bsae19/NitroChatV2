#!/usr/bin/env python3
# Script consommateur Spark qui lit depuis Kafka et sauvegarde dans Hive avec génération d'ID unique (UUID)

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, current_timestamp, udf
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
import uuid

@udf(returnType=StringType())
def uuid_udf():
    return str(uuid.uuid4())


def main():
    spark = SparkSession.builder \
        .appName("KafkaUsersAndMessagesToHive") \
        .enableHiveSupport() \
        .config("spark.sql.warehouse.dir", "/user/hive/warehouse") \
        .config("hive.metastore.uris", "thrift://hive-metastore:9083") \
        .config("spark.sql.session.timeZone", "UTC") \
        .config("hive.exec.dynamic.partition", "true") \
        .config("hive.exec.dynamic.partition.mode", "nonstrict") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    user_schema = StructType([
        StructField("nom", StringType(), True),
        StructField("email", StringType(), True),
        StructField("password", StringType(), True),
        StructField("date_inscription", TimestampType(), True)
    ])

    message_schema = StructType([
        StructField("message", StringType(), True),
        StructField("Created_At", TimestampType(), True),
        StructField("user_id", StringType(), True),
        StructField("chat_id", StringType(), True),
        StructField("type", StringType(), True)
        # StructField("valide", StringType(), True)
    ])

    df_users = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "save_user") \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    df_messages = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "message_ia") \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    json_df_users = df_users.selectExpr("CAST(value AS STRING) AS raw_data")
    json_df_messages = df_messages.selectExpr("CAST(value AS STRING) AS raw_data")

    def process_generic_batch(batch_df, batch_id, schema, table, error_table):
        try:
            if batch_df.isEmpty():
                print(f"\n--- BATCH {batch_id} ({table.upper()}) VIDE ---")
                return

            print(f"\n--- DONNÉES BRUTES ({table.upper()}) (BATCH {batch_id}) ---")
            batch_df.select("raw_data").show(5, truncate=False)

            parsed_df = batch_df.select(
                from_json(col("raw_data"), schema, {"mode": "PERMISSIVE", "columnNameOfCorruptRecord": "corrupt_record"}).alias("data"),
                col("raw_data"),
                current_timestamp().alias("processed_time")
            )

            final_df = parsed_df.select(
                uuid_udf().alias("id"),
                *[col(f"data.{f.name}") for f in schema.fields],
                when(col(f"data.{schema.fields[0].name}").isNull(), col("raw_data")).alias("corrupt_record"),
                col("processed_time")
            )

            valid_df = final_df.filter(col("corrupt_record").isNull())
            invalid_df = final_df.filter(col("corrupt_record").isNotNull())

            valid_cnt = valid_df.count()
            invalid_cnt = invalid_df.count()

            print(f"Enregistrements: {valid_cnt} valides, {invalid_cnt} invalides")

            if valid_cnt > 0:
                print("Échantillon des données valides:")
                valid_df.select("*").show(3, truncate=False)
                spark.sql(f"""
                    CREATE TABLE IF NOT EXISTS default.{table} (
                        id STRING,
                        {', '.join([f'{f.name} {f.dataType.simpleString()}' for f in schema.fields])}
                    )
                    USING hive
                """)
                valid_df.select(["id"] + [f.name for f in schema.fields]) \
                    .write.format("hive").mode("append").insertInto(f"default.{table}")
                print(f"✓ Enregistrements insérés dans la table '{table}'")

            if invalid_cnt > 0:
                print(f"⚠️ {invalid_cnt} enregistrements invalides détectés:")
                invalid_df.select("corrupt_record").show(3, truncate=False)
                spark.sql(f"""
                    CREATE TABLE IF NOT EXISTS default.{error_table} (
                        corrupt_record STRING,
                        processed_time TIMESTAMP
                    )
                    USING hive
                """)
                invalid_df.select("corrupt_record", "processed_time") \
                    .write.format("hive").mode("append").insertInto(f"default.{error_table}")
                print(f"✓ Enregistrements invalides sauvegardés dans '{error_table}'")

        except Exception as e:
            import traceback
            print(f"Erreur critique dans batch {table}: {str(e)}")
            print(traceback.format_exc())

    users_stream = json_df_users.writeStream \
        .foreachBatch(lambda df, bid: process_generic_batch(df, bid, user_schema, "users", "users_errors")) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/checkpoints/users") \
        .trigger(processingTime="30 seconds") \
        .start()

    messages_stream = json_df_messages.writeStream \
        .foreachBatch(lambda df, bid: process_generic_batch(df, bid, message_schema, "messages", "messages_errors")) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/checkpoints/messages") \
        .trigger(processingTime="30 seconds") \
        .start()

    print("=== Stream Kafka -> Hive lancé pour utilisateurs et messages ===")

    try:
        spark.streams.awaitAnyTermination()
    except KeyboardInterrupt:
        users_stream.stop()
        messages_stream.stop()
        print("Stream arrêté.")
    finally:
        spark.stop()
        print("Session Spark terminée.")


if __name__ == "__main__":
    main()
