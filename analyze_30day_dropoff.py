"""Analyze user drop-off within first 30 days of enrollment."""

import pandas as pd
import matplotlib.pyplot as plt
import os
from config import DATA_DIR, OUTPUT_DIR, load_tables


def get_active_days_in_first_30(patients: pd.DataFrame, fact_patient_day: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate how many active days each patient achieved within their first 30 days of enrollment.

    Returns DataFrame with patient_id and active_days_in_first_30
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

    # Filter to first 30 days only (days 0-29)
    first_30_days = activity_merged[
        (activity_merged["day_since_enrollment"] >= 0)
        & (activity_merged["day_since_enrollment"] < 30)
    ]

    # Count active days per patient in first 30 days
    patient_active_days = (
        first_30_days.groupby("patient_id")
        .agg(active_days_in_first_30=("is_active_day", "sum"))
        .reset_index()
    )

    # Include all patients (even those with 0 active days)
    result = patients_with_dates[["patient_id"]].merge(
        patient_active_days, on="patient_id", how="left"
    ).fillna(0)

    result["active_days_in_first_30"] = result["active_days_in_first_30"].astype(int)

    return result


def get_retention_by_active_days(patient_active_days: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate cumulative retention: how many users reached at least X active days.

    Returns DataFrame with:
        - active_days_threshold: 1, 2, 3, ..., 30
        - users_reached: count of users who achieved at least that many active days
        - pct_reached: percentage of total users
        - drop_from_previous: how many users dropped compared to previous threshold
        - drop_pct: percentage drop from previous threshold
    """
    total_users = len(patient_active_days)

    results = []
    for threshold in range(0, 31):
        users_reached = (patient_active_days["active_days_in_first_30"] >= threshold).sum()
        pct_reached = users_reached / total_users * 100
        results.append({
            "active_days_threshold": threshold,
            "users_reached": users_reached,
            "pct_reached": pct_reached,
        })

    df = pd.DataFrame(results)

    # Calculate drop from previous threshold
    df["drop_from_previous"] = df["users_reached"].shift(1) - df["users_reached"]
    df["drop_pct"] = df["drop_from_previous"] / df["users_reached"].shift(1) * 100
    df = df.fillna(0)

    return df


def plot_30day_retention(retention_df: pd.DataFrame, show_plot: bool = True) -> str:
    """
    Create bar plot showing user retention by active days threshold.
    Shows where the biggest drop-off occurs.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "30day_retention_dropoff.png")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Top plot: Cumulative users who reached each threshold
    colors = ["#4C72B0" if x > 0 else "#2E4A7A" for x in retention_df["active_days_threshold"]]
    bars = ax1.bar(
        retention_df["active_days_threshold"],
        retention_df["users_reached"],
        color=colors,
        edgecolor="black",
        alpha=0.8,
    )

    # Add percentage labels on bars
    for i, (bar, pct) in enumerate(zip(bars, retention_df["pct_reached"])):
        if i % 2 == 0:  # Label every other bar to avoid clutter
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 5,
                f"{pct:.0f}%",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax1.set_xlabel("Minimum Active Days Achieved", fontsize=12)
    ax1.set_ylabel("Number of Users", fontsize=12)
    ax1.set_title("User Retention: How Many Users Reached X Active Days in First 30 Days", fontsize=14)
    ax1.set_xticks(range(0, 31, 2))
    ax1.grid(axis="y", alpha=0.3)

    # Bottom plot: Drop-off at each threshold (where users fall off)
    drop_df = retention_df[retention_df["active_days_threshold"] > 0].copy()

    # Color bars by drop magnitude - bigger drops are redder
    max_drop = drop_df["drop_from_previous"].max()
    colors = [plt.cm.Reds(0.3 + 0.7 * (d / max_drop)) if max_drop > 0 else "#D55E00"
              for d in drop_df["drop_from_previous"]]

    bars2 = ax2.bar(
        drop_df["active_days_threshold"],
        drop_df["drop_from_previous"],
        color=colors,
        edgecolor="black",
        alpha=0.8,
    )

    # Highlight the biggest drop
    max_drop_idx = drop_df["drop_from_previous"].idxmax()
    max_drop_threshold = drop_df.loc[max_drop_idx, "active_days_threshold"]
    max_drop_value = drop_df.loc[max_drop_idx, "drop_from_previous"]

    ax2.annotate(
        f"Biggest drop: {int(max_drop_value)} users\nat {int(max_drop_threshold)} active days",
        xy=(max_drop_threshold, max_drop_value),
        xytext=(max_drop_threshold + 5, max_drop_value * 0.8),
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color="black"),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
    )

    ax2.set_xlabel("Active Days Threshold", fontsize=12)
    ax2.set_ylabel("Users Dropped (from previous threshold)", fontsize=12)
    ax2.set_title("Drop-off Analysis: Where Users Stop Engaging", fontsize=14)
    ax2.set_xticks(range(1, 31))
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    if show_plot:
        plt.show()
    else:
        plt.close()

    return output_path


def main():
    # Load data
    tables = load_tables(DATA_DIR)
    patients = tables["patients"]
    fact_patient_day = tables["fact_patient_day"]

    # Convert dates
    fact_patient_day["date"] = pd.to_datetime(fact_patient_day["date"])
    patients["enrollment_date"] = pd.to_datetime(patients["enrollment_date"])

    # Calculate active days per patient in first 30 days
    patient_active_days = get_active_days_in_first_30(patients, fact_patient_day)

    print("=" * 60)
    print("30-DAY RETENTION ANALYSIS")
    print("=" * 60)

    print(f"\nTotal patients analyzed: {len(patient_active_days):,}")
    print(f"Mean active days in first 30: {patient_active_days['active_days_in_first_30'].mean():.1f}")
    print(f"Median active days in first 30: {patient_active_days['active_days_in_first_30'].median():.1f}")

    # Get retention curve
    retention_df = get_retention_by_active_days(patient_active_days)

    # Find biggest drops
    print("\n" + "-" * 40)
    print("TOP 5 BIGGEST DROP-OFF POINTS:")
    print("-" * 40)

    top_drops = retention_df[retention_df["active_days_threshold"] > 0].nlargest(5, "drop_from_previous")
    for _, row in top_drops.iterrows():
        print(f"  At {int(row['active_days_threshold'])} active days: "
              f"{int(row['drop_from_previous'])} users dropped "
              f"({row['drop_pct']:.1f}% of previous)")

    # Key milestones
    print("\n" + "-" * 40)
    print("KEY RETENTION MILESTONES:")
    print("-" * 40)

    milestones = [1, 5, 10, 16, 20, 25, 30]
    for m in milestones:
        row = retention_df[retention_df["active_days_threshold"] == m].iloc[0]
        print(f"  {m:2d}+ active days: {int(row['users_reached']):,} users ({row['pct_reached']:.1f}%)")

    # Create visualization
    output_path = plot_30day_retention(retention_df)
    print(f"\nVisualization saved to: {output_path}")


if __name__ == "__main__":
    main()
