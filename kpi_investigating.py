import pandas as pd
from pathlib import Path

## loading raw data
RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT = Path("output")
OUTPUT.mkdir(parents=True, exist_ok=True)


patients = pd.read_csv(RAW / "patients.csv")
day_raw = pd.read_csv(RAW / "fact_patient_day.csv")

## pasing date columns
patients["first_data_date"] = pd.to_datetime(
    patients["first_data_date"], errors="coerce"
)

day_raw["date"] = pd.to_datetime(day_raw["date"], errors="coerce")

## building a daily data per user table
# select what i need from day_raw
patient_day = day_raw[
    [
        "patient_id",
        "clinic_id",
        "date",
        "background_data_minutes",
        "steps_count",
        "is_active_day",
        "walk_score",
        "fall_risk_score",
    ]
].copy()

##? quality chercking for duplicates of user-day level as a praimery key
counts = (
    patient_day.groupby(["patient_id", "date"])
    .size()
    .reset_index(name="n")
    .query("n > 1")
)
print(counts.head())  # there are no duplicates
# patient_day = patient_day.drop_duplicates(subset=["patient_id", "date"])

# basic checks
print("shape:", patient_day.shape)
print("date range:", patient_day["date"].min(), "->", patient_day["date"].max())
print("active_day_rate:", round(patient_day["is_active_day"].mean(), 3))
print(
    "active_day_per_user_rate:",
    round(patient_day.groupby("patient_id")["is_active_day"].sum().mean(), 3),
)
## saving processed data
patient_day.to_csv(OUT / "fact_patient_day.csv", index=False)
