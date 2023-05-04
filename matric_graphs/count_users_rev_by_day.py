import requests
import json
from collections import Counter
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
time_filter_range_days = 30

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
# Count data points by day
count_by_day = Counter(start_date.date() for start_date in start_dates)
# Sort count_by_day by day
count_by_day = dict(sorted(count_by_day.items()))
# Convert count_by_day to lists of dates and counts
dates = list(count_by_day.keys())
counts = list(count_by_day.values())

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
amount_cents = [int(dp['amount_cents']) for dp in data]
# Sum amount_cents by paid_date
sum_by_day = {}
for i in range(len(paid_dates)):
    if paid_dates[i] in sum_by_day:
        sum_by_day[paid_dates[i]] += (amount_cents[i] / 100)
    else:
        sum_by_day[paid_dates[i]] = (amount_cents[i] / 100)
# Sort sum_by_day by day
sum_by_day = dict(sorted(sum_by_day.items()))
# Convert sum_by_day to lists of dates and sums
sum_dates = list(sum_by_day.keys())
sums = list(sum_by_day.values())

# Create line graph with two lines
fig, ax = plt.subplots()
# Plot data points by start date
ax.bar(dates, counts, label='Data Points by Start Date')
# Plot sums by paid date
ax.bar(sum_dates, sums, label='Sum of Amount Cents by Paid Date')
# Set x-axis label to "Date"
ax.set_xlabel('Date')
# Set y-axis label to "Count / Sum of Amount Cents"
ax.set_ylabel('Count / Sum of Amount Cents')
# Set graph title to "Data Points and Amount Cents by Date (Last Month)"
ax.set_title('Data Points and Amount Cents by Date (Last Month)')
# Display legend
ax.legend()
# Display graph
plt.show()