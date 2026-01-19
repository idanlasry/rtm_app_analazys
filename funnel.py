import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

# load
patients = pd.read_csv(RAW / "patients.csv")
patient_day = pd.read_csv(OUT / "fact_patient_day.csv")

# parse dates
for c in ["enrollment_date", "install_date", "first_data_date"]:
    patients[c] = pd.to_datetime(patients[c], errors="coerce")
patient_day["date"] = pd.to_datetime(patient_day["date"], errors="coerce")

# as-of date (global snapshot date)
as_of_date = patient_day["date"].max().normalize()

# last active date (using is_active_day)
last_active = (
    patient_day.loc[patient_day["is_active_day"] == 1]
    .groupby("patient_id")["date"]
    .max()
    .rename("last_active_date")
)

# active days in first 14 / first 30 days since first_data_date
d = patient_day[["patient_id", "date", "is_active_day"]].copy()
d = d.merge(patients[["patient_id", "first_data_date"]], on="patient_id", how="left")
d["day_index"] = (
    d["date"].dt.normalize() - d["first_data_date"].dt.normalize()
).dt.days

active14 = (
    d[(d["day_index"].between(0, 13)) & (d["is_active_day"] == 1)]
    .groupby("patient_id")["date"]
    .nunique()
    .rename("active_days_first_14")
)

active30 = (
    d[(d["day_index"].between(0, 29)) & (d["is_active_day"] == 1)]
    .groupby("patient_id")["date"]
    .nunique()
    .rename("active_days_first_30")
)

# assemble patient_funnel
patient_funnel = patients.set_index("patient_id").copy()
patient_funnel = patient_funnel.join([active14, active30, last_active])

patient_funnel["active_days_first_14"] = (
    patient_funnel["active_days_first_14"].fillna(0).astype(int)
)
patient_funnel["active_days_first_30"] = (
    patient_funnel["active_days_first_30"].fillna(0).astype(int)
)

patient_funnel["is_installed"] = patient_funnel["install_date"].notna().astype(int)
patient_funnel["has_first_data"] = patient_funnel["first_data_date"].notna().astype(int)

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

# enforce eligibility in flags (so rates are correct)
patient_funnel["is_7_active"] = (
    (patient_funnel["active_days_first_14"] >= 7) & (patient_funnel["eligible_14"] == 1)
).astype(int)
patient_funnel["is_16of30"] = (
    (patient_funnel["active_days_first_30"] >= 16)
    & (patient_funnel["eligible_30"] == 1)
).astype(int)

patient_funnel["days_since_last_active"] = (
    as_of_date - patient_funnel["last_active_date"].dt.normalize()
).dt.days
patient_funnel["at_risk_3d"] = (
    (patient_funnel["has_first_data"] == 1)
    & (patient_funnel["days_since_last_active"] >= 3)
).astype(int)

# save
patient_funnel = patient_funnel.reset_index()
patient_funnel.to_csv(OUT / "patient_funnel.csv", index=False)

# quick sanity prints
print("as_of_date:", as_of_date.date())
print("patients rows:", len(patient_funnel))
print(
    "missing first_data%:",
    round(patient_funnel["first_data_date"].isna().mean() * 100, 2),
)
print("eligible_30:", int(patient_funnel["eligible_30"].sum()))
print("16of30 compliant (eligible):", int(patient_funnel["is_16of30"].sum()))
print("at_risk_3d:", int(patient_funnel["at_risk_3d"].sum()))
