#! ----- import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import os
import jason
from pathlib import Path
from helpers import load_tables


##* loading all 7 tabels into a dictionary 'alerts', 'assessment_assignments',
##*'clinics', 'fact_patient_day', 'patients', 'providers', 'rtm_monthly'
tables = load_tables("data")
tables.keys()
for name, table in tables.items():
    print(f"{name},  {table.shape}")
#! unpacking tables
alerts = tables["alerts"]
assign = tables["assessment_assignments"]
clinics = tables["clinics"]
day = tables["fact_patient_day"]
patients = tables["patients"]
providers = tables["providers"]
rtm_monthly = tables["rtm_monthly"]

#! analyzyg d types
for name, table in tables.items():
    print(f"{name} dtypes:\n{table.dtypes}\n")


##
## looking particlary on date colums

print("BEFORE dtypes:")
print(
    "patients:",
    patients[["enrollment_date", "install_date", "first_data_date"]].dtypes.to_dict(),
)
print("day:", day[["date"]].dtypes.to_dict())
print("assign:", assign[["assigned_ts", "completed_ts"]].dtypes.to_dict())
print("alerts:", alerts[["created_ts", "ack_ts"]].dtypes.to_dict())
## transfaring date columns to datetime type


#!-------------------- fetching data from open meteo api
# Calculate dates
today = datetime.now()
week_ago = today - timedelta(days=7)

# Format dates for API (YYYY-MM-DD)
start_date = week_ago.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

# Get Paris weather for past week
url = f"https://api.open-meteo.com/v1/forecast?latitude=32.088472&longitude=34.821614&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,temperature_2m_min"

response = requests.get(url)
data = response.json()
daily_data = data["daily"]
print(daily_data)

#!-------------------- transfering data to pd data frame
df = pd.DataFrame(
    {
        "date": daily_data["time"],
        "temp_max": daily_data["temperature_2m_max"],
        "temp_min": daily_data["temperature_2m_min"],
    }
)

df["date"] = pd.to_datetime(df["date"])
print(df)

# * plotting the data
import matplotlib.pyplot as plt

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(df["date"], df["temp_max"], marker="o", label="Max Temp")
plt.plot(df["date"], df["temp_min"], marker="o", label="Min Temp")

# Add labels and title
plt.xlabel("Date")
plt.ylabel("Temperature (°C)")
plt.title("Ramat Gan Weather - Past 7 Days")
plt.legend()

# Rotate x-axis labels for readability
plt.xticks(rotation=45)
plt.tight_layout()

# Save the plot
plt.savefig("weather_chart.png")
plt.show()


if not os.path.exists("data"):
    os.makedirs("data")

plt.savefig("data/weather_chart.png")
df.to_csv("data/paris_weather.csv", index=False)


print(f"Average temperature: {df['avg_temp'].mean():.1f}°C")
