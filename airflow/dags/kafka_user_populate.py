from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from confluent_kafka import Producer
import random
import json


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Kafka config
KAFKA_CONFIG = {
    'bootstrap.servers': 'kafka:9092',
}
KAFKA_TOPIC = 'register'

def send_random_users_to_kafka():
    producer = Producer(KAFKA_CONFIG)

    def delivery_report(err, msg):
        if err is not None:
            print("Message delivery failed: %s" % err)
        else:
            print("Message delivered to %s [%s]" % (msg.topic(), msg.partition()))

    prenoms = ["Alice", "Bob", "Charlie", "Diana", "Ethan"]
    domaines = ["gmail.com", "yahoo.com", "outlook.com"]

    for i in range(5):
        nom = prenoms[i % len(prenoms)]
        email = "%s%d@%s" % (nom.lower(), random.randint(1, 999), random.choice(domaines))
        user = {
            "nom": nom,
            "email": email,
            "password": "pass%d" % random.randint(1000, 9999),
            "date_inscription": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        message = json.dumps(user)
        print("Sending user: %s" % message)
        producer.produce(KAFKA_TOPIC, value=message, callback=delivery_report)

    producer.flush()


with DAG(
    'kafka_user_pipeline',
    default_args=default_args,
    description='Send random users to Kafka save_user',
    schedule_interval=None,
    catchup=False,
) as dag:

    send_users = PythonOperator(
        task_id='send_random_users_to_kafka',
        python_callable=send_random_users_to_kafka
    )