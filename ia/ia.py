from flask import Flask, request, jsonify
from transformers import TFAutoModelForSequenceClassification, CamembertTokenizer
import tensorflow as tf
from kafka import KafkaProducer
import json


# Load the saved model and tokenizer
model_path = "../saved_model"
model = TFAutoModelForSequenceClassification.from_pretrained(model_path)
tokenizer = CamembertTokenizer.from_pretrained(model_path, use_fast=False)
producer = KafkaProducer(bootstrap_servers='kafka:9092',
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

print("Model and tokenizer loaded successfully")

flask = Flask(__name__)

@flask.route('/ia', methods=['POST'])
def send_data():
    flask.logger.info("get data")
    data = request.get_json()
    flask.logger.info(data)
    flask.logger.info(data['message'])
    exec_ia(data)
    return jsonify(data)

def exec_ia(data):
    # Tokenize the input
    flask.logger.info("model start")
    inputs = tokenizer(data["message"], return_tensors="tf", padding=True, truncation=True, max_length=512)
    logits = model(**inputs).logits
    predicted_class = tf.argmax(logits, axis=-1).numpy()[0]
    labels = ["inapproprié", "approprié"]
    predicted_label = labels[predicted_class]

    flask.logger.info(f"Predicted class: {predicted_class}")
    flask.logger.info(f"Probabilities: {predicted_label}")
    data["type"] = predicted_label
    producer.send("message_ia", json.dumps(data))
    producer.flush()

if __name__ == '__main__':
    flask.run(host='0.0.0.0', port=5052, debug=True)