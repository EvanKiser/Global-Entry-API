from datetime import datetime, timedelta
from sqlite3 import Timestamp
from dotenv import load_dotenv
import json
import logging
import requests
import os
from urllib import request

load_dotenv()

API_URL = os.getenv("API_URL")

SCHEDULER_API_URL = 'https://ttp.cbp.dhs.gov/schedulerapi/locations/{location}/slots?startTimestamp={start}&endTimestamp={end}'
TTP_TIME_FORMAT = '%Y-%m-%dT%H:%M'
MESSAGE_TIME_FORMAT = '%A, %B %d, %Y at %I:%M %p'

class Appointment:
    def __init__(self, name, city, state, timestamp):
        self.name = name
        self.city = city
        self.state = state
        self.timestamp = timestamp

def check_for_appointments(location_id):
    start = datetime.now()
    end = start + timedelta(weeks=6)

    url = SCHEDULER_API_URL.format(location=location_id,
                                   start=start.strftime(TTP_TIME_FORMAT),
                                   end=end.strftime(TTP_TIME_FORMAT))

    try:
        results = requests.get(url).json()  # List of flat appointment objects
    except requests.ConnectionError:
        logging.exception('Could not connect to scheduler API')
        return

    
    response = request.urlopen(f"{API_URL}/location/{location_id}")
    data = response.read()
    location = json.loads(data)

    new_appointments = []
    for result in results:
        if result['active'] > 0:
            date = datetime.strptime(result['timestamp'], TTP_TIME_FORMAT)
            timestamp = date.strftime(MESSAGE_TIME_FORMAT)
            # Check if we have seen this appointment in the last 24 hours
            if timestamp not in location.past_appts_24_hours:
                new_appt = Appointment(location.name, location.city, location.state, timestamp)
                new_appointments.append(new_appt)
    return new_appointments