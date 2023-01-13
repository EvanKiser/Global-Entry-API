from appointments import check_for_appointments
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
from twilio.rest import Client

load_dotenv()

REMINDER_MSG = '''
    If you find our service useful, please consider donating at https://tinyurl.com/GEScanDonate once you have successfully booked your appointment.
'''

API_URL = os.getenv("API_URL") if os.getenv("ENV") != 'dev' else 'http://127.0.0.1:5000'
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
client = Client(ACCOUNT_SID, AUTH_TOKEN)

class User():
    def __init__(self, id, phone_number, texts_sent, texts_sent_today):
        self.id = id
        self.phone_number = phone_number
        self.texts_sent = texts_sent
        self.texts_sent_today = texts_sent_today

def users_dict_to_locations_dict(users_dict):
    locations_dict = {}
    for user in users_dict:
        user_obj = User(user["id"], user["phone"], user["texts_sent"], user["texts_sent_today"])
        for location in user["locations"]:
            if location in locations_dict:
                locations_dict[location].add(user_obj)
            else:
                locations_dict[location] = {user_obj}
    return locations_dict

def add_sent_texts_to_db(user_id, message_content):
    requests.put(f"{API_URL}/user/{user_id}", json={'id': user_id,'text_sent': message_content})

def send_text_message(user_id, phone_number, message_content):
    print(phone_number)
    _ = client.messages \
        .create(
            body=message_content,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
    add_sent_texts_to_db(user_id, message_content)
    return

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
    for user in users_dict:
        # We will send the text early in the morning ideally after texts nums have
        # been reset and no texts have been sent. That is why it is set to 0.
        # After a reminder is set it would then be 1.
        if (user['texts_sent_today'] == 0) and (current_day%3==0):
            send_text_message(user['id'], user['phone'], REMINDER_MSG)

    locations_dict = users_dict_to_locations_dict(users_dict)
    for location_id, users in locations_dict.items():
        new_appointments = check_for_appointments(location_id)
        if new_appointments != []:
            location = new_appointments[0].location
            for appointment in new_appointments:
                message_content = f"New Global Entry Appointment Available in {location.city}, {location.state} on {appointment.timestamp}"
                for user in users:
                    if (user.texts_sent_today < 15) and (message_content not in user.texts_sent):
                        send_text_message(user.id, user.phone_number, message_content)
                        user.texts_sent_today += 1
