from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json
import os
from mutable import MutableList
from twilio.rest import Client
import stripe

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET')

ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
PAID = os.getenv('PAID')
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_text(message_content, phone_number):
    return client.messages \
        .create(
            body=message_content,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )

def create_checkout_session(user_id):
    try:
        checkout_session = stripe.checkout.Session.create(
            client_reference_id={user_id},
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    # 'price': 'price_1MQ5VWIcbfJQY4bat1kPw3P0', #PROD $5
                    # 'price': 'price_1MRUqaIcbfJQY4baaOsS1rWx', #TEST
                    'price': 'price_1MBsRUIcbfJQY4baGWEtwBCg', # PROD What you want
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url='https://www.globalentryscan.com',
            automatic_tax={'enabled': False},
        )
    except Exception as e:
        return str(e)

    return checkout_session.url

def send_checkout_link(user_id, phone_number):
    checkout_url = create_checkout_session(user_id)
    CHECKOUT_MSG = f"""
        That is the end of your 3 free messages. Pay what you feel is fair ($5 minimum) to continue receiving appointment notifications. {checkout_url}
        """
    send_text("Sorry we have to do this but...", phone_number)
    return send_text(CHECKOUT_MSG, phone_number)

def send_welcome_message(phone_number, city, state):
    WELCOME_MSG = f"""
        While I wanted to keep this app free forever (fighting the good fight against our price gouging competitors), the reality is that maintaining software is quite expensive and yall were burning a hole in my pockets.
\nTo that end, after receiving 3 texts regarding new appointments in {city}, {state}, you will receive a checkout link. We ask that you pay an amount that you feel is fair (even as little as $5). to conitnue receiving 
appointment notifications. Thank you for your understanding!
        """
    send_text(WELCOME_MSG, phone_number)
    PS_MSG = f"""P.S. These appointments go fast, so if you see one you like, sign up on the website ASAP! Then text "STOP" to unsubscribe from these messages."""
    send_text(PS_MSG, phone_number)

def send_paid_message_to_user(phone_number, city, state):
    PAID_MSG = f"""
        Congrats! You will now recieve texts about new Global Entry interviews in {city}, {state} for the next 7 days! \nSimply text "STOP" at any time to unsubscribe.
        """
    return send_text(PAID_MSG, phone_number)

def send_paid_message_to_me(id, phone, amount_cents, city, state):
    PAID_MSG_TO_ME = f"""
        User paid. \n{id}, \n{phone}, \n{amount_cents} \n{city}, \n{state}.
        """
    return send_text(PAID_MSG_TO_ME, "+15016504390")

def send_reminder_to_user(user_id, phone_number, city, state):
    checkout_url = create_checkout_session(user_id)
    REMINDER_MSG = f"""
        Just a reminder that if you would like to continue receiving texts about new Global Entry interviews in {city}, {state}, you can pay what you feel is fair here: {checkout_url} 
        """
    return send_text(REMINDER_MSG, phone_number)

def map_id_to_location(location_id):
    with open('locations.json') as locations_path:
        locations = json.load(locations_path)
    for location in locations:
        if location["id"] == int(location_id):
            return location["city"], location["state"]

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
    texts_sent_today = db.Column(db.Integer)

    def __init__(self, email, phone, locations, texts_sent=[]):
        self.email = email
        self.phone = phone
        self.locations = locations
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=7)
        self.texts_sent = texts_sent
        self.texts_sent_today = 1

@app.route('/user', methods = ['POST'])
def add_user():
    if request.form:
        data = request.form
        if request.method == 'POST':
            email = data['email']
            phone = data['phone']
            if phone == '6104728779':
                resp = jsonify("Fuck the competition")
                resp.status_code = 400
                return resp
            location = data['location']
            locations = [int(location)]
            curr_users = User.query.filter(User.end_date > datetime.now())
            for user in curr_users:
                if user.phone == phone:
                    resp = jsonify("Currently we have another user with this phone number. Please use a different phone number.")
                    resp.status_code = 400
                    return resp
            try:
                city, state = map_id_to_location(location)
                send_welcome_message(phone, city, state)
            except:
                resp = jsonify("phone number seems incorrect")
                resp.status_code = 400
                return resp
        data = User(email, phone, locations)
        db.session.add(data)
        db.session.commit()
        resp = jsonify("user created successfully")
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
                'texts_sent': user.texts_sent,
                'texts_sent_today': user.texts_sent_today
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
                'texts_sent': user.texts_sent,
                'texts_sent_today': user.texts_sent_today
            } 
            for user in users
        ]
    resp = jsonify(user_json)
    resp.status_code = 200
    return resp

@app.route('/user/count', methods = ['GET'])
def count_users():
    if request.method == 'GET':
        users = User.query.all()
    resp = jsonify(len(users))
    resp.status_code = 200
    return resp


@app.route('/user/<id>', methods = ['PUT'])
def update_user(id):
    new_text = request.json['text_sent']
    if request.method == 'PUT':
        user = User.query.get(id)
        user.texts_sent.append(new_text)
        user.texts_sent_today += 1
        if PAID == 'True' and len(user.texts_sent) == 3:
            send_checkout_link(user.id, user.phone)
        db.session.commit()
    resp = jsonify(f"texts sent updated")
    resp.status_Code = 200
    return resp

@app.route('/user/reset', methods = ['PUT'])
def reset_texts_per_day():
    if request.method == 'PUT':
        users = User.query.filter(User.end_date > datetime.now())
        for user in users:
            user.texts_sent_today = 0
        db.session.commit()
    resp = jsonify(f"number of texts sent updated")
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

