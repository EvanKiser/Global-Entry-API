from datetime import datetime, timedelta
from app import Location
from dotenv import load_dotenv
import json
import logging
import requests
import os

load_dotenv()

API_URL = os.getenv("API_URL") if os.getenv("ENV") != 'dev' else 'http://127.0.0.1:5000'

SCHEDULER_API_URL = 'https://ttp.cbp.dhs.gov/schedulerapi/locations/{location}/slots?startTimestamp={start}&endTimestamp={end}'
TTP_TIME_FORMAT = '%Y-%m-%dT%H:%M'
POSTGRES_TIME_FORMAT = '%a, %d %b %Y %H:%M:%S'
MESSAGE_TIME_FORMAT = '%A, %B %d, %Y at %I:%M %p'

class Appointment:
    def __init__(self, location: Location, timestamp):
        self.location = location
        self.timestamp = timestamp

def check_for_appointments(location_id):
    start = datetime.now()
    end = start + timedelta(weeks=6)

    url = SCHEDULER_API_URL.format(location=location_id,
                                   start=start.strftime(TTP_TIME_FORMAT),
                                   end=end.strftime(TTP_TIME_FORMAT))

    try:
        print(url)
        results = requests.get(url).json()  # List of flat appointment objects
    except requests.ConnectionError:
        logging.exception('Could not connect to scheduler API')
        return

    
    response = requests.get(f"{API_URL}/location/{location_id}")
    location = response.json()
    location = Location(location['id'], 
                        location['name'], 
                        location['code'], 
                        location['city'], 
                        location['state'],
                        location['past_appts_24_hours']
                    )

    past_appts_24_hours = []
    for appointment in location.past_appts_24_hours:
        past_appointment_time = datetime.strptime(appointment[:-4], POSTGRES_TIME_FORMAT)
        past_appts_24_hours.append(past_appointment_time)

    new_appointments = []
    for result in results:
        if result['active'] > 0:
            date = datetime.strptime(result['timestamp'], TTP_TIME_FORMAT) 
            timestamp = date.strftime(MESSAGE_TIME_FORMAT)
            # Check if we have seen this appointment in the last 24 hours
            if date not in past_appts_24_hours:
                new_appt = Appointment(location, timestamp)
                new_appointments.append(new_appt)
    return new_appointments

if __name__ == '__main__':
    with open('locations.json') as locations_path:
        locations = json.load(locations_path)
    start = datetime.now()
    end = start + timedelta(weeks=2)
    for location in locations:
        url = SCHEDULER_API_URL.format(location=location["id"],
                                   start=start.strftime(TTP_TIME_FORMAT),
                                   end=end.strftime(TTP_TIME_FORMAT))

        try:
            results = requests.get(url).json()
        except requests.ConnectionError:
            logging.exception('Could not connect to scheduler API')
        for result in results:
            if result['active'] > 0:
                date = datetime.strptime(result['timestamp'], TTP_TIME_FORMAT) 
                print(location["name"], date)