import requests
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

#!-------------------- fetching data from open meteo api--------------------------------------------
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
