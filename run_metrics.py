"""Main runner for RTM metrics analysis."""

import pandas as pd
from config import DATA_DIR, load_tables
from metrics import (
    get_patient_count,
    get_billable_patients,
    get_active_patients,
    get_high_fall_risk_patients,
    get_active_users_biweekly,
    get_enrollments_biweekly,
    calculate_period_changes,
    get_total_active_rate,
    get_active_rate_by_clinic,
    get_patient_active_distribution,
    get_patient_funnel,
    print_funnel,
)
from visualizations import plot_active_days_distribution, plot_patient_funnel


def main():
    # Load cleaned data
    tables = load_tables(DATA_DIR)

    # Unpack tables
    patients = tables["patients"]
    fact_patient_day = tables["fact_patient_day"]
    clinics = tables["clinics"]

    # Convert date columns to datetime
    fact_patient_day["date"] = pd.to_datetime(fact_patient_day["date"])
    patients["enrollment_date"] = pd.to_datetime(patients["enrollment_date"])
    patients["install_date"] = pd.to_datetime(patients["install_date"])
    patients["first_data_date"] = pd.to_datetime(patients["first_data_date"])

    # =========================================================================
    # OVERALL METRICS REPORT
    # =========================================================================
    print("\n" + "=" * 60)
    print("OVERALL METRICS REPORT")
    print("=" * 60)

    # 1. Overall patients count
    patient_count = get_patient_count(patients)
    print(f"\n1. Overall Patients Count: {patient_count:,}")

    # 2. Billable patients
    billable = get_billable_patients(fact_patient_day)
    print("\n2. Patients Billable in Last Month (December 2025):")
    print(
        f"   - Billable Patients: {billable['billable_count']:,} / {billable['total_patients']:,}"
    )
    print(f"   - Billable Rate: {billable['billable_rate']:.2f}%")

    # 3. Active patients
    active = get_active_patients(fact_patient_day)
    print("\n3. Active Patients in Last Month (December 2025):")
    print(f"   - Active Patients: {active['active_count']:,}")
    print(f"   - Active Rate: {(active['active_count'] / patient_count * 100):.2f}%")

    # 4. High fall risk patients
    fall_risk = get_high_fall_risk_patients(fact_patient_day)
    print("\n4. Patients with Fall Risk Score >= 75 (Last 7 Days):")
    print(f"   - High Fall Risk Patients: {fall_risk['high_risk_count']:,}")
    print(
        f"   - High Risk Rate: {(fall_risk['high_risk_count'] / patient_count * 100):.2f}%"
    )

    # =========================================================================
    # BI-WEEKLY KPI TRENDS
    # =========================================================================
    print("\n" + "=" * 60)
    print("BI-WEEKLY KPI TRENDS (2-Week Periods)")
    print("=" * 60)

    # 1. Active users per bi-week
    active_users_biweekly = get_active_users_biweekly(fact_patient_day)
    print("\n1. Active Users per Bi-Week (8+ active days):")
    for _, row in active_users_biweekly.iterrows():
        print(f"   Period {row['bi_week']}: {row['active_users']:,} users")

    # Period changes
    if len(active_users_biweekly) > 1:
        active_users_changes = calculate_period_changes(
            active_users_biweekly, "active_users"
        )
        print("\n   Period-over-Period Changes:")
        for _, row in active_users_changes.iterrows():
            if pd.notna(row["change"]):
                change = int(row["change"])
                sign = "+" if change > 0 else ""
                print(
                    f"   Period {row['bi_week']}: {sign}{change} ({sign}{row['pct_change']:.1f}%)"
                )

    # 2. New patient enrollments
    enrollments_biweekly = get_enrollments_biweekly(patients)
    print("\n2. New Patient Enrollments per Bi-Week:")
    for _, row in enrollments_biweekly.iterrows():
        print(f"   Period {row['bi_week']}: {row['new_patients']:,} patients")

    # Period changes
    if len(enrollments_biweekly) > 1:
        enrollments_changes = calculate_period_changes(
            enrollments_biweekly, "new_patients"
        )
        print("\n   Period-over-Period Changes:")
        for _, row in enrollments_changes.iterrows():
            if pd.notna(row["change"]):
                change = int(row["change"])
                sign = "+" if change > 0 else ""
                print(
                    f"   Period {row['bi_week']}: {sign}{change} ({sign}{row['pct_change']:.1f}%)"
                )

    # =========================================================================
    # ACTIVE DAYS METRICS
    # =========================================================================
    print("\n" + "=" * 60)
    print("ACTIVE DAYS METRICS (December 2025)")
    print("=" * 60)

    # 1. Total active days rate
    active_rate = get_total_active_rate(fact_patient_day)
    print("\n1. Total Active Days Rate:")
    print(f"   - Total Patient-Days: {active_rate['total_patient_days']:,}")
    print(f"   - Active Days: {active_rate['total_active_days']:,}")
    print(f"   - Active Days Rate: {active_rate['active_days_rate']:.2f}%")

    # 2. Active days rate by clinic
    clinic_rates = get_active_rate_by_clinic(fact_patient_day, clinics)
    print("\n2. Active Days Rate by Clinic:")
    for _, row in clinic_rates.iterrows():
        print(
            f"   - {row['clinic_name']}: {row['active_rate']:.2f}% "
            f"({int(row['active_days']):,}/{int(row['total_days']):,} days)"
        )

    # 3. Patient active days distribution
    distribution = get_patient_active_distribution(fact_patient_day)
    print("\n3. Patient Active Days Distribution:")
    print(f"   - Mean Active Days: {distribution['mean']:.1f}")
    print(f"   - Median Active Days: {distribution['median']:.1f}")
    print(f"   - Min Active Days: {distribution['min']}")
    print(f"   - Max Active Days: {distribution['max']}")

    # Create distribution plot
    output_path = plot_active_days_distribution(distribution["distribution_df"])
    print(f"\n   Graph saved to: {output_path}")

    # =========================================================================
    # PATIENT FUNNEL
    # =========================================================================
    print("\n" + "=" * 60)
    print("PATIENT FUNNEL (Enrollment to Compliance)")
    print("=" * 60)

    funnel_result = get_patient_funnel(patients, fact_patient_day)
    print_funnel(funnel_result)

    # Create funnel visualization
    funnel_path = plot_patient_funnel(funnel_result["funnel_df"])
    print(f"\n   Graph saved to: {funnel_path}")

    print("\n" + "=" * 60)
    print("REPORT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
