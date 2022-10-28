import json
from urllib import request
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
    for item in users_dict:
        for _, user in item.items():
            user_phone_number = user["phone"]
            for location in user["locations"]:
                if location in locations_dict:
                    locations_dict.append(user_phone_number)
                else:
                    locations_dict[location] = [user_phone_number]
    return locations_dict

if __name__ == '__main__':
    response = request.urlopen(f"{API_URL}/user")
    data = response.read()
    users_dict = json.loads(data)
    locations_dict = users_dict_to_locations_dict(users_dict)
    for location_code, location_phone_numbers in locations_dict.items():
        pass
        # CAN"T TEXT PPL THE SAME THING
        #   check for new appts
        #   send text about new appt if new appt found