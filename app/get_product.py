#!/usr/bin/env python3
# Script consommateur Spark qui lit depuis deux topics Kafka et sauvegarde dans des tables Hive
# Version optimisée avec meilleure gestion des formats de données et des erreurs

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, expr, lit, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

def main():
    # Créer une session Spark avec support Hive
    spark = SparkSession.builder \
    .appName("KafkaToHiveConsumer") \
    .enableHiveSupport() \
    .config("hive.metastore.uris", "thrift://hive-metastore:9083") \
    .config("spark.sql.session.timeZone", "UTC") \
    .getOrCreate()
    
    # Réduire le niveau de log pour une meilleure lisibilité
    spark.sparkContext.setLogLevel("WARN")
    
    # Schéma des données produit
    produit_schema = StructType([
        StructField("produit_id", IntegerType(), True),
        StructField("nom", StringType(), True),
        StructField("categorie", StringType(), True),
        StructField("prix", DoubleType(), True)
    ])
    
    # Configurer les flux de lecture Kafka pour les produits (topic1)
    df_produits = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "topic1") \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Convertir les valeurs binaires en chaînes
    json_df_produits = df_produits.selectExpr("CAST(key AS STRING) AS key", "CAST(value AS STRING) AS value")
    json_df_users = df_users.selectExpr("CAST(key AS STRING) AS key", "CAST(value AS STRING) AS value")
    
    # TRAITEMENT DES DONNÉES PRODUITS (TOPIC1)
    # ---------------------------------------
    def process_produits_batch(batch_df, batch_id):
        try:
            if batch_df.isEmpty():
                print(f"\n--- BATCH {batch_id} PRODUITS VIDE ---")
                return
                
            print(f"\n--- DONNÉES BRUTES PRODUITS (BATCH {batch_id}) ---")
            batch_df.select("raw_data").show(13, truncate=False)
            
            # Parser les données JSON avec gestion des erreurs
            parsed_df = batch_df.select(
                from_json(col("raw_data"), produit_schema, {"mode": "PERMISSIVE", "columnNameOfCorruptRecord": "corrupt_record"}).alias("data")
            )
            
            # Extraire et valider les champs
            final_df = parsed_df.select(
                col("data.produit_id").cast(IntegerType()).alias("produit_id"),
                col("data.nom").cast(StringType()).alias("nom"),
                col("data.categorie").cast(StringType()).alias("categorie"),
                col("data.prix").cast(DoubleType()).alias("prix")
            )
            
            # Séparer les enregistrements valides et invalides
            valid_df = final_df.filter(col("produit_id").isNotNull())
            invalid_df = final_df.filter(col("produit_id").isNull())
            
            valid_cnt = valid_df.count()
            invalid_cnt = invalid_df.count()
            total_cnt = valid_cnt + invalid_cnt
            
            print(f"Enregistrements: {valid_cnt} valides, {invalid_cnt} invalides, {total_cnt} total")
            
            # Traiter les enregistrements valides
            if valid_cnt > 0:
                print("Échantillon des données valides:")
                valid_df.select("produit_id", "nom", "categorie", "prix").show(3, truncate=False)
                
                # Sauvegarder dans Hive
                try:
                    # Créer la table si elle n'existe pas
                    spark.sql("""
    CREATE EXTERNAL TABLE IF NOT EXISTS default.produits2 (
        produit_id INT,
        nom STRING,
        categorie STRING,
        prix DOUBLE
        )
    USING hive
    LOCATION 'hdfs://namenode:8020/user/hive/warehouse/produits2'
""")
                    
                    
                    
                    valid_df.write \
                        .format("hive") \
                        .mode("append") \
                        .insertInto("default.produits2")
                    print(f"✓ {valid_cnt} enregistrements sauvegardés dans la table Hive 'produits'")
                except Exception as e:
                    print(f"✗ Erreur lors de la sauvegarde dans Hive: {str(e)}")
            
            # Traiter les enregistrements invalides
            if invalid_cnt > 0:
                print(f"⚠️ {invalid_cnt} enregistrements invalides détectés:")
                invalid_df.select("corrupt_record").show(3, truncate=False)
                
                # Optionnel: Sauvegarder les enregistrements invalides dans une table d'erreurs
                try:
                    spark.sql("""
                        CREATE TABLE IF NOT EXISTS default.produits_errors (
                            corrupt_record STRING,
                            processed_time TIMESTAMP
                        )
                        USING hive
                    """)
                    
                    invalid_df.select("corrupt_record", "processed_time").write \
                        .format("hive") \
                        .mode("append") \
                        .insertInto("default.produits_errors")
                    print(f"✓ {invalid_cnt} enregistrements invalides sauvegardés dans la table d'erreurs")
                except Exception as e:
                    print(f"✗ Erreur lors de la sauvegarde des erreurs2: {str(e)}")
                    
        except Exception as e:
            import traceback
            print(f"Erreur critique lors du traitement du batch produits: {str(e)}")
            print(traceback.format_exc())
    
    # TRAITEMENT DES DONNÉES UTILISATEURS (TOPIC2)
    # ------------------------------------------
    def process_users_batch(batch_df, batch_id):
        try:
            if batch_df.isEmpty():
                print(f"\n--- BATCH {batch_id} UTILISATEURS VIDE ---")
                return
                
            print(f"\n--- DONNÉES BRUTES UTILISATEURS (BATCH {batch_id}) ---")
            batch_df.select("raw_data").show(3, truncate=False)
            
            # Parser les données JSON avec gestion des erreurs
            parsed_df = batch_df.select(
                col("raw_data"),
                from_json(col("raw_data"), user_schema, {"mode": "PERMISSIVE", "columnNameOfCorruptRecord": "corrupt_record"}).alias("data")
            )
            
            # Extraire et valider les champs
            final_df = parsed_df.select(
                col("data.user_id").cast(IntegerType()).alias("user_id"),
                col("data.nom").cast(StringType()).alias("nom"),
                col("data.email").cast(StringType()).alias("email"),
                col("data.date_inscription").cast(TimestampType()).alias("date_inscription"),
                when(col("data.user_id").isNull(), col("raw_data")).alias("corrupt_record"),
                current_timestamp().alias("processed_time")
            )
            
            # Séparer les enregistrements valides et invalides
            valid_df = final_df.filter(col("user_id").isNotNull())
            invalid_df = final_df.filter(col("user_id").isNull())
            
            valid_cnt = valid_df.count()
            invalid_cnt = invalid_df.count()
            total_cnt = valid_cnt + invalid_cnt
            
            print(f"Enregistrements: {valid_cnt} valides, {invalid_cnt} invalides, {total_cnt} total")
            
            # Traiter les enregistrements valides
            if valid_cnt > 0:
                print("Échantillon des données valides:")
                valid_df.select("user_id", "nom", "email", "date_inscription").show(3, truncate=False)
                
                # Sauvegarder dans Hive
                try:
                    # Créer la table si elle n'existe pas
                    spark.sql("""
                        CREATE TABLE IF NOT EXISTS default.users (
                            user_id INT,
                            nom STRING,
                            email STRING,
                            date_inscription TIMESTAMP
                        )
                        USING hive
                        PARTITIONED BY (year INT, month INT, day INT)
                    """)
                    
                    # Ajouter les partitions temporelles
                    partitioned_df = valid_df.withColumn("year", expr("year(processed_time)")) \
                                             .withColumn("month", expr("month(processed_time)")) \
                                             .withColumn("day", expr("dayofmonth(processed_time)"))
                    
                    valid_df.write \
                        .format("hive") \
                        .mode("append") \
                        .partitionBy("year", "month", "day") \
                        .insertInto("default.users")
                    print(f"✓ {valid_cnt} enregistrements sauvegardés dans la table Hive 'users'")
                except Exception as e:
                    print(f"✗ Erreur lors de la sauvegarde dans Hive: {str(e)}")
            
            # Traiter les enregistrements invalides
            if invalid_cnt > 0:
                print(f"⚠️ {invalid_cnt} enregistrements invalides détectés:")
                invalid_df.select("corrupt_record").show(3, truncate=False)
                
                # Optionnel: Sauvegarder les enregistrements invalides dans une table d'erreurs
                try:
                    spark.sql("""
                        CREATE TABLE IF NOT EXISTS default.users_errors (
                            corrupt_record STRING,
                            processed_time TIMESTAMP
                        )
                        USING hive
                    """)
                    
                    invalid_df.select("corrupt_record", "processed_time").write \
                        .format("hive") \
                        .mode("append") \
                        .insertInto("default.users_errors")
                    print(f"✓ {invalid_cnt} enregistrements invalides sauvegardés dans la table d'erreurs")
                except Exception as e:
                    print(f"✗ Erreur lors de la sauvegarde des erreurs: {str(e)}")
                    
        except Exception as e:
            import traceback
            print(f"Erreur critique lors du traitement du batch utilisateurs: {str(e)}")
            print(traceback.format_exc())
    
    # Préparer les données pour le traitement par lot
    produits_with_raw = json_df_produits.withColumn("raw_data", col("value"))
    users_with_raw = json_df_users.withColumn("raw_data", col("value"))
    
    # DÉMARRAGE DES STREAMS
    # ---------------------
    
    # Stream pour traiter les données produits
    produits_stream = produits_with_raw.writeStream \
        .foreachBatch(process_produits_batch) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/checkpoints/produits") \
        .trigger(processingTime="30 seconds") \
        .start()
    
    # Stream pour traiter les données utilisateurs
    users_stream = users_with_raw.writeStream \
        .foreachBatch(process_users_batch) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/checkpoints/users") \
        .trigger(processingTime="30 seconds") \
        .start()
    
    print("=================================================")
    print("Consommateur Kafka Spark démarré avec succès!")
    print("Traitement des données vers Hive en cours...")
    print("Stream 1: topic1 -> table produits")
    print("Stream 2: topic2 -> table users")
    print("=================================================")
    print("Appuyez sur Ctrl+C pour arrêter...")
    
    try:
        # Attendre que les requêtes se terminent
        spark.streams.awaitAnyTermination()
    except KeyboardInterrupt:
        print("\nArrêt des streams...")
        produits_stream.stop()
        users_stream.stop()
        print("Streams arrêtés proprement.")
    finally:
        spark.stop()
        print("Session Spark fermée.")

if __name__ == "__main__":
    main()