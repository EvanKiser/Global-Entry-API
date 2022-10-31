from appointments import (
    format_past_appointments, 
    format_ttp_date,
    get_appointments, 
    get_location_data,
    MESSAGE_TIME_FORMAT
)
from datetime import datetime
import logging
import json
import os
import random
import requests
import sys
import tweepy

API_KEY = os.getenv("TWITTER_API_KEY")
API_KEY_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

NOTIF_MESSAGE = 'New appointment slot open in {city}, {state} at {name}: {timestamp}'

def send_tweet(location, timestamp):
    auth = tweepy.OAuth1UserHandler(
            API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
        )
    api = tweepy.API(auth, wait_on_rate_limit=True)

    tweet_msg = NOTIF_MESSAGE.format(
        city=location.city, state=location.state, name=location.name, timestamp=timestamp
    )

    try:
        api.update_status(tweet_msg)
        logging.info(f"Tweeted: {tweet_msg}")
    except tweepy.errors.Forbidden as duplicate:
        print("Duplicate")
        return False
    except Exception as e:
        logging.exception(e)
        send_text_message("Error Updating Twitter Status. Check logs", '+15016504390')
        sys.exit(1)
    return True

if __name__ == '__main__':
    while True:
        with open('locations.json') as locations_path:
            locations = json.load(locations_path)
        random_location = locations[random.randint(0, len(locations)-1)]
        random_location_id = random_location["id"]
        appointments = get_appointments(random_location_id, 8)
        if appointments == []:
            continue 
        location = get_location_data(random_location_id)

        # cast past appointments into datetime format
        past_appointments = format_past_appointments(location.past_appts_24_hours)

        for appointment in appointments:
            if appointment['active'] <= 0:
                continue
            date = format_ttp_date(appointment['timestamp'])
            # Check if we have tweeted this appointment before
            if date in past_appointments:
                continue
            timestamp = date.strftime(MESSAGE_TIME_FORMAT)
            if send_tweet(location, timestamp):
                sys.exit(1)