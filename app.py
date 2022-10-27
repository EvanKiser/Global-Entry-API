from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

ENV = os.getenv("ENV")
DB_URI = os.getenv("DB_URI")

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:aaaa@localhost/ge'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(15))
    locations = db.Column(db.ARRAY(db.Integer))
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
    for user in users:
        print(user.email)
    user_json = [
        {user.id: {
            'email': user.email, 
            'phone': user.phone, 
            'locations': user.locations
            }
        } 
        for user in users
    ]
    resp = jsonify(user_json)
    resp.status_code = 200
    return resp
    

@app.route('/user', methods = ['PUT'])
def unsubscribe_user():
    if request.method == 'PUT':
        phone = request.body["phone"]
        end_date = datetime.now()
        db.session.query(User).filter(User.phone==phone)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # app.run()