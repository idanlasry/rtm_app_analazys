# Step App Analysis

A data analysis project for OneStep RTM (Remote Therapeutic Monitoring) engagement tracking and clinic operations analysis.

## Project Overview

This project analyzes synthetic data from a OneStep-like system that captures passive patient engagement data and monitors adherence to RTM requirements. The analysis focuses on patient engagement metrics, clinic operations, and risk alerts.

## Dataset

The project includes synthetic data generated on 2026-01-08 with the following structure:

### Data Files

| File | Description |
|------|-------------|
| `clinics.csv` | Clinic information and metadata |
| `providers.csv` | Healthcare provider details |
| `patients.csv` | Patient demographics and enrollment data |
| `fact_patient_day.csv` | Daily patient activity data with walk scores and fall risk metrics |
| `assessment_assignments.csv` | Assessment assignment tracking (assigned vs completed) |
| `alerts.csv` | Risk alerts including fall risk spikes and engagement warnings |
| `rtm_monthly.csv` | Monthly RTM compliance metrics and active day counts |

### Key Metrics

- **Active Day**: ≥10 minutes of background data OR ≥300 steps
- **7-Day Active KPI**: Distinct active days in first 14 days from enrollment
- **16/30 Compliance**: Active days in first 30 days ≥ 16
- **Engagement Risk**: Last active day ≥3 days before analysis date
- **Walk Score & Fall Risk**: Simulated metrics tracking patient mobility trends

## Installation

### Requirements

- Python 3.7+
- pandas
- matplotlib
- requests
- numpy

### Setup

1. Clone or download the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main analysis script:

```bash
python hello.py
```

The script performs:
- Data loading and exploration
- Patient engagement analysis
- Weather data retrieval (Paris region as example)
- Visualization of key metrics

## Project Structure

```
.
├── hello.py              # Main analysis script
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── data/                # Input data directory
│   ├── clinics.csv
│   ├── providers.csv
│   ├── patients.csv
│   ├── fact_patient_day.csv
│   ├── assessment_assignments.csv
│   ├── alerts.csv
│   ├── rtm_monthly.csv
│   └── README.txt       # Data documentation
└── output/              # Analysis outputs
```

## Key Features

- **Engagement Tracking**: Monitor patient activity and compliance with RTM requirements
- **Risk Identification**: Detect patients at risk of dropout or health decline
- **Compliance Monitoring**: Track 16/30 RTM compliance metrics
- **Multi-dimensional Analysis**: Combine gait metrics, activity data, and clinical assessments

## Data Notes

- All dates are relative to 2026-01-08 (analysis as-of date)
- Walk Score and fall risk scores are simulated for development/testing purposes
- Data includes realistic patterns for engagement, adherence, and risk indicators

## License

Synthetic dataset for analysis and learning purposes.
