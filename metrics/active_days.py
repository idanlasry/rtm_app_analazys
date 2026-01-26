"""Active days metrics for RTM analysis."""

import pandas as pd
from config import DECEMBER_START, DECEMBER_END


def get_total_active_rate(
    fact_patient_day: pd.DataFrame,
    start_date: str = DECEMBER_START,
    end_date: str = DECEMBER_END,
) -> dict:
    """
    Get total active days rate for a period.

    Returns dict with:
        - total_patient_days: total patient-day records
        - total_active_days: number of active days
        - active_days_rate: percentage of days that are active
    """
    # Filter to date range
    period_activity = fact_patient_day[
        (fact_patient_day["date"] >= start_date)
        & (fact_patient_day["date"] < end_date)
    ]

    total_patient_days = len(period_activity)
    total_active_days = int(period_activity["is_active_day"].sum())
    active_days_rate = (
        (total_active_days / total_patient_days * 100) if total_patient_days > 0 else 0
    )

    return {
        "total_patient_days": total_patient_days,
        "total_active_days": total_active_days,
        "active_days_rate": active_days_rate,
    }


def get_active_rate_by_clinic(
    fact_patient_day: pd.DataFrame,
    clinics: pd.DataFrame,
    start_date: str = DECEMBER_START,
    end_date: str = DECEMBER_END,
) -> pd.DataFrame:
    """
    Get active days rate segmented by clinic.

    Returns DataFrame with columns:
        - clinic_id, clinic_name
        - total_days: total patient-days for clinic
        - active_days: number of active days
        - active_rate: percentage active
    """
    # Filter to date range
    period_activity = fact_patient_day[
        (fact_patient_day["date"] >= start_date)
        & (fact_patient_day["date"] < end_date)
    ]

    # Merge clinic info
    period_with_clinic = period_activity.merge(
        clinics[["clinic_id", "clinic_name"]], on="clinic_id", how="left"
    )

    # Aggregate by clinic
    clinic_active_rate = (
        period_with_clinic.groupby(["clinic_id", "clinic_name"])
        .agg(
            total_days=("is_active_day", "count"),
            active_days=("is_active_day", "sum"),
        )
        .reset_index()
    )

    clinic_active_rate["active_rate"] = (
        clinic_active_rate["active_days"] / clinic_active_rate["total_days"] * 100
    )

    # Sort by active rate descending
    clinic_active_rate = clinic_active_rate.sort_values("active_rate", ascending=False)

    return clinic_active_rate


def get_patient_active_distribution(
    fact_patient_day: pd.DataFrame,
    start_date: str = DECEMBER_START,
    end_date: str = DECEMBER_END,
) -> dict:
    """
    Get patient active days distribution statistics.

    Returns dict with:
        - distribution_df: DataFrame with patient_id and active_days
        - mean: mean active days per patient
        - median: median active days per patient
        - min: minimum active days
        - max: maximum active days
    """
    # Filter to date range
    period_activity = fact_patient_day[
        (fact_patient_day["date"] >= start_date)
        & (fact_patient_day["date"] < end_date)
    ]

    # Count active days per patient
    patient_active_days = (
        period_activity[period_activity["is_active_day"] == 1]
        .groupby("patient_id")
        .size()
        .reset_index(name="active_days")
    )

    # Include patients with 0 active days
    all_patients = period_activity[["patient_id"]].drop_duplicates()
    patient_active_days = all_patients.merge(
        patient_active_days, on="patient_id", how="left"
    ).fillna(0)

    return {
        "distribution_df": patient_active_days,
        "mean": patient_active_days["active_days"].mean(),
        "median": patient_active_days["active_days"].median(),
        "min": int(patient_active_days["active_days"].min()),
        "max": int(patient_active_days["active_days"].max()),
    }
