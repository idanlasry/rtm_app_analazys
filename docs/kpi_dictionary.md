KPI dictionary


KPI 1: Active day

Definition: A calendar day where patient generated meaningful passive data.

Formula: is_active_day = (background_data_minutes >= 10) OR (steps_count >= 300)

Grain: patient_id, date

Edge cases: missing minutes/steps → treat as 0

KPI 2: Active days (7/14/30)

Definition: Count of active days in the last N days.

Formula: rolling sum of is_active_day over N-day window

Anchor date: analysis date (or “as-of” date for snapshot)

Edge cases: patient has < N days since first_data_date → still compute, but mark as not eligible for “goal thresholds”

KPI 3: 16/30 compliance

Definition: Patient has ≥16 active days in their first 30 days after first data.

Eligibility: first_data_date is not null AND as_of_date >= first_data_date + 29 days

Formula: active_days_first_30 >= 16

Edge cases: first_data_date missing → not eligible, belongs to funnel earlier stage

KPI 4: Drop-off risk

Definition: Patient has no active day for ≥3 consecutive days.

Formula: days_since_last_active = as_of_date - last_active_date; at risk if >= 3

Edge cases: never active → treat as “pre-first-data” funnel issue (not “drop-off”)

KPI 5: Assessment completion rate

Definition: Completed assessments / assigned assessments within window.

Formula: count(status='completed') / count(assigned) (by week/clinic/type)

Edge cases: late completion after due_date — decide if counted (yes/no)

KPI 6: Alerts acknowledgement

Ack rate: acked / total

Time-to-ack: median(ack_ts - created_ts) in hours

Edge cases: missing ack_ts → not acked; exclude from time-to-ack calc