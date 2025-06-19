import pandas as pd
import matplotlib.pyplot as plt
from typing import Union
from risk_analyzer import merge_with_modis, add_risk_column


def plot_brightness_vs_risk(
    weather_df: pd.DataFrame,
    modis_df: pd.DataFrame,
    output: Union[str, None] = "satellite_risk.png",
) -> str:
    """Merge data and plot brightness against computed risk score."""
    merged = merge_with_modis(weather_df, modis_df)
    merged = add_risk_column(merged)
    plt.figure(figsize=(6, 4))
    plt.scatter(merged["brightness"], merged["risk"], alpha=0.6)
    plt.xlabel("MODIS Brightness")
    plt.ylabel("Risk Score")
    plt.title("Brightness vs Risk Score")
    if output:
        plt.savefig(output, bbox_inches="tight")
    else:
        output = "satellite_risk.png"
        plt.savefig(output, bbox_inches="tight")
    plt.close()
    return output
