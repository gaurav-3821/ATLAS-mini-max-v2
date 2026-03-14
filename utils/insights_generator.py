from __future__ import annotations

import pandas as pd


def generate_explore_insight(
    variable_label: str,
    units: str,
    selected_time: pd.Timestamp,
    trend_label: str,
    slope_per_year: float,
    anomaly_count: int,
    summary: dict[str, float],
    nearest_lat: float,
    nearest_lon: float,
) -> str:
    return (
        f"{variable_label} on {selected_time.strftime('%B %Y')} has a mean of {summary['mean']:.2f} {units}. "
        f"The selected grid cell near ({nearest_lat:.1f}, {nearest_lon:.1f}) shows a {trend_label.lower()} trend "
        f"of {slope_per_year:+.3f} {units}/year, with {anomaly_count} unusual months highlighted in the local series."
    )


def generate_compare_insight(
    variable_label: str,
    units: str,
    label_a: str,
    label_b: str,
    delta: float,
) -> str:
    direction = "increased" if delta > 0 else "decreased" if delta < 0 else "stayed nearly flat"
    return (
        f"{variable_label} {direction} by {delta:+.2f} {units} between {label_a} and {label_b}. "
        "Use the difference map to see where the strongest change occurred."
    )


def generate_story_insight(title: str, caption: str) -> str:
    return f"{title}: {caption}"


def generate_globe_insight(
    variable_label: str,
    units: str,
    time_label: str,
    summary: dict[str, float],
    anomaly_mode: bool,
) -> str:
    mode_text = "anomaly view" if anomaly_mode else "absolute view"
    return (
        f"The globe is showing {variable_label} for {time_label} in {mode_text}. "
        f"Current mean is {summary['mean']:.2f} {units}, with a maximum of {summary['max']:.2f} "
        f"and minimum of {summary['min']:.2f}. Use the polar and equatorial color contrast to explain "
        "how climate patterns vary by latitude."
    )
