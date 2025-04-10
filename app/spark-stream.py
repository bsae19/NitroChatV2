#!/usr/bin/env python3
# Script consommateur Spark qui lit depuis Kafka et sauvegarde dans Hive avec génération d'ID unique (UUID)

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, current_timestamp, udf, to_json, struct, collect_list, lit, expr
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.streaming import DataStreamWriter
from pyspark.sql import Row
import uuid

@udf(returnType=StringType())
def uuid_udf():
    return str(uuid.uuid4())

def main():
    spark = SparkSession.builder \
        .appName("KafkaUsersAndMessagesToHive") \
        .enableHiveSupport() \
        .config("hive.metastore.uris", "thrift://hive-metastore:9083") \
        .config("spark.sql.session.timeZone", "UTC") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    user_schema = StructType([
        StructField("nom", StringType(), True),
        StructField("email", StringType(), True),
        StructField("password", StringType(), True),
        StructField("date_inscription", TimestampType(), True)
    ])
    
    user_login = StructType([
        StructField("email", StringType(), True),
        StructField("password", StringType(), True)
    ])

    message_schema = StructType([
        StructField("message", StringType(), True),
        StructField("Created_At", TimestampType(), True),
        StructField("user_id", StringType(), True),
        StructField("chat_id", StringType(), True),
        StructField("type", StringType(), True)
    ])
    message_schema2 = StructType([
        StructField("message", StringType(), True),
        StructField("Created_At", TimestampType(), True),
        StructField("user_id", StringType(), True),
        StructField("chat_id", StringType(), True),
        StructField("type", StringType(), True),
        StructField("valide", StringType(), True),
    ])

    metadata_schema = StructType([
        StructField("id_message", StringType(), True),
        StructField("valide", StringType(), True),
        StructField("date", TimestampType(), True)
    ])

    df_users = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "register") \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    df_messages = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "ia_message") \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    df_metadata = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "check_message") \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    json_df_users = df_users.selectExpr("CAST(value AS STRING) AS raw_data")
    json_df_messages = df_messages.selectExpr("CAST(value AS STRING) AS raw_data")
    json_df_metadata = df_metadata.selectExpr("CAST(value AS STRING) AS raw_data")

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
                print("\n--- Données valides envoyées sur Kafka ---")
                valid_df.selectExpr("CAST(NULL AS STRING) AS key", "to_json(struct(*)) AS value").show(5, False)
                spark.sql(f"""
                    CREATE TABLE IF NOT EXISTS default.{table} (
                        id STRING,
                        {', '.join([f'{f.name} {f.dataType.simpleString()}' for f in schema.fields])}
                    )
                    CLUSTERED BY (id) INTO 2 BUCKETS
                    STORED AS ORC
                    LOCATION 'hdfs://namenode:8020/user/hive/warehouse/{table}'
                """)
                valid_df.selectExpr("CAST(NULL AS STRING) AS key", "to_json(struct(*)) AS value") \
                    .write.format("kafka") \
                    .option("kafka.bootstrap.servers", "kafka:9092") \
                    .option("topic", f"{table}_save") \
                    .save()
                valid_df.select(["id"] + [f.name for f in schema.fields]) \
                    .write.format("hive").mode("append").insertInto(f"default.{table}")
                print(f"✓ Enregistrements insérés dans la table '{table}' et envoyés sur Kafka")

            if invalid_cnt > 0:
                print(f"⚠️ {invalid_cnt} enregistrements invalides détectés:")
                invalid_df.select("corrupt_record").show(3, truncate=False)
                spark.sql(f"""
                    CREATE TABLE IF NOT EXISTS default.{error_table} (
                        corrupt_record STRING,
                        processed_time TIMESTAMP
                    )
                    STORED AS ORC
                    LOCATION 'hdfs://namenode:8020/user/hive/warehouse/{table}'
                """)
                invalid_df.select("corrupt_record", "processed_time") \
                    .write.format("hive").mode("append").insertInto(f"default.{error_table}")
                print(f"✓ Enregistrements invalides sauvegardés dans '{error_table}'")

        except Exception as e:
            import traceback
            print(f"Erreur critique dans batch {table}: {str(e)}")
            print(traceback.format_exc())

    def handle_request(topic_name: str, table: str, response_topic: str):
        df = spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("subscribe", topic_name) \
            .option("startingOffsets", "latest") \
            .load()

        def respond_if_ping(batch_df, batch_id):
            if not batch_df.isEmpty():
                print(f"\nPing reçu sur '{topic_name}' (batch {batch_id})")
                batch_df.selectExpr("CAST(value AS STRING)").show(5, False)

                if topic_name == "send_all_messages":
                    try:
                        # messages_df = spark.read.table("default.messages")
                        # metadata_df = spark.read.table("default.message_metadata")
                        # result_df = messages_df.join(metadata_df, messages_df.id == metadata_df.id_message, "left")
                        # aggregated = result_df.selectExpr("CAST(NULL AS STRING) AS key", "to_json(collect_list(struct(*))) AS value")
                        # result_df_formatted = aggregated
                        messages_df = spark.read.table("default.messages").alias("m")
                        metadata_df = spark.read.table("default.message_metadata").alias("md")
                        joined_df = messages_df.join(metadata_df, col("m.id") == col("md.id_message"), "left")
                        joined_df = joined_df.select(
                            [
                                col("m.id").alias("message_id"),
                                col("m.message"),
                                col("m.Created_At"),
                                col("m.user_id"),
                                col("m.chat_id"),
                                col("m.type"),
                                when(col("md.valide").isNull(), lit("false")).otherwise(col("md.valide")).alias("valide")
                            ]
                        )
                        result_json = joined_df.select(to_json(struct("message_id", "message", "Created_At", "user_id", "chat_id", "type", "valide")).alias("value"))
                        parsed_values = result_json.selectExpr("CAST(NULL AS STRING) as key", "from_json(value, '{}') as parsed".format(message_schema2.simpleString()))
                        aggregated = parsed_values.groupBy("key").agg(expr("to_json(collect_list(parsed)) as value"))
                        result_df_formatted = aggregated.select("key", "value")
                    except Exception as e:
                        print(f"Erreur lors de la lecture des tables Hive: {e}")
                        empty_df = spark.createDataFrame([Row(key=None, value="[]")], ["key", "value"])
                        result_df_formatted = empty_df

                elif topic_name == "send_users":
                    import json
                    import pyspark.sql.functions as F

                    credentials = batch_df.selectExpr("CAST(value AS STRING) as json").select(from_json(col("json"), user_login).alias("data"))
                    credentials = credentials.select("data.*")

                    try:
                        users_df = spark.read.table("default.users")
                        matched_users = users_df.join(credentials, on=["email", "password"], how="inner")

                        if matched_users.count() > 0:
                            aggregated = users_df.selectExpr("CAST(NULL AS STRING) AS key", "to_json(collect_list(struct(*))) AS value")
                            result_df_formatted = aggregated
                        else:
                            error_row = Row(key=None, value=json.dumps({"error": "Utilisateur non trouvé"}))
                            result_df_formatted = spark.createDataFrame([error_row], ["key", "value"])
                    except Exception as e:
                        print(f"Erreur lors de la vérification des utilisateurs: {e}")
                        empty_df = spark.createDataFrame([Row(key=None, value="[]")], ["key", "value"])
                        result_df_formatted = empty_df

                else:
                    try:
                        result_df = spark.read.table(f"default.{table}")
                        result_json = result_df.select(to_json(struct("*")).alias("value"))
                        aggregated = result_json.selectExpr("CAST(NULL AS STRING) AS key", "collect_list(value) as value_list")
                        result_df_formatted = aggregated.selectExpr("key", "to_json(value_list) as value")
                    except Exception as e:
                        print(f"Table '{table}' introuvable: {e}")
                        empty_df = spark.createDataFrame([Row(key=None, value="[]")], ["key", "value"])
                        result_df_formatted = empty_df

                print(f"--- Données envoyées sur topic '{response_topic}' ---")
                result_df_formatted.show(5, False)

                result_df_formatted.write \
                    .format("kafka") \
                    .option("kafka.bootstrap.servers", "kafka:9092") \
                    .option("topic", response_topic) \
                    .save()

        return df.writeStream.foreachBatch(respond_if_ping).start()

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

    metadata_stream = json_df_metadata.writeStream \
        .foreachBatch(lambda df, bid: process_generic_batch(df, bid, metadata_schema, "message_metadata", "metadata_errors")) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/checkpoints/metadata") \
        .trigger(processingTime="30 seconds") \
        .start()

    get_users_stream = handle_request("send_users", "users", "get_users")
    get_messages_stream = handle_request("send_all_messages", "message_metadata", "get_all_messages")

    print("=== Stream Kafka -> Hive lancé pour utilisateurs, messages et metadata ===")

    try:
        spark.streams.awaitAnyTermination()
    except KeyboardInterrupt:
        users_stream.stop()
        messages_stream.stop()
        metadata_stream.stop()
        get_users_stream.stop()
        get_messages_stream.stop()
        print("Stream arrêté.")
    finally:
        spark.stop()
        print("Session Spark terminée.")

if __name__ == "__main__":
    main()
