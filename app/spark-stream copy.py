#!/usr/bin/env python3
# Script consommateur Spark qui lit depuis Kafka et sauvegarde dans Hive avec génération d'ID unique (UUID)

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, current_timestamp, udf, to_json, struct, collect_list
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
        StructField("email", StringType(), True),
        StructField("password", StringType(), True)
    ])

    full_user_schema = StructType([
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

                if topic_name == "get_all_messages":
                    try:
                        messages_df = spark.read.table("default.messages")
                        metadata_df = spark.read.table("default.message_metadata")
                        result_df = messages_df.join(metadata_df, messages_df.id == metadata_df.id_message, "left")
                        aggregated = result_df.selectExpr("CAST(NULL AS STRING) AS key", "to_json(collect_list(struct(*))) AS value")
                        result_df_formatted = aggregated
                    except Exception as e:
                        print(f"Erreur lors de la lecture des tables Hive: {e}")
                        empty_df = spark.createDataFrame([Row(key=None, value="[]")], ["key", "value"])
                        result_df_formatted = empty_df

                elif topic_name == "get_users":
                    import json
                    import pyspark.sql.functions as F

                    credentials = batch_df.selectExpr("CAST(value AS STRING) as json").select(from_json(col("json"), user_schema).alias("data"))
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

    get_users_stream = handle_request("get_users", "users", "send_users")
    get_messages_stream = handle_request("get_all_messages", "messages", "send_all_messages")

    print("=== Stream Kafka -> Hive lancé pour les requêtes utilisateurs/messages ===")

    try:
        spark.streams.awaitAnyTermination()
    except KeyboardInterrupt:   
        get_users_stream.stop()
        get_messages_stream.stop()
        print("Stream arrêté.")
    finally:
        spark.stop()
        print("Session Spark terminée.")

if __name__ == "__main__":
    main()
