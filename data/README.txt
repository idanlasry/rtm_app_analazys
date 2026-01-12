Synthetic OneStep-like dataset (engagement/adherence + clinic ops)
Generated: 2026-01-08T12:56:10.160484Z
As-of date (for "no data in 3 days" alerts): 2026-01-08

Why these fields exist:
- OneStep markets passive data capture that can meet a "16-day requirement" for RTM (16 days of data in 30 days) and provides gait metrics like Walk Score / fall risk insights.
  Sources: OneStep RTM page and product pages.

Files:
1) clinics.csv
2) providers.csv
3) patients.csv
4) fact_patient_day.csv   (daily background data + active day flag + walk_score/fall_risk_score)
5) assessment_assignments.csv (assigned vs completed)
6) alerts.csv             (fall risk spikes, decline flags, and "no data in 3 days")
7) rtm_monthly.csv        (active days in first 30 days; 16/30 compliance flag)

Key KPI definitions implemented:
- is_active_day = (background_data_minutes >= 10) OR (steps_count >= 300)
- 7 active days KPI: count distinct active days in first 14 days from first_data_date
- 16/30 compliant: active_days_first_30 >= 16
- Patients at risk of dropout: last active day is >= 3 days before as_of_date (alert_type=no_data_3_days)

Notes:
- Walk Score and fall_risk_score are simulated numeric scores to support "improving vs stagnating" distributions and alerting.
