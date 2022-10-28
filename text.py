import json
from urllib import request
from appointments import check_for_appointments
from dotenv import load_dotenv
import os
from twilio.rest import Client

load_dotenv()

API_URL = os.getenv("API_URL")
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def users_dict_to_locations_dict(users_dict):
    locations_dict = {}
    for user in users_dict:
        user_phone_number = user["phone"]
        for location in user["locations"]:
            if location in locations_dict:
                locations_dict[location].append(user_phone_number)
            else:
                locations_dict[location] = [user_phone_number]
    return locations_dict

def send_text_message(appointment, phone_numbers):
    message_content = f"New Global Entry Appointment Available in {appointment.city}, {appointment.state} at {appointment.timestamp}"
    for phone_number in phone_numbers:
        _ = client.messages \
            .create(
                body=message_content,
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
    return

if __name__ == '__main__':
    response = request.urlopen(f"{API_URL}/user")
    data = response.read()
    users_dict = json.loads(data)
    locations_dict = users_dict_to_locations_dict(users_dict)
    for location_id, phone_numbers in locations_dict.items():
        new_appointments = check_for_appointments(location_id)
        for appointment in new_appointments:
            # update database obj with new appts
            send_text_message(phone_numbers)