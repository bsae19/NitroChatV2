from flask import Flask, request, jsonify
from transformers import TFAutoModelForSequenceClassification, CamembertTokenizer, TrainingArguments, Trainer
import tensorflow as tf
from kafka import KafkaProducer
import json
from pyhive import hive
import os


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
    producer.send("ia_message", json.dumps(data))
    producer.flush()

@flask.route('/train', methods=['POST'])
def retrain_model():
    flask.logger.info("Starting training pipeline")

    try:
        conn = hive.Connection(host='hive-server', port='10000', database='default', auth='NONE')
        cursor = conn.cursor()

        cursor.execute("SELECT id_message FROM message_metadata WHERE valide = 'true'")
        ids = [row[0] for row in cursor.fetchall()]

        if not ids:
            return jsonify({"status": "No valid messages found for training"})

        ids_str = ",".join([f"'{id}'" for id in ids])
        cursor.execute(f"SELECT message FROM messages WHERE id IN ({ids_str})")
        texts = [row[0] for row in cursor.fetchall()]
        labels = [1] * len(texts)  # Only "approprié" for now

        from datasets import Dataset
        train_dataset = Dataset.from_dict({"text": texts, "label": labels})

        def tokenize(batch):
            return tokenizer(batch["text"], padding=True, truncation=True, max_length=512)

        train_dataset = train_dataset.map(tokenize, batched=True)

        training_args = TrainingArguments(
            output_dir="/app/saved_model",
            num_train_epochs=1,
            per_device_train_batch_size=8,
            save_steps=10,
            save_total_limit=1,
            logging_dir="/app/logs",
            logging_steps=10,
            remove_unused_columns=False
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset
        )

        trainer.train()
        trainer.save_model("/app/saved_model")
        return jsonify({"status": "Model retrained and saved successfully"})

    except Exception as e:
        flask.logger.error(f"Training failed: {str(e)}")
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    flask.run(host='0.0.0.0', port=5052, debug=True)