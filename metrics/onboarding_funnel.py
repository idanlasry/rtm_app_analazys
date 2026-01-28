"""Patient funnel metrics for RTM analysis."""

import pandas as pd


def get_patient_funnel(
    patients: pd.DataFrame,
    fact_patient_day: pd.DataFrame,
    billing_compliance_threshold: int = 16,
) -> dict:
    """
    Calculate patient funnel from enrollment to compliance.

    Funnel stages:
        1. Enrolled - patients with enrollment_date
        2. Installed - patients with install_date
        3. First Data - patients with first_data_date within 1 week from enrollment
        4. 16/30 Compliant - 16+ active days in first 30 days from enrollment

    Returns dict with:
        - funnel_df: DataFrame with stage, count, rate, dropoff
        - stage_patients: dict mapping stage name to patient IDs
    """
    # Stage 1: Enrolled
    enrolled = patients[patients["enrollment_date"].notna()]["patient_id"].unique()
    enrolled_count = len(enrolled)

    # Stage 2: Installed
    installed = patients[patients["install_date"].notna()]["patient_id"].unique()
    installed_count = len(installed)

    # Stage 3: First Data (within 1 week from enrollment)
    patients_with_first_data = patients[
        (patients["first_data_date"].notna()) & (patients["enrollment_date"].notna())
    ].copy()
    patients_with_first_data["days_to_first_data"] = (
        patients_with_first_data["first_data_date"]
        - patients_with_first_data["enrollment_date"]
    ).dt.days
    first_data = patients_with_first_data[
        (patients_with_first_data["days_to_first_data"] >= 0)
        & (patients_with_first_data["days_to_first_data"] <= 7)
    ]["patient_id"].unique()
    first_data_count = len(first_data)

    # Stage 4: 16/30 Compliant (16+ active days in first 30 days from enrollment)
    patients_with_dates = patients[["patient_id", "enrollment_date"]].copy()
    activity_merged = fact_patient_day.merge(patients_with_dates, on="patient_id")
    activity_merged["days_since_enrollment"] = (
        activity_merged["date"] - activity_merged["enrollment_date"]
    ).dt.days

    first_30_days_activity = activity_merged[
        (activity_merged["days_since_enrollment"] >= 0)
        & (activity_merged["days_since_enrollment"] < 30)
    ]
    active_days_first_30 = (
        first_30_days_activity[first_30_days_activity["is_active_day"] == 1]
        .groupby("patient_id")
        .size()
    )
    compliant_patients = active_days_first_30[
        active_days_first_30 >= billing_compliance_threshold
    ].index.tolist()
    compliant_count = len(compliant_patients)

    # Build funnel DataFrame
    stages = [
        ("1. Enrolled", enrolled_count),
        ("2. Installed", installed_count),
        ("3. First Data", first_data_count),
        ("4. 16/30 Compliant", compliant_count),
    ]

    funnel_df = pd.DataFrame(stages, columns=["stage", "count"])
    funnel_df["rate_from_enrolled"] = (funnel_df["count"] / enrolled_count * 100).round(
        1
    )
    funnel_df["rate_from_previous"] = (
        funnel_df["count"] / funnel_df["count"].shift(1) * 100
    ).round(1)
    funnel_df.loc[0, "rate_from_previous"] = 100.0

    return {
        "funnel_df": funnel_df,
        "stage_patients": {
            "enrolled": enrolled.tolist(),
            "installed": installed.tolist(),
            "first_data": first_data.tolist(),
            "compliant": compliant_patients,
        },
    }


def print_funnel(funnel_result: dict) -> None:
    """Print funnel results in a formatted way."""
    df = funnel_result["funnel_df"]
    enrolled_count = df.loc[0, "count"]

    print("\nPATIENT FUNNEL")
    print("-" * 50)

    for _, row in df.iterrows():
        bar_length = int(row["rate_from_enrolled"] / 2)
        bar = "█" * bar_length
        print(
            f"{row['stage']:<25} {row['count']:>5,} "
            f"({row['rate_from_enrolled']:>5.1f}%) {bar}"
        )

    print("-" * 50)
    print(
        f"Overall conversion: {df.iloc[-1]['count']:,} / {enrolled_count:,} "
        f"= {df.iloc[-1]['rate_from_enrolled']:.1f}%"
    )
