from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json
import os
from mutable import MutableList

load_dotenv()

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
    city = db.Column(db.String(50))
    state = db.Column(db.String(15))
    past_appts_24_hours = db.Column(MutableList.as_mutable(db.ARRAY(db.DateTime)))

    def __init__(self, id, name, city, state, past_appts_24_hours):
        self.id = id
        self.name = name
        self.city = city
        self.state = state
        self.past_appts_24_hours = past_appts_24_hours

@app.route('/location', methods = ['POST'])
def add_all_locations():
    with open('locations.json') as locations_path:
        locations = json.load(locations_path)
    if request.method == 'POST':
        for location in locations:
            id = location["locationCode"]
            name = location["name"]
            city = location["city"]
            state = location["state"]
            past_appts_24_hours = []
            data = Location(id, name, city, state, past_appts_24_hours)
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
                'city': location.city, 
                'state': location.state,
                'past_appts_24_hours': location.past_appts_24_hours,
            }
            for location in locations
        ]
    resp = jsonify(locations)
    resp.status_code = 200
    return resp

@app.route('/location/<id>', methods = ['PUT'])
def update_location(id):
    if request.method == 'PUT':
        location = Location.query.get(id)
        location.past_appts_24_hours.append(datetime.now())
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

    def __init__(self, email, phone, locations):
        self.email = email
        self.phone = phone
        self.locations = locations
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=28)

@app.route('/user', methods = ['POST'])
def add_user():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        location0 = request.form['location0']
        location1 = request.form['location1']
        location2 = request.form['location2']
        locations = [location0]
        if location1 != '':
            locations.append(location1)
        if location2 != '':
            locations.append(location2)
        data = User(email, phone, locations)
        db.session.add(data)
        db.session.commit() 
    resp = jsonify("cool email")
    resp.status_code = 200
    return resp

@app.route('/user', methods = ['GET'])
def get_users():
    if request.method == 'GET':
        users = User.query.all()
        user_json = [
            {
                'id': user.id,
                'email': user.email, 
                'phone': user.phone, 
                'locations': user.locations
            } 
            for user in users
        ]
    resp = jsonify(user_json)
    resp.status_code = 200
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

if __name__ == '__main__':
    with app.app_context():
        # db.create_all()
        app.run()