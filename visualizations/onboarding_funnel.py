"""Funnel visualizations for RTM analysis."""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from config import OUTPUT_DIR


def plot_patient_funnel(
    funnel_df: pd.DataFrame,
    output_filename: str = "patient_funnel.png",
    title: str = "Patient Funnel: Enrollment to Compliance",
    show_plot: bool = True,
) -> str:
    """
    Create a line chart visualization of the patient funnel.

    Args:
        funnel_df: DataFrame with 'stage', 'count', 'rate_from_enrolled' columns
        output_filename: filename for saved plot
        title: plot title
        show_plot: whether to display the plot

    Returns:
        Path to saved plot file
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Extract data
    stages = funnel_df["stage"].tolist()
    counts = funnel_df["count"].tolist()
    rates = funnel_df["rate_from_enrolled"].tolist()

    x_pos = range(len(stages))

    # Create line chart with markers
    ax.plot(
        x_pos,
        counts,
        marker="o",
        markersize=12,
        linewidth=3,
        color="#3498db",
        markerfacecolor="#2980b9",
        markeredgecolor="white",
        markeredgewidth=2,
    )

    # Fill area under the line
    ax.fill_between(x_pos, counts, alpha=0.2, color="#3498db")

    # Add labels at each point
    max_count = max(counts)
    for i, (x, count, rate) in enumerate(zip(x_pos, counts, rates)):
        # Count label above marker
        ax.annotate(
            f"{count:,}",
            xy=(x, count),
            xytext=(0, 15),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color="#2c3e50",
        )
        # Percentage label below marker
        ax.annotate(
            f"{rate:.1f}%",
            xy=(x, count),
            xytext=(0, -20),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=10,
            color="#7f8c8d",
        )

    # Styling
    ax.set_xticks(x_pos)
    ax.set_xticklabels(stages, fontsize=10, rotation=15, ha="right")
    ax.set_ylabel("Number of Patients", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.set_ylim(0, max_count * 1.25)

    # Remove spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add grid
    ax.yaxis.grid(True, linestyle="--", alpha=0.3)

    # Add conversion annotation
    initial = counts[0]
    final = counts[-1]
    conversion = final / initial * 100 if initial > 0 else 0
    ax.annotate(
        f"Overall Conversion: {conversion:.1f}%",
        xy=(0.98, 0.98),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=11,
        style="italic",
        color="#666",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#ddd"),
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    if show_plot:
        plt.show()
    else:
        plt.close()

    return output_path
