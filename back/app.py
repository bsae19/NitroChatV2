from flask import Flask, request, jsonify
from flask_cors import CORS
from kafka import KafkaProducer
import json
import random
from datetime import datetime
import asyncio
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5000"}})
app.config['JWT_SECRET_KEY'] = 'super-secret'
jwt = JWTManager(app)
KAFKA_SERVER = 'kafka:9092'
SEND_ALL_MESSAGES_TOPIC = 'send_all_messages'
CHECK_MESSAGE_TOPIC = 'check_message'
SEND_MESSAGE_TOPIC = 'send_message'
REGISTER_TOPIC = 'register'
SEND_USERS_TOPIC = 'send_users'
GET_ALL_MESSAGES_TOPIC = 'get_all_messages'
GET_USERS_TOPIC = 'get_users'
IA_MESSAGE_TOPIC = 'ia_message'
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
users = {}


# Mes 5 topics KAFKA

@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    email = d.get('email', '')
    password = d.get('password', '')
    nom = d.get('nom', '')
    date_inscription = d.get('date_inscription', '')
    if email in users:
        return jsonify({'msg': 'User already exists'}), 400
    users[email] = password
    producer.send(REGISTER_TOPIC, d)
    producer.flush()
    return jsonify({'msg': 'User registered successfully'}), 200

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    email = d.get('email', '')
    password = d.get('password', '')
    if email not in users or users[email] != password:
        return jsonify({'msg': 'Bad email or password'}), 401
    access_token = create_access_token(identity=email)
    return jsonify({'access_token': access_token}), 200

@app.route('/api/send_all_messages', methods=['POST'])
@jwt_required()
def send_all_messages():
    d = request.json
    producer.send(SEND_ALL_MESSAGES_TOPIC, d)
    producer.flush()
    return jsonify({'status': 'ok'}), 200

@app.route('/api/check_message', methods=['POST'])
@jwt_required()
def check_message():
    d = request.json
    producer.send(CHECK_MESSAGE_TOPIC, d)
    producer.flush()
    return jsonify({'status': 'ok'}), 200

@app.route('/api/send_message', methods=['POST'])
@jwt_required()
def send_message():
    d = request.json
    r = {
        'id': str(random.randint(0, 999999999999)),
        'user_id': d.get('user_id', ''),
        'message': d.get('message', ''),
        'type': '',
        'chat_id': '0',
        'Created_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    producer.send(SEND_MESSAGE_TOPIC, r)
    producer.flush()
    return jsonify({'status': 'ok', 'payload': r}), 200

@app.route('/api/send_users', methods=['POST'])
@jwt_required()
def send_users():
    d = request.json
    producer.send(SEND_USERS_TOPIC, d)
    producer.flush()
    return jsonify({'status': 'ok'}), 200



 # Ecoute HTTP DE NIFI   

@app.route('/api/get_all_messages', methods=['POST'])
@jwt_required()
async def get_all_messages():
    d = request.json
    await asyncio.sleep(0)
    return jsonify({'status': 'ok', 'data': d}), 200

@app.route('/api/get_users', methods=['POST'])
@jwt_required()
async def get_users():
    d = request.json
    await asyncio.sleep(0)
    return jsonify({'status': 'ok', 'data': d}), 200

@app.route('/api/ia_message', methods=['POST'])
@jwt_required()
async def ia_message():
    d = request.json
    await asyncio.sleep(0)
    return jsonify({'status': 'ok', 'data': d}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
