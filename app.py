from tokenize import String
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)

ENV = 'dev'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:aaaa@localhost/ge'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''

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
    active = db.Column(db.Boolean)

    def __init__(self, email, phone, locations):
        self.email = email
        self.phone = phone
        self.locations = locations
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=28)
        self.active = True

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

@app.route("/locations", methods=["PUT"])
def update_locations():
    return

if __name__ == '__main__':
    with app.app_context():
        # db.create_all()
        app.run()