@app.route('/unsub/<id>', methods = ['POST']) 
def unsub_users(id):
    user = User.query.get(id)
    print("\n\n\nuser.id, user.end_date")
    user.end_date = datetime.now()
    db.session.commit()
    print("user.id, user.end_date\n\n")
    resp = jsonify(f"user id: {user.id} unsubscribed")
    resp.status_Code = 200
    return resp

@app.route('/stop', methods = ['POST']) 
def stop_texts():
    data = request.values
    if request.method == 'POST':
        phone = data.get('From', None)
        body = data.get('Body', None).upper()
        if body not in ["STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]:
            resp = jsonify(f"Not a correct text body.")
            resp.status_Code = 400
            return resp
        phone_number = '(' + phone[:2] + ') ' + phone[2:]
        users = User.query.filter(User.end_date > datetime.now())
        user = None
        found_users = []
        for u in users:
            if u.phone == phone_number:
                found_users.append(u)
        if found_users == []:
            phone_number = phone[2:]
            for u in users:
                if u.phone == phone_number:
                    found_users.append(u)
        for user in found_users:
            user.end_date = datetime.now()
        db.session.commit()
    resp = jsonify(f"user id: {user.id} no longer receving texts")
    resp.status_Code = 200
    return resp

##### PAID OPERATIONS #####
 
class Paid(db.Model):
    __tablename__ = 'paid'
    user_id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer)
    amount_cents = db.Column(db.String(200))
    paid_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

    def __init__(self, user_id, amount_cents, location_id):
        self.user_id = user_id
        self.amount_cents = amount_cents
        self.location_id = location_id
        self.paid_date = datetime.now()
        self.end_date = self.paid_date + timedelta(days=7)

@app.route('/paid', methods = ['GET'])
def get_current_paid():
    if request.method == 'GET':
        current_paid = Paid.query.filter(Paid.end_date > datetime.now())
        paid_user_json = [
            {   
                "user_id": user.user_id,
                "location": user.location_id,
                "amount_cents": user.amount_cents,
                "paid_date": user.paid_date,
                'end_date': user.end_date, 
            }
            for user in current_paid
        ]
    resp = jsonify(paid_user_json)
    resp.status_code = 200
    return resp

@app.route('/paid/all', methods = ['GET'])
def all_paid():
    if request.method == 'GET':
        all_paid = Paid.query.all()
        paid_users_json = [
            {   
                "user_id": user.user_id,
                "location": user.location_id,
                "amount_cents": user.amount_cents,
                "paid_date": user.paid_date,
                'end_date': user.end_date, 
            }
            for user in all_paid
        ]
    resp = jsonify(paid_users_json)
    resp.status_code = 200
    return resp

@app.route('/paid', methods = ['POST']) 
def paid():
    payload = request.data
    resp = jsonify(f"")
    try:
        event = json.loads(payload) 
    except ValueError as e:
        # Invalid payload
        resp.status_Code = 400
        return resp
    except Exception as e:
        print(e)
        resp.status_Code = 400
        return resp
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['client_reference_id'][1:-1]
        amount_cents = session['amount_total']
        if (amount_cents < 500):
            resp = jsonify(f"Need more moolah beotch")
            resp.status_Code = 400
            return resp
        user = User.query.get(user_id)
        user.start_date = datetime.now()
        user.end_date = datetime.now() + timedelta(days=7)
        location_id = user.locations[0]
        paid = Paid(user_id, amount_cents, location_id)
        db.session.add(paid)
        db.session.commit()
        resp = jsonify(f"Successfully paid")
        resp.status_Code = 200
        city, state = map_id_to_location(location_id)
        send_paid_message_to_user(user.phone, city, state)
        send_paid_message_to_me(user.id, user.phone, amount_cents, city, state)
    if event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        user_id = session['client_reference_id'][1:-1]
        user = User.query.get(user_id)
        if user and user.end_date > datetime.now():
            print(user.phone)
            location_id = user.locations[0]
            city, state = map_id_to_location(location_id)
            send_reminder_to_user(user.id, user.phone, city, state)
            return resp

    resp = jsonify(f"Something went wrong")
    resp.status_Code = 400
    return resp

@app.route('/paid_test', methods = ['POST'])
def add_paid_user():
    if request.method == 'POST':
        user_id = request.json['user_id']
        amount_cents = request.json['amount_cents']
        user = User.query.get(user_id)
        user.start_date = datetime.now()
        user.end_date = datetime.now() + timedelta(days=7)
        location_id = user.locations[0]
        paid = Paid(user_id, amount_cents, int(location_id))
        db.session.add(paid)
        db.session.add(user)
        db.session.commit()
        resp = jsonify("user added to paid table successfully")
        resp.status_code = 200
        return resp

@app.route('/paid/<id>', methods = ['DELETE'])
def delete_paid_user(id):
    if request.method == 'DELETE':
        user = Paid.query.get(id)
        db.session.delete(user)
        db.session.commit()
        resp = jsonify("user deleted successfully")
        resp.status_code = 200
        return resp

@app.route('/paid/count', methods = ['GET'])
def count_paid_users():
    if request.method == 'GET':
        users = Paid.query.all()
    resp = jsonify(len(users))
    resp.status_code = 200
    return resp
        
if __name__ == '__main__':
    with app.app_context():
        # db.create_all()
        # db.session.commit()
        app.run()
