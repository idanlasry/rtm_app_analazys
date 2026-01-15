#! ----- import requests
import os
from datetime import datetime, timedelta

import pandas as pd

from helpers import load_tables

##* loading all 7 tabels into a dictionary 'alerts', 'assessment_assignments',
##*'clinics', 'fact_patient_day', 'patients', 'providers', 'rtm_monthly'
tables = load_tables("data/raw")
tables.keys()  # view the loaded raw tabels

for name, table in tables.items():
    print(f"{name},  {table.shape}")  # view the shape of each table

## unpacking tables
alerts = tables["alerts"]
assign = tables["assessment_assignments"]
clinics = tables["clinics"]
day = tables["fact_patient_day"]
patients = tables["patients"]
providers = tables["providers"]
rtm_monthly = tables["rtm_monthly"]

## analyzyg data types
for name, table in tables.items():
    print(f"{name} dtypes:\n{table.dtypes}\n")

#############? looking particlary on date colums####################
print("BEFORE dtypes:")
print(
    "patients:",
    patients[["enrollment_date", "install_date", "first_data_date"]].dtypes.to_dict(),
)
print("day:", day[["date"]].dtypes.to_dict())
print("assign:", assign[["assigned_ts", "completed_ts"]].dtypes.to_dict())
print("alerts:", alerts[["created_ts", "ack_ts"]].dtypes.to_dict())
# seems all the date columns are object dtypes

##  converting date columns to datetime dtype
date_columns = [
    (patients, ["enrollment_date", "install_date", "first_data_date"]),
    (day, ["date"]),
    (assign, ["assigned_ts", "completed_ts"]),
    (alerts, ["created_ts", "ack_ts"]),
]  # listing the date columns to convert

for table, cols in date_columns:
    table[cols] = table[cols].apply(
        pd.to_datetime, errors="coerce", cache=True
    )  # converting

## rechecking dtypes after conversion
print("AFTER dtypes:")
print("day:", day[["date"]].dtypes.to_dict())
print("assign:", assign[["assigned_ts", "completed_ts"]].dtypes.to_dict())
print("alerts:", alerts[["created_ts", "ack_ts"]].dtypes.to_dict())
# * all date columns are now datetime dtypes

## saving cleaned data
cleaned_data_dir = os.path.join(
    "data", "cleaned data"
)  # making a path for cleaned data
os.makedirs(cleaned_data_dir, exist_ok=True)  # creating directory in the path
for name, table in tables.items():
    table.to_csv(
        os.path.join(cleaned_data_dir, f"{name}.csv"), index=False
    )  # saving the scv files in the path

## checking quality of date columns
print("\nParse quality:")

print(
    "patients first_data_date NaT%:",
    round(patients["first_data_date"].isna().mean() * 100, 2),
)
print("day date NaT%:", round(day["date"].isna().mean() * 100, 2))
print("day range:", day["date"].min() - day["date"].max())
############# finish looking particlary on date colums####################
