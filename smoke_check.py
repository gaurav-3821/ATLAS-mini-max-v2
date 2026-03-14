from __future__ import annotations

from pathlib import Path

from utils.data_loader import detect_axes, load_demo_dataset, period_mean, prepare_map_slice
from utils.stats_engine import compute_period_change


def main() -> None:
    dataset = load_demo_dataset()
    assert {"t2m", "precipitation", "sea_level_pressure", "wind_speed"} <= set(dataset.data_vars)

    data_array = dataset["t2m"]
    axes = detect_axes(data_array)
    assert all(axes.values())

    latest_slice = prepare_map_slice(data_array, axes, dataset["time"].values[-1], "Global", False)
    assert latest_slice.ndim == 2

    baseline = period_mean(data_array, axes, dataset["time"].values[0], dataset["time"].values[239], "Global")
    recent = period_mean(data_array, axes, dataset["time"].values[-240], dataset["time"].values[-1], "Global")
    delta = compute_period_change(baseline, recent)
    assert delta["delta"] > 0

    demo_file = Path("data") / "demo_temperature.nc"
    assert demo_file.exists()

    print("ATLAS smoke check passed.")


if __name__ == "__main__":
    main()
