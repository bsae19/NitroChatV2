from flask import Flask, jsonify, request
from flask_cors import CORS
from kafka import KafkaConsumer, KafkaProducer
import json
from datetime import datetime
import random

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5000"}})
KAFKA_SERVER = 'kafka:9092'
MESSAGES_TOPIC = 'message'
MESSAGES_IA_TOPIC = 'message_ia'
MESSAGES_GET_TOPIC = 'get_messages'
MESSAGES_POST_TOPIC = 'post_messages'

messages_cache = {}
# contacts_cache = []

producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    
@app.route('/api/messages', methods=['POST'])
def send_message():
    app.logger.info("get data")
    data = request.json
    try:
        message = {
            'id': str(random.randint(0, 100000000000)),
            'user_id': data['user_id'],
            'message': data['message'],
            'type': '',
            'chat_id': '0',
            'Created_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        app.logger.info(message)
        messages_consumer = KafkaConsumer(
            MESSAGES_IA_TOPIC,
            bootstrap_servers=KAFKA_SERVER,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest'
        )
        app.logger.info(MESSAGES_TOPIC)

        # Envoie le message à Kafka
        producer.send(MESSAGES_TOPIC, message)
        producer.flush()
        response=None
        try:
            for msg in messages_consumer:
                response = json.loads(msg.value)
                app.logger.info(response)
                if response["id"] == message["id"]:
                    messages_consumer.close() 
        finally:
            messages_consumer.close()
        if response:
            # Mise à jour du cache local
            if message['chat_id'] not in messages_cache:
                messages_cache[message['chat_id']] = []
            messages_cache[message['chat_id']].append(message)

            return jsonify({'status': 'success', 'message': response}), 201

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/messages/<string:chat_id>')
def get_messages(chat_id):
    app.logger.info("get all data")
    messages_consumer = KafkaConsumer(
            MESSAGES_GET_TOPIC,
            bootstrap_servers=KAFKA_SERVER,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest'
        )

    
    producer.send(MESSAGES_POST_TOPIC, {"chat_id": chat_id,"user_id":""})
    producer.flush()
    response=None
    try:
        for msg in messages_consumer:
            response = msg.value
            app.logger.info(response)
            if response["chat_id"] == chat_id:
                messages_consumer.close()
                
                return jsonify(response), 200
    finally:
        messages_consumer.close()
    if response:
        # Mise à jour du cache local
        if response['chat_id'] not in messages_cache:
            messages_cache[response['chat_id']] = []
        messages_cache[response['chat_id']]= messages_cache[response['chat_id']] + response["message"]
        messages = messages_cache[chat_id]
        return jsonify(messages)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)