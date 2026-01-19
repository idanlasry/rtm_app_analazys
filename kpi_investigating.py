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


##! creating a patient funnel enrollment -> installing -> active usage kpis-> churn
# last active date per patient (based on is_active_day == 1)
last_active = (
    patient_day.loc[patient_day["is_active_day"] == 1]
    .groupby("patient_id")["date"]
    .max()
    .rename("last_active_date")
    .reset_index()
)

# active days in first 14 / first 30 days since first_data_date
d = patient_day[["patient_id", "date", "is_active_day"]].copy()
d = d.merge(patients[["patient_id", "first_data_date"]], on="patient_id", how="left")
d["day_index"] = (
    d["date"].dt.normalize() - d["first_data_date"].dt.normalize()
).dt.days

w14 = d[(d["day_index"].between(0, 13)) & (d["is_active_day"] == 1)]
w30 = d[(d["day_index"].between(0, 29)) & (d["is_active_day"] == 1)]

active14 = w14.groupby("patient_id")["date"].nunique().rename("active_days_first_14")
active30 = w30.groupby("patient_id")["date"].nunique().rename("active_days_first_30")

patient_funnel = patients.merge(active14, on="patient_id", how="left").merge(
    active30, on="patient_id", how="left"
)
patient_funnel = patient_funnel.merge(last_active, on="patient_id", how="left")

patient_funnel["active_days_first_14"] = (
    patient_funnel["active_days_first_14"].fillna(0).astype(int)
)
patient_funnel["active_days_first_30"] = (
    patient_funnel["active_days_first_30"].fillna(0).astype(int)
)

patient_funnel["is_7_active"] = (patient_funnel["active_days_first_14"] >= 7).astype(
    int
)
patient_funnel["is_16of30"] = (patient_funnel["active_days_first_30"] >= 16).astype(int)

patient_funnel["days_since_last_active"] = (
    -patient_funnel["last_active_date"].dt.normalize()
).dt.days

# eligibility flags
patient_funnel["eligible_14"] = (
    patient_funnel["first_data_date"].notna()
    & (
        as_of_date
        >= (patient_funnel["first_data_date"].dt.normalize() + pd.Timedelta(days=13))
    )
).astype(int)

patient_funnel["eligible_30"] = (
    patient_funnel["first_data_date"].notna()
    & (
        as_of_date
        >= (patient_funnel["first_data_date"].dt.normalize() + pd.Timedelta(days=29))
    )
).astype(int)

patient_funnel.to_csv(OUT / "patient_funnel.csv", index=False)

print("as_of_date:", as_of_date.date())
print("patients:", len(patient_funnel))
print(
    "first_data missing%:",
    round(patient_funnel["first_data_date"].isna().mean() * 100, 2),
)
print("eligible_30:", int(patient_funnel["eligible_30"].sum()))
print(
    "16of30 compliant (eligible only):",
    int(
        (
            (patient_funnel["eligible_30"] == 1) & (patient_funnel["is_16of30"] == 1)
        ).sum()
    ),
)

## function that open a website about the wheather
