from pathlib import Path
import pandas as pd
from visualize import plot_brightness_vs_risk

def test_plot_brightness_vs_risk(tmp_path: Path) -> None:
    weather_df = pd.DataFrame({
        "district": ["A", "A"],
        "date": ["2024-01-01", "2024-01-02"],
        "temp": [20, 21],
        "humidity": [50, 55],
        "wind_speed": [5, 6],
    })
    modis_df = pd.DataFrame({
        "acq_date": ["2024-01-01", "2024-01-02"],
        "brightness": [300, 350],
    })
    out_file = tmp_path / "plot.png"
    result = plot_brightness_vs_risk(weather_df, modis_df, out_file)
    assert Path(result) == out_file
    assert out_file.exists()
