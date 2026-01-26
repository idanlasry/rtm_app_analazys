import pandas as pd
import matplotlib.pyplot as plt
from helpers import load_tables

# Load cleaned data
tables = load_tables("data/cleaned data")

# Unpack tables
patients = tables["patients"]
fact_patient_day = tables["fact_patient_day"]
clinics = tables["clinics"]

# Convert date column to datetime
fact_patient_day["date"] = pd.to_datetime(fact_patient_day["date"])
patients["enrollment_date"] = pd.to_datetime(patients["enrollment_date"])

print("=" * 60)
print("OVERALL METRICS REPORT")
print("=" * 60)

# 1. Overall patients count
overall_patients_count = len(patients)
print(f"\n1. Overall Patients Count: {overall_patients_count:,}")

# 2. Patients billable in last month (December 2025)
# Patients who had 16+ active days in December 2025
december_activity = fact_patient_day[
    (fact_patient_day["date"] >= "2025-12-01")
    & (fact_patient_day["date"] < "2026-01-01")
]

# Count active days per patient in December
patient_active_days = (
    december_activity[december_activity["is_active_day"] == 1]
    .groupby("patient_id")
    .size()
)

# Patients with 16+ active days are billable
billable_patients = patient_active_days[patient_active_days >= 16]
billable_count = len(billable_patients)
total_patients_in_december = december_activity["patient_id"].nunique()

print("\n2. Patients Billable in Last Month (December 2025):")
print(f"   - Billable Patients: {billable_count:,} / {total_patients_in_december:,}")
if total_patients_in_december > 0:
    print(
        f"   - Billable Rate: {(billable_count / total_patients_in_december * 100):.2f}%"
    )

# 3. Active patients in last month (at least 1 active day)
active_patients_last_month = december_activity[december_activity["is_active_day"] == 1][
    "patient_id"
].nunique()

print("\n3. Active Patients in Last Month (December 2025):")
print(f"   - Active Patients: {active_patients_last_month:,}")
print(
    f"   - Active Rate: {(active_patients_last_month / overall_patients_count * 100):.2f}%"
)

# 4. Patients with fall risk score above 80 in last 3 days
# Assuming analysis date is 2026-01-08 (as per README)
analysis_date = pd.to_datetime("2026-01-08")
last_7_days = fact_patient_day[
    (fact_patient_day["date"] >= analysis_date - pd.Timedelta(days=7))
    & (fact_patient_day["date"] <= analysis_date)
]

high_fall_risk_patients = last_7_days[last_7_days["fall_risk_score"] >= 75][
    "patient_id"
].nunique()

print("\n4. Patients with Fall Risk Score >= 75 (Last 7 Days):")
print(f"   - High Fall Risk Patients: {high_fall_risk_patients:,}")
print(
    f"   - High Risk Rate: {(high_fall_risk_patients / overall_patients_count * 100):.2f}%"
)

print()
print("=" * 60)

# ============================================================================
# BI-WEEKLY KPIs
# ============================================================================

print("\n" + "=" * 60)
print("BI-WEEKLY KPI TRENDS (2-Week Periods)")
print("=" * 60)

# Create bi-weekly periods (2-week intervals)
# Use 2W-MON to start periods on Mondays with 2-week intervals
fact_patient_day["bi_week"] = fact_patient_day["date"].dt.to_period("2W-MON")

# 1. Change of active users per bi-week (active = 8+ active days in 2 weeks)
# Count active days per patient per bi-week
biweekly_active_days = (
    fact_patient_day[fact_patient_day["is_active_day"] == 1]
    .groupby(["patient_id", "bi_week"])
    .size()
    .reset_index(name="active_days")
)

# Filter patients with 8+ active days per bi-week (equivalent to 4+ per week)
active_users_per_biweek = (
    biweekly_active_days[biweekly_active_days["active_days"] >= 8]
    .groupby("bi_week")
    .size()
    .reset_index(name="active_users")
)

print("\n1. Active Users per Bi-Week (8+ active days):")
for _, row in active_users_per_biweek.iterrows():
    biweek_str = str(row["bi_week"])
    count = row["active_users"]
    print(f"   Period {biweek_str}: {count:,} users")

# Calculate period-over-period change
if len(active_users_per_biweek) > 1:
    active_users_per_biweek["change"] = active_users_per_biweek["active_users"].diff()
    active_users_per_biweek["pct_change"] = (
        active_users_per_biweek["active_users"].pct_change() * 100
    )
    print("\n   Period-over-Period Changes:")
    for idx, row in active_users_per_biweek.iterrows():
        if pd.notna(row["change"]):
            biweek_str = str(row["bi_week"])
            change = int(row["change"])
            pct_change = row["pct_change"]
            sign = "+" if change > 0 else ""
            print(f"   Period {biweek_str}: {sign}{change} ({sign}{pct_change:.1f}%)")

