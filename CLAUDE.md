# CLAUDE.md — RTM App Analysis

This file provides guidance for AI assistants working in this repository.

## Project Overview

This is a **Python data analysis project** for Remote Therapeutic Monitoring (RTM) engagement tracking. It analyzes synthetic patient data from a OneStep-like passive monitoring system to produce compliance metrics, engagement trends, and risk alerts aligned with Medicare RTM billing requirements.

**Analysis reference date:** `2026-01-08`
**Data range:** November 15, 2025 – January 8, 2026 (full month: December 2025)

---

## Repository Structure

```
.
├── config.py                    # Constants, thresholds, load_tables() utility
├── run_metrics.py               # Main entry point — runs all metrics and reports
├── data_preparation.py          # One-time data cleaning/type conversion script
├── analyze_30day_dropoff.py     # Standalone 30-day dropout analysis
│
├── metrics/                     # Reusable metric functions
│   ├── __init__.py              # Public API exports
│   ├── overall.py               # Patient count, billable, active, fall risk
│   ├── kpis.py                  # Bi-weekly active users, enrollments, period changes
│   ├── active_days.py           # Active rates, by clinic, distribution, engagement curve
│   └── onboarding_funnel.py     # Enrollment → install → first data → compliant funnel
│
├── visualizations/              # Matplotlib chart generators
│   ├── __init__.py              # Public API exports
│   ├── distributions.py         # Active days histogram, engagement-by-day line chart
│   └── onboarding_funnel.py     # Funnel line chart
│
├── docs/
│   └── kpi_dictionary.md        # Canonical KPI definitions and edge cases
│
├── data/
│   ├── raw/                     # Original CSV files (gitignored)
│   ├── cleaned data/            # Type-converted, clinic-mapped CSVs (gitignored)
│   └── processed/               # Further processed datasets (gitignored)
│
├── output/                      # Generated charts and reports (gitignored)
├── archive/                     # Deprecated scripts — do not modify
└── requirements.txt
```

---

## Data Model

Seven CSV files form the data model (loaded from `data/cleaned data/`):

| Table | Key Columns | Description |
|-------|-------------|-------------|
| `clinics` | `clinic_id`, `clinic_name`, `region` | 6 clinics across US states |
| `providers` | `provider_id`, `clinic_id` | Healthcare providers |
| `patients` | `patient_id`, `clinic_id`, `enrollment_date`, `install_date`, `first_data_date` | Demographics and onboarding milestones |
| `fact_patient_day` | `patient_id`, `date`, `is_active`, `background_data_minutes`, `steps_count`, `fall_risk_score` | Daily activity grain — one row per patient per day |
| `assessment_assignments` | `patient_id`, `status`, `due_date` | Assessment tracking |
| `alerts` | `patient_id`, `alert_type`, `created_ts`, `ack_ts` | Risk alerts |
| `rtm_monthly` | `patient_id`, `month`, `active_days` | Monthly RTM compliance rollups |

**Primary grain:** `fact_patient_day` at `(patient_id, date)`.

---

## Configuration (`config.py`)

All shared constants live in `config.py`. **Do not hardcode thresholds inline.**

```python
ANALYSIS_DATE = pd.to_datetime("2026-01-08")   # As-of date for snapshots
DATA_DIR      = "data/cleaned data"             # Input for load_tables()
OUTPUT_DIR    = "output"                        # Chart save destination

BILLING_THRESHOLD        = 16   # Active days required for Medicare RTM billing
ACTIVE_WEEK_THRESHOLD    = 4    # Active days to qualify as active in a week
ACTIVE_BIWEEK_THRESHOLD  = 8    # Active days to qualify as active in a bi-week
FALL_RISK_THRESHOLD      = 70   # Fall risk score triggering high-risk flag
FALL_RISK_LOOKBACK_DAYS  = 7    # Window for fall risk evaluation

DATE_END   = yesterday (dynamic)
DATE_START = 30 days before DATE_END (dynamic)
```

`load_tables(data_dir)` reads all CSVs in a directory into a `dict[stem → DataFrame]`.

---

## KPI Definitions

Canonical definitions are in `docs/kpi_dictionary.md`. Summary:

| KPI | Definition | Formula |
|-----|-----------|---------|
| **Active Day** | Day with meaningful passive data | `background_data_minutes >= 10` OR `steps_count >= 300` |
| **16/30 Compliance** | ≥16 active days in first 30 days after first data | `active_days_first_30 >= 16`; requires `first_data_date + 29 <= as_of_date` |
| **Active User (bi-weekly)** | 8+ active days in a 2-week period | Rolling sum per bi-week window |
| **Fall Risk High** | Score ≥70 in last 7 days | Max `fall_risk_score` in lookback window |
| **Drop-off Risk** | No active day for ≥3 consecutive days | `as_of_date - last_active_date >= 3` |
| **Assessment Completion Rate** | `completed / assigned` in window | Exclude late completions unless otherwise specified |
| **Alerts Ack Rate** | `acked / total`; median time-to-ack | Missing `ack_ts` → not acked; exclude from time-to-ack |

**Edge cases (always enforce):**
- Missing `steps_count` or `background_data_minutes` → treat as 0.
- Patient with `< N` days since `first_data_date` → compute rolling metric, mark as ineligible for goal thresholds.
- `first_data_date` is null → patient belongs to an earlier funnel stage, not eligible for 16/30.

