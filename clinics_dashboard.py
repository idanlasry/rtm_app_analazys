import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
OUT = Path("output")
OUT.mkdir(parents=True, exist_ok=True)

FALL_RISK_THRESHOLD = 0.8
TOP_N_HIGH_RISK_CLINICS = 5

clinics = pd.read_csv(RAW / "clinics.csv")
patients = pd.read_csv(RAW / "patients.csv", usecols=["patient_id", "clinic_id"])
patient_day = pd.read_csv(
    RAW / "fact_patient_day.csv",
    usecols=["patient_id", "steps_count", "is_active_day", "fall_risk_score", "date"],
)
patient_day["date"] = pd.to_datetime(patient_day["date"], errors="coerce")

# Use the latest date in the data as the anchor for the last-7-days window.
as_of_date = patient_day["date"].max()
recent_start = as_of_date - pd.Timedelta(days=6)
recent_mask = patient_day["date"].between(recent_start, as_of_date)

patient_metrics = (
    patient_day.groupby("patient_id")
    .agg(
        avg_steps=("steps_count", "mean"),
        active_days=("is_active_day", "sum"),
        max_fall_risk=("fall_risk_score", "max"),
    )
    .reset_index()
)

recent_metrics = (
    patient_day.loc[recent_mask]
    .groupby("patient_id")
    .agg(
        is_active_last_7d=("is_active_day", lambda s: (s == 1).any()),
        is_high_fall_risk_last_7d=(
            "fall_risk_score",
            lambda s: (s > FALL_RISK_THRESHOLD).any(),
        ),
    )
    .reset_index()
)

patient_metrics = patients.merge(patient_metrics, on="patient_id", how="left").merge(
    recent_metrics, on="patient_id", how="left"
)
patient_metrics[["avg_steps", "active_days", "max_fall_risk"]] = patient_metrics[
    ["avg_steps", "active_days", "max_fall_risk"]
].fillna(0)
patient_metrics[["is_active_last_7d", "is_high_fall_risk_last_7d"]] = patient_metrics[
    ["is_active_last_7d", "is_high_fall_risk_last_7d"]
].fillna(False)
# High fall-risk patients must also be active in the last 7 days.
patient_metrics["is_high_fall_risk_last_7d"] = (
    patient_metrics["is_active_last_7d"] & patient_metrics["is_high_fall_risk_last_7d"]
)

clinic_metrics = (
    patient_metrics.groupby("clinic_id")
    .agg(
        total_patients=("patient_id", "nunique"),
        avg_steps_per_patient=("avg_steps", "mean"),
        avg_active_days_per_patient=("active_days", "mean"),
        active_users_last_7d=("is_active_last_7d", "sum"),
        high_fall_risk_patients=("is_high_fall_risk_last_7d", "sum"),
    )
    .reset_index()
)
clinic_metrics = clinic_metrics.rename(
    columns={"high_fall_risk_patients": "high_fall_risk_patients_last_7d"}
)
clinic_metrics[["avg_steps_per_patient", "avg_active_days_per_patient"]] = (
    clinic_metrics[["avg_steps_per_patient", "avg_active_days_per_patient"]].round(2)
)

clinic_metrics = clinics.merge(clinic_metrics, on="clinic_id", how="left")
numeric_cols = [
    "total_patients",
    "avg_steps_per_patient",
    "avg_active_days_per_patient",
    "active_users_last_7d",
    "high_fall_risk_patients_last_7d",
]
clinic_metrics[numeric_cols] = clinic_metrics[numeric_cols].fillna(0)
clinic_metrics["high_fall_risk_patient_rate"] = (
    clinic_metrics["high_fall_risk_patients_last_7d"]
    / clinic_metrics["total_patients"]
).fillna(0)
clinic_metrics["high_fall_risk_patient_rate"] = clinic_metrics[
    "high_fall_risk_patient_rate"
].round(3)

overall_active_days = (
    patient_metrics.set_index("patient_id")["active_days"]
    .reindex(patients["patient_id"].unique(), fill_value=0)
    .mean()
)
overall_metrics = pd.DataFrame(
    [
        {
            "total_clinics": clinics["clinic_id"].nunique(),
            "total_patients": patients["patient_id"].nunique(),
            "overall_avg_active_days_per_patient": overall_active_days,
        }
    ]
)

high_risk_clinics = clinic_metrics.sort_values(
    ["high_fall_risk_patients_last_7d", "high_fall_risk_patient_rate"],
    ascending=False,
).head(TOP_N_HIGH_RISK_CLINICS)

dashboard_columns = [
    "clinic_id",
    "clinic_name",
    "region",
    "total_patients",
    "active_users_last_7d",
    "high_fall_risk_patients_last_7d",
    "high_fall_risk_patient_rate",
    "avg_steps_per_patient",
    "avg_active_days_per_patient",
]
clinic_metrics = clinic_metrics.reindex(columns=dashboard_columns)

clinic_metrics.to_csv(OUT / "clinics_dashboard.csv", index=False)
overall_metrics.to_csv(OUT / "clinics_overview.csv", index=False)
high_risk_clinics.to_csv(OUT / "clinics_high_fall_risk.csv", index=False)

print("Wrote:", OUT / "clinics_dashboard.csv")
print("Wrote:", OUT / "clinics_overview.csv")
print("Wrote:", OUT / "clinics_high_fall_risk.csv")
