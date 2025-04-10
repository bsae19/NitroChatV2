from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from confluent_kafka import Producer
import uuid
import random
import json

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

KAFKA_CONFIG = {
    'bootstrap.servers': 'kafka:9092',
}
TOPIC_MESSAGES = 'ia_message'
TOPIC_METADATA = 'check_message'

def send_messages_and_metadata():
    producer = Producer(KAFKA_CONFIG)

    def delivery_report(err, msg):
        if err is not None:
            print("Message delivery failed: %s" % err)
        else:
            print("Message delivered to %s [%s]" % (msg.topic(), msg.partition()))

    user_ids = [str(uuid.uuid4()) for _ in range(5)]
    types = ['text', 'image', 'voice']
    chat_ids = [str(uuid.uuid4()) for _ in range(3)]

    for i in range(5):
        message_id = str(uuid.uuid4())

        msg_data = {
            "message": f"Contenu message {i}",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": random.choice(user_ids),
            "chat_id": random.choice(chat_ids),
            "type": random.choice(types)
        }

        metadata = {
            "id_message": message_id,
            "valide": random.choice(["true", "false"]),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        print(f"Sending message: {msg_data}")
        # print(f"Sending metadata: {metadata}")

        producer.produce(TOPIC_MESSAGES, value=json.dumps({**msg_data, "id": message_id}), callback=delivery_report)
        # producer.produce(TOPIC_METADATA, value=json.dumps(metadata), callback=delivery_report)

    producer.flush()

with DAG(
    'kafka_messages_pipeline',
    default_args=default_args,
    description='Send random messages and metadata to Kafka',
    schedule_interval=None,
    catchup=False,
) as dag:

    send_kafka_data = PythonOperator(
        task_id='send_messages_and_metadata',
        python_callable=send_messages_and_metadata
    )
