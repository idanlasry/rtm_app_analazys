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
