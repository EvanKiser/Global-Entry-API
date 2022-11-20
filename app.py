from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json
import os
from mutable import MutableList
from twilio.rest import Client

load_dotenv()

ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_welcome_message(phone_number):
    WELCOME_MSG = f"""
        This is Global Entry Scanner. Thanks for signing up! You will now recieve texts about new Global Entry interviews. Simply text "STOP" at any time to unsubscribe.
        """
    return client.messages \
        .create(
            body=WELCOME_MSG,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )

def send_exit_message(phone_number):
    EXIT_MSG = f"""
        You have successfully been unsubscribed!
        """
    return client.messages \
        .create(
            body=EXIT_MSG,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )

def map_location_names_to_ids(location_name):
    with open('locations.json') as locations_path:
        locations = json.load(locations_path)
    for location in locations:
        if location["display_name"] == location_name:
            return location["id"]

app = Flask(__name__)

ENV = os.getenv("ENV")
DB_URI = os.getenv("DB_URI") if ENV != 'dev' else 'postgresql://postgres:aaaa@localhost/ge'

if ENV == 'dev':
    app.debug = True
else:
    app.debug = False

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route("/healthz")
def healthz():
    resp = jsonify("Healthz")
    resp.status_code = 200
    return resp

@app.route("/")
def home():
    resp = jsonify("Home")
    resp.status_code = 200
    return resp

##### LOCATION OPERATIONS #####

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250))
    code = db.Column(db.Integer)
    city = db.Column(db.String(50))
    state = db.Column(db.String(15))
    past_appointments = db.Column(MutableList.as_mutable(db.ARRAY(db.DateTime)))

    def __init__(self, id, name, code, city, state, past_appointments):
        self.id = id
        self.name = name
        self.code = code
        self.city = city
        self.state = state
        self.past_appointments = past_appointments

@app.route('/location', methods = ['POST'])
def add_all_locations():
    with open('locations.json') as locations_path:
        locations = json.load(locations_path)
    if request.method == 'POST':
        for location in locations:
            id = location["id"]
            name = location["name"]
            code = location["locationCode"]
            city = location["city"]
            state = location["state"]
            past_appointments = []
            data = Location(id, name, code, city, state, past_appointments)
            db.session.add(data)
            db.session.commit() 
    resp = jsonify("sweet locations")
    resp.status_code = 200
    return resp

@app.route('/location', methods = ['GET'])
def get_locations():
    if request.method == 'GET':
        locations = Location.query.all()
        locations = [
            {   
                "id": location.id,
                "name": location.name,
                "code": location.code,
                'city': location.city, 
                'state': location.state,
                'past_appointments': location.past_appointments,
            }
            for location in locations
        ]
    resp = jsonify(locations)
    resp.status_code = 200
    return resp

@app.route('/location/<id>', methods = ['GET'])
def get_location_by_id(id):
    if request.method == 'GET':
        location = Location.query.get(id)
        location = {   
                "id": location.id,
                "name": location.name,
                "code": location.code,
                'city': location.city, 
                'state': location.state,
                'past_appointments': location.past_appointments,
            }
    resp = jsonify(location)
    resp.status_code = 200
    return resp

@app.route('/location/<id>', methods = ['PUT'])
def update_location(id):
    new_appointment = request.json['new_appointment']
    if request.method == 'PUT':
        location = Location.query.get(id)
        location.past_appointments.append(new_appointment)
        db.session.commit()
    resp = jsonify(f"location appts updated")
    resp.status_Code = 200
    return resp

##### USER OPERATIONS #####
 
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(15))
    locations = db.Column(MutableList.as_mutable(db.ARRAY(db.Integer)))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    texts_sent = db.Column(MutableList.as_mutable(db.ARRAY(db.String(200))))

    def __init__(self, email, phone, locations, texts_sent=[]):
        self.email = email
        self.phone = phone
        self.locations = locations
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=30)
        self.texts_sent = texts_sent

@app.route('/user', methods = ['POST'])
def add_user():
    print(request.json)
    data = request.json['data']
    if request.method == 'POST':
        # first_name = data['field:comp-la6ibvk5']
        email = data['field:comp-la6fcw1i']
        phone = data['field:comp-la6fcw2e2']
        location0 = data['field:comp-la6fcw4h']
        locations = [map_location_names_to_ids(location0)]
        if 'field:comp-la6gjwjv' in data and data['field:comp-la6gjwjv'] != 'None':
            location1 = data['field:comp-la6gjwjv']
            locations.append(map_location_names_to_ids(location1))
        if 'field:comp-la6gk26t' in data and data['field:comp-la6gk26t'] != 'None':
            location2 = data['field:comp-la6gk26t']
            locations.append(map_location_names_to_ids(location2))
        data = User(email, phone, locations)
        db.session.add(data)
        db.session.commit()
        send_welcome_message(phone)
    resp = jsonify("cool email")
    resp.status_code = 200
    return resp

@app.route('/user', methods = ['GET'])
def get_current_users():
    if request.method == 'GET':
        users = User.query.filter(User.end_date > datetime.now())
        user_json = [
            {
                'id': user.id,
                'email': user.email, 
                'phone': user.phone,
                'start_date': user.start_date,
                'end_date': user.end_date,
                'locations': user.locations,
                'texts_sent': user.texts_sent

            } 
            for user in users
        ]
    resp = jsonify(user_json)
    resp.status_code = 200
    return resp

@app.route('/user/all', methods = ['GET'])
def get_all_users():
    if request.method == 'GET':
        users = User.query.all()
        user_json = [
            {
                'id': user.id,
                'email': user.email, 
                'phone': user.phone,
                'start_date': user.start_date,
                'end_date': user.end_date,
                'locations': user.locations,
                'texts_sent': user.texts_sent
            } 
            for user in users
        ]
    resp = jsonify(user_json)
    resp.status_code = 200
    return resp

@app.route('/user/<id>', methods = ['PUT'])
def update_user(id):
    new_text = request.json['text_sent']
    if request.method == 'PUT':
        user = User.query.get(id)
        user.texts_sent.append(new_text)
        db.session.commit()
    resp = jsonify(f"texts sent updated")
    resp.status_Code = 200
    return resp

@app.route('/user/<id>', methods = ['DELETE'])
def delete_user(id):
    if request.method == 'DELETE':
        user = User.query.get(id)
        db.session.delete(user)
        db.session.commit()
    resp = jsonify(f"user id: '{id}' deleted")
    resp.status_Code = 200
    return resp

##### STOP TEXTS #####
@app.route('/stop', methods = ['POST']) 
def stop_texts():
    print(request.body)
    data = request.json['data']
    if request.method == 'POST':
        phone_number = data["phone_number"]
        user = User.query.filter_by(phone=phone_number).first()
        user.end_date = datetime.now()
        db.session.commit()
        send_exit_message(phone_number)
    resp = jsonify(f"user id: {user.id} no longer receving texts")
    resp.status_Code = 200
    return resp
        
if __name__ == '__main__':
    with app.app_context():
        # db.create_all()
        # db.session.commit()
        app.run()