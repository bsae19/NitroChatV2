#!/usr/bin/env python3
# Script consommateur Spark qui lit depuis deux topics Kafka et sauvegarde dans des tables Hive
# Version optimisée avec meilleure gestion des formats de données et des erreurs

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, expr, lit
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

def main():
    # Créer une session Spark avec support Hive
    spark = SparkSession.builder \
        .appName("KafkaToHiveConsumer") \
        .enableHiveSupport() \
        .config("hive.metastore.uris", "thrift://hive-metastore:9083") \
        .getOrCreate()
    
    # Réduire le niveau de log pour une meilleure lisibilité
    spark.sparkContext.setLogLevel("WARN")
    
    
    # Schéma des données achat (format direct)
    achat_schema = StructType([
        StructField("achat_id", IntegerType(), True),
        StructField("produit_id", IntegerType(), True),
        StructField("date_achat", StringType(), True),
        StructField("client_id", IntegerType(), True),
        StructField("quantite", IntegerType(), True),
        StructField("montant_total", DoubleType(), True)
    ])
    
    
    df_achats = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "topic2") \
        .option("startingOffsets", "latest") \
        .load()
    
    json_df_achats = df_achats.selectExpr("CAST(value AS STRING)")
    
    # TRAITEMENT DES DONNÉES ACHATS (TOPIC2)
    # --------------------------------------
    def process_achats_batch(batch_df, batch_id):
        try:
            if batch_df.count() == 0:
                print(f"\n--- BATCH {batch_id} ACHATS VIDE ---")
                return
                
            print(f"\n--- DONNÉES BRUTES ACHATS (BATCH {batch_id}) ---")
            batch_df.select("raw_data").show(3, truncate=False)
            
            # Essayer d'abord avec le schéma complet
            parsed_with_direct = batch_df.select(
                from_json(col("raw_data"), achat_schema, {"mode": "PERMISSIVE"}).alias("data")
            )
            parsed_with_direct = batch_df.select(
                    from_json(col("raw_data"), achat_schema, {"mode": "PERMISSIVE"}).alias("data")
                )
            final_df = parsed_with_direct.select("data.*")
            
            # Filtrer les enregistrements valides
            valid_df = final_df.filter(col("achat_id").isNotNull())
            valid_cnt = valid_df.count()
            total_cnt = final_df.count()
            
            print(f"Enregistrements valides: {valid_cnt}/{total_cnt}")
            
            if valid_cnt > 0:
                print("Échantillon des données valides:")
                valid_df.show(3, truncate=False)
                
                # Sauvegarder dans Hive
                try:
                    # Créer la table si elle n'existe pas
                    spark.sql("""
                        CREATE TABLE IF NOT EXISTS default.achats (
                            achat_id INT,
                            produit_id INT,
                            date_achat STRING,
                            client_id INT,
                            quantite INT,
                            montant_total DOUBLE
                        )
                        USING hive
                    """)
                    
                    valid_df.write \
                        .format("hive") \
                        .mode("append") \
                        .insertInto("default.achats")
                    print(f"✓ {valid_cnt} enregistrements sauvegardés dans la table Hive 'achats'")
                except Exception as e:
                    print(f"✗ Erreur lors de la sauvegarde dans Hive: {str(e)}")
            
            # Afficher les enregistrements invalides s'il y en a
            null_cnt = total_cnt - valid_cnt
            if null_cnt > 0:
                null_records = final_df.filter(col("achat_id").isNull())
                print(f"⚠️ {null_cnt} enregistrements avec achat_id NULL détectés:")
                null_records.show(3, truncate=False)
                
        except Exception as e:
            print(f"Erreur lors du traitement du batch achats: {str(e)}")
    
    achats_with_raw = json_df_achats.withColumn("raw_data", col("value"))
    
    # DÉMARRAGE DES STREAMS OPTIMISÉS
    # -------------------------------
    
    # Un seul stream pour traiter les données achats avec détection intelligente du format
    achats_stream = achats_with_raw.writeStream \
        .foreachBatch(process_achats_batch) \
        .outputMode("append") \
        .option("checkpointLocation", "/checkpoints/achats_unified") \
        .start()
    
    print("=================================================")
    print("Consommateur Kafka Spark démarré avec succès!")
    print("Traitement intelligent des données vers Hive en cours...")
    print("Les streams détecteront automatiquement le format des données")
    print("=================================================")
    print("Appuyez sur Ctrl+C pour arrêter...")
    
    try:
        # Attendre que les requêtes se terminent
        spark.streams.awaitAnyTermination()
    except KeyboardInterrupt:
        print("\nArrêt des streams...")
        achats_stream.stop()
        print("Streams arrêtés proprement.")

if __name__ == "__main__":
    main()