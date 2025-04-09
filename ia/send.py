import json
from kafka import KafkaProducer

# Kafka configuration
KAFKA_TOPIC = 'message'
KAFKA_SERVER = 'kafka:9092'

# Read the content of structure.json
with open('structure.json', 'r') as file:
    data = json.load(file)

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send data to Kafka topic
producer.send(KAFKA_TOPIC, data)
producer.flush()

print(f"Data from structure.json has been sent to Kafka topic {KAFKA_TOPIC}")