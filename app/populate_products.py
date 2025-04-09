import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
TOPIC1 = 'topic1'

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

produits = [
    {"produit_id": 1, "nom": "Smartphone", "categorie": "Electronique", "prix": 599.99},
    {"produit_id": 2, "nom": "Laptop", "categorie": "Electronique", "prix": 1299.99},
    {"produit_id": 3, "nom": "Casque audio", "categorie": "Accessoires", "prix": 149.99},
    {"produit_id": 4, "nom": "Livre", "categorie": "Culture", "prix": 19.99},
    {"produit_id": 5, "nom": "Chaussures de sport", "categorie": "Mode", "prix": 89.99}
]


def envoyer_vers_topic(topic, donnees):
    future = producer.send(topic, donnees)
    record_metadata = future.get(timeout=10)
    print("Message envoye a " + topic + ": Partition=" + str(record_metadata.partition) + ", Offset=" + str(record_metadata.offset))
    print("Donnees: "+json.dumps(donnees, indent=2))

def main():
    try:
        for i in produits:
            envoyer_vers_topic(TOPIC1, i)
    except KeyboardInterrupt:
        print("Interruption detectee, arret du producteur...")
    finally:
        producer.close()
        print("Producteur ferme.")

if __name__ == "__main__":
    main()