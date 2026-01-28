"""Configuration constants and utilities for the RTM metrics analysis."""

import pandas as pd
from pathlib import Path


def load_tables(data_dir: str) -> dict:
    """Load all CSV files from a directory into a dictionary."""
    tables = {}
    for p in Path(data_dir).iterdir():
        if p.is_file() and p.suffix == ".csv":
            tables[p.stem] = pd.read_csv(p)
    return tables

# Analysis reference date
ANALYSIS_DATE = pd.to_datetime("2026-01-08")

# Data directories
DATA_DIR = "data/cleaned data"
OUTPUT_DIR = "output"

# Billing and compliance thresholds
BILLING_THRESHOLD = 16  # Days required for 16/30 compliance
ACTIVE_WEEK_THRESHOLD = 4  # Active days per week
ACTIVE_BIWEEK_THRESHOLD = 8  # Active days per bi-week

# Risk thresholds
FALL_RISK_THRESHOLD = 70
FALL_RISK_LOOKBACK_DAYS = 7

# Date ranges - default to last 30 days
DATE_END = (pd.Timestamp.today() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")  # Yesterday
DATE_START = (pd.Timestamp.today() - pd.Timedelta(days=31)).strftime("%Y-%m-%d")  # 30 days before end
