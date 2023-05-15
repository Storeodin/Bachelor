import requests
import json
import datetime
from matplotlib import pyplot as plt

today = datetime.datetime.now().strftime("%Y/%m-%d")
tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y/%m-%d")

response_today = requests.get(f"https://www.hvakosterstrommen.no/api/v1/prices/{today}_NO1.json").text
response_tomorrow = requests.get(f"https://www.hvakosterstrommen.no/api/v1/prices/{tomorrow}_NO1.json").text

response_info_today = json.loads(response_today)
response_info_tomorrow = json.loads(response_tomorrow)

price_today = []
time_today = []
price_tomorrow = []
time_tomorrow = []

i = 0
for row in response_info_today:
    price_today.append(row["NOK_per_kWh"])
    time_today.append(i)
    i += 1

i = 0
for row in response_info_tomorrow:
    price_tomorrow.append(row["NOK_per_kWh"])
    time_tomorrow.append(i)
    i += 1

fig, axs = plt.subplots(2)
axs[0].bar(time_today, price_today, label='Today')
axs[0].legend()
axs[1].bar(time_tomorrow, price_tomorrow, label='Tomorrow')
axs[1].legend()
plt.show()

print("Today's prices: ",price_today)
print("Tomorrow's prices: ",price_tomorrow)
