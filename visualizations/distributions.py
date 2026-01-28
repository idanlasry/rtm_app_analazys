"""Distribution visualizations for RTM analysis."""

import os
import pandas as pd
import matplotlib.pyplot as plt
from config import BILLING_THRESHOLD, OUTPUT_DIR


def plot_active_days_distribution(
    distribution_df: pd.DataFrame,
    output_filename: str = "patient_active_days_distribution.png",
    title: str = "Patient Active Days Distribution (December 2025)",
    show_plot: bool = True,
) -> str:
    """
    Create histogram of patient active days distribution.

    Args:
        distribution_df: DataFrame with 'active_days' column
        output_filename: filename for saved plot
        title: plot title
        show_plot: whether to display the plot

    Returns:
        Path to saved plot file
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Create histogram
    plt.figure(figsize=(10, 6))
    plt.hist(
        distribution_df["active_days"],
        bins=range(0, 33),
        edgecolor="black",
        alpha=0.7,
        color="#4C72B0",
    )

    # Add billing threshold line
    plt.axvline(
        x=BILLING_THRESHOLD,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Billing Threshold ({BILLING_THRESHOLD} days)",
    )

    # Labels and styling
    plt.xlabel("Active Days", fontsize=12)
    plt.ylabel("Number of Patients", fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    # Save plot
    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    if show_plot:
        plt.show()
    else:
        plt.close()

    return output_path


def plot_active_rate_by_day_since_enrollment(
    distribution_df: pd.DataFrame,
    output_filename: str = "active_rate_by_day_since_enrollment.png",
    title: str = "Patient Active Rate by Day Since Enrollment",
    show_plot: bool = True,
) -> str:
    """
    Create line chart of active rate by day since enrollment.

    Shows the percentage of patients who are active on each day (0-30)
    after their enrollment date (day 0 = enrollment day).

    Args:
        distribution_df: DataFrame with 'day_since_enrollment' and 'active_rate' columns
        output_filename: filename for saved plot
        title: plot title
        show_plot: whether to display the plot

    Returns:
        Path to saved plot file
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot line chart
    ax.plot(
        distribution_df["day_since_enrollment"],
        distribution_df["active_rate"],
        marker="o",
        markersize=4,
        linewidth=2,
        color="#4C72B0",
    )

    # Fill area under the curve
    ax.fill_between(
        distribution_df["day_since_enrollment"],
        distribution_df["active_rate"],
        alpha=0.3,
        color="#4C72B0",
    )

    # Add mean line
    mean_rate = distribution_df["active_rate"].mean()
    ax.axhline(
        y=mean_rate,
        color="red",
        linestyle="--",
        linewidth=1.5,
        label=f"Mean Active Rate ({mean_rate:.1f}%)",
    )

    # Labels and styling
    ax.set_xlabel("Days Since Enrollment", fontsize=12)
    ax.set_ylabel("Active Rate (%)", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.set_xlim(0, distribution_df["day_since_enrollment"].max())
    ax.set_ylim(0, min(100, distribution_df["active_rate"].max() * 1.1))
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(alpha=0.3)

    # Add x-axis ticks for each day
    ax.set_xticks(range(0, int(distribution_df["day_since_enrollment"].max()) + 1, 5))

    plt.tight_layout()

    # Save plot
    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    if show_plot:
        plt.show()
    else:
        plt.close()

    return output_path
