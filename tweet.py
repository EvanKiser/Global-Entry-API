from appointments import (
    format_past_appointments, 
    format_ttp_date,
    get_appointments, 
    get_location_data,
    MESSAGE_TIME_FORMAT
)
import logging
import json
import os
import random
import requests
import sys
import tweepy

API_URL = os.getenv("API_URL") if os.getenv("ENV") != 'dev' else 'http://127.0.0.1:5000'

API_KEY_1 = os.getenv("TWITTER_API_KEY")
API_KEY_SECRET_1 = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN_1 = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET_1 = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

NOTIF_MESSAGE = 'New Global Entry interview appointment open in {display_name}: {timestamp}\n\nReceive text message alerts for interviews near you for FREE. Link in bio. GlobalEntryScan.com'

def add_tweeted_appointment_to_db(location_id, timestamp):
    requests.put(f"{API_URL}/location/{location_id}", \
        json={'id': location_id,'new_appointment': timestamp})

def get_location_display_name(location_id):
    with open('locations.json') as locations_path:
        locations = json.load(locations_path)
    for location in locations:
        if location["id"] == location_id:
            return location["display_name"]

def send_tweet(location_id, timestamp, api_key, api_key_secret, access_token, access_token_secret):
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_key_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )

    tweet_msg = NOTIF_MESSAGE.format(
        display_name=get_location_display_name(location_id), timestamp=timestamp
    )

    try:
        client.create_tweet(text=tweet_msg)
        logging.info(f"Tweeted: {tweet_msg}")
    except tweepy.errors.Forbidden:
        add_tweeted_appointment_to_db(location_id, timestamp)
        logging.exception(e)
        print(e)
        return False
    except Exception as e:
        logging.exception(e)
        sys.exit(1)
    return True

if __name__ == '__main__':
    for i in range(4):
        if i == 0:
            API_KEY = os.getenv("TWITTER_API_KEY_1")
            API_KEY_SECRET = os.getenv("TWITTER_API_SECRET_1")
            ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN_1")
            ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET_1")
        if i == 1:
            API_KEY = os.getenv("TWITTER_API_KEY_2")
            API_KEY_SECRET = os.getenv("TWITTER_API_SECRET_2")
            ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN_2")
            ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET_2")
        if i == 2:
            API_KEY = os.getenv("TWITTER_API_KEY_3")
            API_KEY_SECRET = os.getenv("TWITTER_API_SECRET_3")
            ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN_3")
            ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET_3")
        if i == 3:
            API_KEY = os.getenv("TWITTER_API_KEY_4")
            API_KEY_SECRET = os.getenv("TWITTER_API_SECRET_4")
            ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN_4")
            ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET_4")
            
        keep_running = True
        while keep_running:
            with open('locations.json') as locations_path:
                locations = json.load(locations_path)
            random_location = locations[random.randint(0, len(locations)-1)]
            random_location_id = random_location["id"]
            appointments = get_appointments(random_location_id, 8)
            if appointments == []:
                continue 
            location = get_location_data(random_location_id)

            # cast past appointments into datetime format
            past_appointments = format_past_appointments(location.past_appointments)

            for appointment in appointments:
                if appointment['active'] <= 0:
                    continue
                date = format_ttp_date(appointment['timestamp'])
                # Check if we have tweeted this appointment before
                if date in past_appointments:
                    continue
                timestamp = date.strftime(MESSAGE_TIME_FORMAT)
                if send_tweet(location.id, timestamp, API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET):
                    add_tweeted_appointment_to_db(location.id, timestamp)
                    keep_running = False
                    break
        