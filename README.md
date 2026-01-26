# Steps App Analysis

A data analysis project for RTM (Remote Therapeutic Monitoring) engagement tracking and clinic operations analysis.

## Project Overview

This project analyzes synthetic data from a OneStep-like system that captures passive patient engagement data and monitors adherence to RTM requirements. The analysis focuses on patient engagement metrics, clinic operations, and risk alerts.

## Dataset

The project includes synthetic data generated on 2026-01-08 with the following structure:

### Data Files

| File | Description |
|------|-------------|
| `clinics.csv` | Clinic information (6 clinics across US states) |
| `providers.csv` | Healthcare provider details |
| `patients.csv` | Patient demographics and enrollment data |
| `fact_patient_day.csv` | Daily patient activity data with walk scores and fall risk metrics |
| `assessment_assignments.csv` | Assessment assignment tracking (assigned vs completed) |
| `alerts.csv` | Risk alerts including fall risk spikes and engagement warnings |
| `rtm_monthly.csv` | Monthly RTM compliance metrics and active day counts |

### Clinics

| Clinic ID | Name | Region |
|-----------|------|--------|
| C001 | Sunrise Physical Therapy | Florida |
| C002 | Evergreen Rehabilitation Center | Washington |
| C003 | Summit Health Partners | Colorado |
| C004 | Coastal Wellness Clinic | California |
| C005 | Maple Grove Medical | Minnesota |
| C006 | Horizon Recovery Institute | Arizona |

### Key Metrics

- **Active Day**: ≥10 minutes of background data OR ≥300 steps
- **16/30 Compliance**: Active days in first 30 days ≥ 16 (Medicare RTM billing requirement)
- **Active User (Bi-Weekly)**: 8+ active days in a 2-week period
- **Fall Risk Threshold**: Score ≥ 75 in last 7 days
- **Walk Score & Fall Risk**: Simulated metrics tracking patient mobility trends

## Installation

### Requirements

- Python 3.7+
- pandas
- matplotlib
- numpy

### Setup

1. Clone or download the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run the full metrics report:

```bash
python run_metrics.py
```

This generates:
- Overall metrics (patient count, billable, active, fall risk)
- Bi-weekly KPI trends (active users, enrollments)
- Active days analysis (rates, by clinic, distribution graph)

### Data preparation (run once after getting new data):

```bash
python "exploration and cleaning.py"
```

### Import metrics in your own scripts:

```python
from metrics import get_billable_patients, get_active_rate_by_clinic
from visualizations import plot_active_days_distribution

# Get billable patients for December
billable = get_billable_patients(fact_patient_day)
print(f"Billable rate: {billable['billable_rate']:.2f}%")

# Plot distribution
plot_active_days_distribution(distribution_df)
```

## Project Structure

```
.
├── config.py                    # Constants, thresholds, and load_tables()
├── run_metrics.py               # Main runner - executes all metrics
│
├── metrics/                     # Metrics module
│   ├── __init__.py
│   ├── overall.py              # Patient count, billable, active, fall risk
│   ├── kpis.py                 # Bi-weekly trends (active users, enrollments)
│   └── active_days.py          # Active days rates, by clinic, distribution
│
├── visualizations/              # Charts module
│   ├── __init__.py
│   └── distributions.py        # Active days histogram
│
├── exploration and cleaning.py  # Data preparation and cleaning
│
├── data/
│   ├── raw/                    # Original data files
│   ├── cleaned data/           # Cleaned and type-converted data
│   └── processed/              # Further processed datasets
│
├── output/                      # Analysis outputs and graphs
└── archive/                     # Old/deprecated files
```

## Key Features

- **Modular Architecture**: Reusable metric functions for notebooks and dashboards
- **Engagement Tracking**: Monitor patient activity and compliance with RTM requirements
- **Risk Identification**: Detect patients at risk of dropout or health decline
- **Compliance Monitoring**: Track 16/30 RTM billing compliance metrics
- **Clinic Segmentation**: Compare performance across clinics
- **Trend Analysis**: Bi-weekly KPIs with period-over-period changes
- **Visualizations**: Distribution graphs with billing threshold markers

## Data Notes

- All dates are relative to 2026-01-08 (analysis as-of date)
- Data range: November 15, 2025 - January 8, 2026
- Full month available: December 2025
- Walk Score and fall risk scores are simulated for development/testing purposes
- Data includes realistic patterns for engagement, adherence, and risk indicators

## License

Synthetic dataset for analysis and learning purposes.
