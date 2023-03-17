from appointments import check_for_appointments
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()

PAID = os.getenv("PAID")

API_URL = os.getenv("API_URL") if os.getenv("ENV") != 'dev' else 'http://127.0.0.1:5000'
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
MAX_TEXTS_PER_DAY = int(os.getenv('MAX_TEXTS_PER_DAY'))
client = Client(ACCOUNT_SID, AUTH_TOKEN)

class User():
    def __init__(self, id, end_date, phone_number, texts_sent, texts_sent_today):
        self.id = id
        self.end_date = end_date
        self.phone_number = phone_number
        self.texts_sent = texts_sent
        self.texts_sent_today = texts_sent_today

def users_dict_to_locations_dict(users_dict):
    locations_dict = {}
    for user in users_dict:
        user_obj = User(user["id"], user["end_date"], user["phone"], user["texts_sent"], user["texts_sent_today"])
        for location in user["locations"]:
            if location in locations_dict:
                locations_dict[location].add(user_obj)
            else:
                locations_dict[location] = {user_obj}
    return locations_dict

def add_sent_texts_to_db(user_id, message_content):
    requests.put(f"{API_URL}/user/{user_id}", json={'id': user_id,'text_sent': message_content})

def send_text_message(user_id, phone_number, message_content):
    try:
        _ = client.messages \
            .create(
                body=message_content,
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
        add_sent_texts_to_db(user_id, message_content)
    except TwilioRestException:
        requests.put(f"{API_URL}/unsub/{user_id}", json={})
    return

def get_paid_users_ids():
    response = requests.get(f"{API_URL}/paid")
    paid_users_dict = response.json()
    return [paid_user["user_id"] for paid_user in paid_users_dict]

def reset_texts_sent_per_day():
    requests.put(f"{API_URL}/user/reset")

if __name__ == '__main__':
    # Instead of setting up a seperate cron job just run it here.
    current_day = datetime.now().day
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    if current_hour == 0 and current_minute < 5:
        reset_texts_sent_per_day()

    response = requests.get(f"{API_URL}/user")
    users_dict = response.json()

    paid_users_ids = get_paid_users_ids()

    locations_dict = users_dict_to_locations_dict(users_dict)
    for location_id, users in locations_dict.items():
        new_appointments = check_for_appointments(location_id)
        if new_appointments != []:
            location = new_appointments[0].location
            for appointment in new_appointments:
                message_content = f"New Global Entry Appointment Available in {location.city}, {location.state} on {appointment.timestamp}"
                for user in users:
                    # Only send a text if the user hasn't sent MAX_TEXTS_PER_DAY texts today and if the user hasn't already been sent this text.
                    if (user.texts_sent_today < MAX_TEXTS_PER_DAY) and (message_content not in user.texts_sent):
                        # If the user is a paid user or we are on free mode, send the text.
                        if len(user.texts_sent) < 5 or (PAID == 'True' and user.id in paid_users_ids) or PAID != 'True':
                            print(user.id, user.end_date)
                            if user.end_date > datetime.now():
                                send_text_message(user.id, user.phone_number, message_content)
                                user.texts_sent_today += 1
