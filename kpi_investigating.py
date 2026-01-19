import pandas as pd
from pathlib import Path

## seeting paths
RAW = Path("data/raw")
OUT = Path("data/processed")
# create output directory if not exists
OUT.mkdir(parents=True, exist_ok=True)

## loading raw data
patients = pd.read_csv(RAW / "patients.csv")
day_raw = pd.read_csv(RAW / "fact_patient_day.csv")

## parsing date columns
# patients data dates
patients["enrollment_date"] = pd.to_datetime(
    patients["enrollment_date"], errors="coerce"
)
patients["install_date"] = pd.to_datetime(patients["install_date"], errors="coerce")
patients["first_data_date"] = pd.to_datetime(
    patients["first_data_date"], errors="coerce"
)
# day_raw data dates
day_raw["date"] = pd.to_datetime(day_raw["date"], errors="coerce")

## user daily activity table processing->select what i need from day_raw
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
## setting date column as date only
patient_day["date"] = pd.to_datetime(patient_day["date"]).dt.date
# then groupby("date")

##? quality chercking for duplicates of user-day level as a praimery key
patient_day_dup = (
    patient_day.groupby(["patient_id", "date"])
    .size()
    .reset_index(name="n")
    .query("n > 1")
)
if patient_day_dup.empty:
    print("no duplicates in 'patient_day' table")  # there are no duplicates
# patient_day = patient_day.drop_duplicates(subset=["patient_id", "date"])

print("presenting basic checks abou the 'patient_day' table:")
print("shape:", patient_day.shape)
print("date range:", patient_day["date"].min(), "->", patient_day["date"].max())
print("active days rate:", round(patient_day["is_active_day"].mean(), 3))
print(
    "active days per user mean:",
    round(patient_day.groupby("patient_id")["is_active_day"].sum().mean(), 3),
)
## saving processed data
patient_day.to_csv(OUT / "fact_patient_day.csv", index=False)
