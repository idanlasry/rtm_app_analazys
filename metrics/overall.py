"""Overall metrics for RTM analysis."""

import pandas as pd
from config import (
    ANALYSIS_DATE,
    BILLING_THRESHOLD,
    FALL_RISK_THRESHOLD,
    FALL_RISK_LOOKBACK_DAYS,
    DECEMBER_START,
    DECEMBER_END,
)


def get_patient_count(patients: pd.DataFrame) -> int:
    """Get total number of patients."""
    return len(patients)


def get_billable_patients(
    fact_patient_day: pd.DataFrame,
    start_date: str = DECEMBER_START,
    end_date: str = DECEMBER_END,
    threshold: int = BILLING_THRESHOLD,
) -> dict:
    """
    Get billable patients (16+ active days in period).

    Returns dict with:
        - billable_count: number of billable patients
        - total_patients: total patients in period
        - billable_rate: percentage billable
        - billable_patient_ids: list of billable patient IDs
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
    )

    # Find billable patients (threshold+ active days)
    billable_patients = patient_active_days[patient_active_days >= threshold]
    billable_count = len(billable_patients)
    total_patients = period_activity["patient_id"].nunique()

    billable_rate = (billable_count / total_patients * 100) if total_patients > 0 else 0

    return {
        "billable_count": billable_count,
        "total_patients": total_patients,
        "billable_rate": billable_rate,
        "billable_patient_ids": billable_patients.index.tolist(),
    }


def get_active_patients(
    fact_patient_day: pd.DataFrame,
    start_date: str = DECEMBER_START,
    end_date: str = DECEMBER_END,
) -> dict:
    """
    Get active patients (at least 1 active day in period).

    Returns dict with:
        - active_count: number of active patients
        - total_patients: total patients in period
        - active_rate: percentage active
    """
    # Filter to date range
    period_activity = fact_patient_day[
        (fact_patient_day["date"] >= start_date)
        & (fact_patient_day["date"] < end_date)
    ]

    active_patients = period_activity[period_activity["is_active_day"] == 1][
        "patient_id"
    ].nunique()
    total_patients = period_activity["patient_id"].nunique()

    active_rate = (active_patients / total_patients * 100) if total_patients > 0 else 0

    return {
        "active_count": active_patients,
        "total_patients": total_patients,
        "active_rate": active_rate,
    }


def get_high_fall_risk_patients(
    fact_patient_day: pd.DataFrame,
    analysis_date: pd.Timestamp = ANALYSIS_DATE,
    lookback_days: int = FALL_RISK_LOOKBACK_DAYS,
    threshold: int = FALL_RISK_THRESHOLD,
) -> dict:
    """
    Get patients with high fall risk score in recent days.

    Returns dict with:
        - high_risk_count: number of high risk patients
        - high_risk_rate: percentage of all patients
        - high_risk_patient_ids: list of patient IDs
    """
    # Filter to lookback period
    start_date = analysis_date - pd.Timedelta(days=lookback_days)
    recent_activity = fact_patient_day[
        (fact_patient_day["date"] >= start_date)
        & (fact_patient_day["date"] <= analysis_date)
    ]

    # Find patients with high fall risk
    high_risk_records = recent_activity[recent_activity["fall_risk_score"] >= threshold]
    high_risk_patients = high_risk_records["patient_id"].unique()
    high_risk_count = len(high_risk_patients)

    total_patients = recent_activity["patient_id"].nunique()
    high_risk_rate = (high_risk_count / total_patients * 100) if total_patients > 0 else 0

    return {
        "high_risk_count": high_risk_count,
        "total_patients": total_patients,
        "high_risk_rate": high_risk_rate,
        "high_risk_patient_ids": high_risk_patients.tolist(),
    }