# 2. New patient enrollments per bi-week
patients["bi_week"] = patients["enrollment_date"].dt.to_period("2W-MON")
enrollments_per_biweek = (
    patients.groupby("bi_week").size().reset_index(name="new_patients")
)

print("\n2. New Patient Enrollments per Bi-Week:")
for _, row in enrollments_per_biweek.iterrows():
    biweek_str = str(row["bi_week"])
    count = row["new_patients"]
    print(f"   Period {biweek_str}: {count:,} patients")

# Calculate period-over-period change
if len(enrollments_per_biweek) > 1:
    enrollments_per_biweek["change"] = enrollments_per_biweek["new_patients"].diff()
    enrollments_per_biweek["pct_change"] = (
        enrollments_per_biweek["new_patients"].pct_change() * 100
    )
    print("\n   Period-over-Period Changes:")
    for idx, row in enrollments_per_biweek.iterrows():
        if pd.notna(row["change"]):
            biweek_str = str(row["bi_week"])
            change = int(row["change"])
            pct_change = row["pct_change"]
            sign = "+" if change > 0 else ""
            print(f"   Period {biweek_str}: {sign}{change} ({sign}{pct_change:.1f}%)")

print()
print("=" * 60)

# ============================================================================
# ACTIVE DAYS METRICS
# ============================================================================

print("\n" + "=" * 60)
print("ACTIVE DAYS METRICS (December 2025)")
print("=" * 60)

# 1. Total Active Days Rate
# Rate of active days out of all patient-days in December
total_patient_days = len(december_activity)
total_active_days = december_activity["is_active_day"].sum()
active_days_rate = (total_active_days / total_patient_days * 100) if total_patient_days > 0 else 0

print("\n1. Total Active Days Rate:")
print(f"   - Total Patient-Days: {total_patient_days:,}")
print(f"   - Active Days: {total_active_days:,}")
print(f"   - Active Days Rate: {active_days_rate:.2f}%")

# 2. Active Days Rate by Clinic
# Merge clinic info with activity data
december_with_clinic = december_activity.merge(
    clinics[["clinic_id", "clinic_name"]], on="clinic_id", how="left"
)

clinic_active_rate = (
    december_with_clinic.groupby(["clinic_id", "clinic_name"])
    .agg(
        total_days=("is_active_day", "count"),
        active_days=("is_active_day", "sum"),
    )
    .reset_index()
)
clinic_active_rate["active_rate"] = (
    clinic_active_rate["active_days"] / clinic_active_rate["total_days"] * 100
)
clinic_active_rate = clinic_active_rate.sort_values("active_rate", ascending=False)

print("\n2. Active Days Rate by Clinic:")
for _, row in clinic_active_rate.iterrows():
    print(
        f"   - {row['clinic_name']}: {row['active_rate']:.2f}% "
        f"({row['active_days']:,}/{row['total_days']:,} days)"
    )

# 3. Patient Active Days Distribution (Graph)
# Count active days per patient in December
patient_active_days_dec = (
    december_activity[december_activity["is_active_day"] == 1]
    .groupby("patient_id")
    .size()
    .reset_index(name="active_days")
)

# Include patients with 0 active days
all_patients_dec = december_activity[["patient_id"]].drop_duplicates()
patient_active_days_dec = all_patients_dec.merge(
    patient_active_days_dec, on="patient_id", how="left"
).fillna(0)

print("\n3. Patient Active Days Distribution:")
print(f"   - Mean Active Days: {patient_active_days_dec['active_days'].mean():.1f}")
print(f"   - Median Active Days: {patient_active_days_dec['active_days'].median():.1f}")
print(f"   - Min Active Days: {int(patient_active_days_dec['active_days'].min())}")
print(f"   - Max Active Days: {int(patient_active_days_dec['active_days'].max())}")

# Create histogram
plt.figure(figsize=(10, 6))
plt.hist(patient_active_days_dec["active_days"], bins=range(0, 33), edgecolor="black", alpha=0.7)
plt.axvline(x=16, color="red", linestyle="--", label="Billing Threshold (16 days)")
plt.xlabel("Active Days in December")
plt.ylabel("Number of Patients")
plt.title("Patient Active Days Distribution (December 2025)")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("output/patient_active_days_distribution.png", dpi=150)
plt.show()

print("\n   Graph saved to: output/patient_active_days_distribution.png")

print()
print("=" * 60)