---

## Public API

### `metrics` module

```python
from metrics import (
    # overall.py
    get_patient_count(patients) -> int
    get_billable_patients(fact_patient_day, start, end) -> dict
    get_active_patients(fact_patient_day) -> dict
    get_high_fall_risk_patients(fact_patient_day) -> dict

    # kpis.py
    get_active_users_biweekly(fact_patient_day) -> DataFrame
    get_enrollments_biweekly(patients) -> DataFrame
    calculate_period_changes(df, value_col) -> DataFrame

    # active_days.py
    get_total_active_rate(fact_patient_day) -> dict
    get_active_rate_by_clinic(fact_patient_day, clinics) -> DataFrame
    get_patient_active_distribution(fact_patient_day) -> dict
    get_active_rate_by_day_since_enrollment(patients, fact_patient_day) -> dict

    # onboarding_funnel.py
    get_patient_funnel(patients, fact_patient_day) -> dict
    print_funnel(funnel_result) -> None
)
```

### `visualizations` module

```python
from visualizations import (
    plot_active_days_distribution(distribution_df) -> str          # returns output path
    plot_active_rate_by_day_since_enrollment(distribution_df) -> str
    plot_patient_funnel(funnel_df) -> str
)
```

All chart functions save to `output/` and return the file path string.

---

## Development Workflows

### Running the full report

```bash
pip install -r requirements.txt
python run_metrics.py
```

Outputs to console:
1. Overall Metrics (patient count, billable, active, fall risk)
2. Bi-Weekly KPI Trends (active users, enrollments with period-over-period changes)
3. Active Days Metrics (total rate, by clinic, distribution)
4. Patient Funnel (Enrolled → Installed → First Data → 16/30 Compliant)

Charts saved to `output/`.

### Preparing new data

Run once after receiving new raw CSVs:

```bash
python data_preparation.py
```

This cleans types, maps clinic names/regions, validates quality, and writes to `data/cleaned data/`.

### 30-day dropout analysis

```bash
python analyze_30day_dropoff.py
```

Standalone — builds retention curves and identifies dropout points for the first 30 days post-enrollment.

### Using metrics in a notebook or script

```python
import pandas as pd
from config import DATA_DIR, load_tables
from metrics import get_billable_patients, get_active_rate_by_clinic

tables = load_tables(DATA_DIR)
fact_patient_day = tables["fact_patient_day"]
fact_patient_day["date"] = pd.to_datetime(fact_patient_day["date"])

billable = get_billable_patients(fact_patient_day, "2025-12-01", "2026-01-01")
print(f"Billable rate: {billable['billable_rate']:.2f}%")
```

---

## Conventions

### Code style

- Python 3.7+ compatible.
- Use `pandas` DataFrames as the primary data structure.
- All metric functions return **dicts** (for scalar outputs) or **DataFrames** (for tabular outputs). Do not mix return types within a function.
- Visualization functions must save to `OUTPUT_DIR` and **return the output path** as a string.
- Always convert date columns to `datetime64` before filtering or joining. Do this in the caller (`run_metrics.py`), not inside metric functions.

### Thresholds

- Import thresholds from `config.py`. Never hardcode `16`, `8`, `70`, etc. inline.

### Date handling

- Use `ANALYSIS_DATE` from `config.py` for snapshot-based calculations.
- Use `DATE_START` / `DATE_END` (dynamic 30-day window) for rolling period reports.
- Date ranges are half-open: `[start, end)` — `end` is exclusive.

### Adding a new metric

1. Implement the function in the appropriate `metrics/` submodule.
2. Export it from `metrics/__init__.py`.
3. Call it in `run_metrics.py` under the relevant section.
4. Add any new KPI definitions to `docs/kpi_dictionary.md`.

### Adding a new visualization

1. Implement in `visualizations/distributions.py` or a new file.
2. Export from `visualizations/__init__.py`.
3. Save output to `OUTPUT_DIR` and return the path.

---

## Clinics Reference

| ID | Name | Region |
|----|------|--------|
| C001 | Sunrise Physical Therapy | Florida |
| C002 | Evergreen Rehabilitation Center | Washington |
| C003 | Summit Health Partners | Colorado |
| C004 | Coastal Wellness Clinic | California |
| C005 | Maple Grove Medical | Minnesota |
| C006 | Horizon Recovery Institute | Arizona |

---

## What to Avoid

- **Do not modify files in `archive/`** — they are deprecated and retained for reference only.
- **Do not commit data files** (`data/`, `output/`) — they are gitignored and may contain sensitive synthetic data.
- **Do not add external API calls** without updating `requirements.txt` and documenting the integration.
- **Do not hardcode date strings** as literals where `ANALYSIS_DATE`, `DATE_START`, or `DATE_END` should be used.
- **Do not add a database** without discussion — the project intentionally uses CSV-based storage.

---

## No Test Suite

There is currently no automated test framework. Validation is done through:
- Visual inspection of chart outputs.
- Console metric sanity checks in `run_metrics.py`.
- Data quality checks in `data_preparation.py`.

When adding new metric functions, include print-based validation in `run_metrics.py` or a standalone script.
