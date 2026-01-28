"""Active days metrics for RTM analysis."""

import pandas as pd
from config import DATE_START, DATE_END


def get_total_active_rate(
    fact_patient_day: pd.DataFrame,
    start_date: str = DATE_START,
    end_date: str = DATE_END,
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
    start_date: str = DATE_START,
    end_date: str = DATE_END,
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
    start_date: str = DATE_START,
    end_date: str = DATE_END,
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


def get_active_rate_by_day_since_enrollment(
    patients: pd.DataFrame,
    fact_patient_day: pd.DataFrame,
    days_after_enrollment: int = 30,
) -> dict:
    """
    Get active rate distribution normalized by patient enrollment date.

    Each patient's enrollment date is treated as day 0, and we calculate
    what percentage of patients are active on each day (0 to days_after_enrollment).

    Args:
        patients: DataFrame with patient_id and enrollment_date
        fact_patient_day: DataFrame with patient_id, date, is_active_day
        days_after_enrollment: Number of days to track after enrollment (default 30)

    Returns dict with:
        - distribution_df: DataFrame with day_since_enrollment, total_patients,
          active_patients, active_rate
        - summary: dict with mean/median/min/max active rates across days
    """
    # Get patients with valid enrollment dates
    patients_with_dates = patients[patients["enrollment_date"].notna()][
        ["patient_id", "enrollment_date"]
    ].copy()

    # Merge activity with enrollment dates
    activity_merged = fact_patient_day.merge(patients_with_dates, on="patient_id")

    # Calculate days since enrollment
    activity_merged["day_since_enrollment"] = (
        activity_merged["date"] - activity_merged["enrollment_date"]
    ).dt.days

    # Filter to valid range (0 to days_after_enrollment)
    activity_in_range = activity_merged[
        (activity_merged["day_since_enrollment"] >= 0)
        & (activity_merged["day_since_enrollment"] <= days_after_enrollment)
    ]

    # Group by day_since_enrollment and calculate stats
    daily_stats = (
        activity_in_range.groupby("day_since_enrollment")
        .agg(
            total_patients=("patient_id", "nunique"),
            active_patients=("is_active_day", "sum"),
        )
        .reset_index()
    )

    daily_stats["active_rate"] = (
        daily_stats["active_patients"] / daily_stats["total_patients"] * 100
    )

    # Ensure all days 0-30 are represented (fill missing with 0)
    all_days = pd.DataFrame(
        {"day_since_enrollment": range(days_after_enrollment + 1)}
    )
    distribution_df = all_days.merge(daily_stats, on="day_since_enrollment", how="left")
    distribution_df = distribution_df.fillna(0)

    return {
        "distribution_df": distribution_df,
        "summary": {
            "mean_active_rate": distribution_df["active_rate"].mean(),
            "median_active_rate": distribution_df["active_rate"].median(),
            "min_active_rate": distribution_df["active_rate"].min(),
            "max_active_rate": distribution_df["active_rate"].max(),
        },
    }
