import requests
from appointments import check_for_appointments
from dotenv import load_dotenv
import os
from twilio.rest import Client

load_dotenv()

API_URL = os.getenv("API_URL") if os.getenv("ENV") != 'dev' else 'http://127.0.0.1:5000'
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
                locations_dict[location].add(user_phone_number)
            else:
                locations_dict[location] = {user_phone_number}
    return locations_dict

def add_appointments_to_db(new_appointments):
    location = new_appointments[0].location
    for appointment in new_appointments:
        location.past_appts_24_hours.append(appointment.timestamp)
    requests.put(f"{API_URL}/location/{location.id}", 
        json={'id': location.id,'past_appts_24_hours': location.past_appts_24_hours})

def send_text_message(appointment, phone_numbers):
    location = appointment.location
    message_content = f"New Global Entry Appointment Available in {location.city}, {location.state} at {appointment.timestamp}"
    for phone_number in phone_numbers:
        _ = client.messages \
            .create(
                body=message_content,
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
    return

if __name__ == '__main__':
    response = requests.get(f"{API_URL}/user")
    users_dict = response.json()
    locations_dict = users_dict_to_locations_dict(users_dict)
    for location_id, phone_numbers in locations_dict.items():
        print(phone_numbers)
        new_appointments = check_for_appointments(location_id)
        if new_appointments != []:
            add_appointments_to_db(new_appointments)
            for appointment in new_appointments:
                send_text_message(appointment, phone_numbers)