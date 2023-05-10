import requests
from datetime import datetime, timedelta
from collections import Counter
import matplotlib.pyplot as plt
from collections import defaultdict
import json

time_filter_range_days = 28

# Make HTTP request to API endpoint
response = requests.get('https://global-entry-api.onrender.com/user/all')
# Parse JSON response
data = json.loads(response.text)
# Extract start_date values and convert them to datetime objects
start_dates = [datetime.strptime(dp['start_date'], '%a, %d %b %Y %H:%M:%S %Z') for dp in data]
# Calculate date from one month ago
time_filter = datetime.now() - timedelta(days=time_filter_range_days)
# Filter start_dates to only include dates from the last month
start_dates = [start_date for start_date in start_dates if start_date >= time_filter]
start_dates.sort()
# Count data points by day
count_by_day = Counter(start_date.date() for start_date in start_dates)
# Sort count_by_day by day
count_by_day = dict(sorted(count_by_day.items()))
running_total = 0
sum_over_time = {}
for i in count_by_day:
    running_total += count_by_day[i]
    sum_over_time[i] = running_total

# Make HTTP request to paid endpoint
response = requests.get('https://global-entry-api.onrender.com/paid/all')
# Parse JSON response
data = json.loads(response.text)
# Extract paid_date values and amount_cents values
paid_dates = [datetime.strptime(dp['paid_date'], '%a, %d %b %Y %H:%M:%S %Z') for dp in data]
# Calculate date from one month ago
time_filter = datetime.now() - timedelta(days=time_filter_range_days)
# Filter start_dates to only include dates from the last month
paid_dates = [paid_date.date() for paid_date in paid_dates if paid_date >= time_filter]
# Extract amount_cents values
amount_cents = {datetime.strptime(dp['paid_date'], '%a, %d %b %Y %H:%M:%S %Z').date():int(dp['amount_cents']) for dp in data}
# Sum amount_cents by paid_date
amounts_by_day = {}
running_total = 0
for i in paid_dates:
    running_total += amount_cents[i] / 100
    amounts_by_day[i] = running_total
# Sort amounts_by_day by day
amounts_by_day = dict(sorted(amounts_by_day.items()))

# Plot the data on a line graph
plt.plot(list(sum_over_time.keys()), list(sum_over_time.values()), label='New Global Entry Memberships')
plt.plot(list(amounts_by_day.keys()), list(amounts_by_day.values()), label='Amount Paid')
plt.xlabel('Date')
plt.ylabel('Count/Amount')
plt.legend()
plt.show()
