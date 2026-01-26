"""KPI metrics for RTM analysis - bi-weekly trends."""

import pandas as pd
from config import ACTIVE_BIWEEK_THRESHOLD


def get_active_users_biweekly(
    fact_patient_day: pd.DataFrame,
    active_threshold: int = ACTIVE_BIWEEK_THRESHOLD,
) -> pd.DataFrame:
    """
    Get active users per bi-week (2-week periods).

    Active user = patient with threshold+ active days in the bi-week.

    Returns DataFrame with columns:
        - bi_week: period identifier
        - active_users: count of active users
    """
    # Create bi-weekly periods
    df = fact_patient_day.copy()
    df["bi_week"] = df["date"].dt.to_period("2W-MON")

    # Count active days per patient per bi-week
    biweekly_active_days = (
        df[df["is_active_day"] == 1]
        .groupby(["patient_id", "bi_week"])
        .size()
        .reset_index(name="active_days")
    )

    # Filter patients with threshold+ active days per bi-week
    active_users_per_biweek = (
        biweekly_active_days[biweekly_active_days["active_days"] >= active_threshold]
        .groupby("bi_week")
        .size()
        .reset_index(name="active_users")
    )

    return active_users_per_biweek


def get_enrollments_biweekly(patients: pd.DataFrame) -> pd.DataFrame:
    """
    Get new patient enrollments per bi-week.

    Returns DataFrame with columns:
        - bi_week: period identifier
        - new_patients: count of new enrollments
    """
    df = patients.copy()
    df["bi_week"] = df["enrollment_date"].dt.to_period("2W-MON")

    enrollments_per_biweek = (
        df.groupby("bi_week").size().reset_index(name="new_patients")
    )

    return enrollments_per_biweek


def calculate_period_changes(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """
    Calculate period-over-period changes for a metric.

    Args:
        df: DataFrame with bi_week and value column
        value_col: name of the value column to calculate changes for

    Returns DataFrame with added columns:
        - change: absolute change from previous period
        - pct_change: percentage change from previous period
    """
    result = df.copy()
    result["change"] = result[value_col].diff()
    result["pct_change"] = result[value_col].pct_change() * 100
    return result
