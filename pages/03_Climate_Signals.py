from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.chart_factory import (
    create_anomaly_bar_figure,
    create_heatmap,
    create_ranked_bar_figure,
    create_seasonality_bar_figure,
    create_timeline_figure,
)
from utils.data_loader import (
    REGION_BOUNDS,
    annual_mean_series,
    detect_axes,
    get_active_dataset,
    period_mean,
    spatial_mean_series,
    to_display_array,
)
from utils.style import render_app_shell, render_info_banner, render_metric_card, render_page_hero, render_section_intro


st.set_page_config(page_title="ATLAS | Climate Signals", page_icon=":material/query_stats:", layout="wide")


def _to_frame(series, time_name: str) -> pd.DataFrame:
    return series.to_dataframe(name="value").reset_index().rename(columns={time_name: "time"})


def main() -> None:
    render_app_shell(
        "Climate Signals",
        "Long-range climate indicators, anomaly tracking, and before-versus-after comparisons.",
        search_placeholder="Search warming, rainfall, wind, pressure, or region",
    )
    render_page_hero(
        "Long-range analytics",
        "Climate Signals",
        "Read how the climate field is changing through anomalies, annual signatures, and comparative change maps.",
        subtitle="Historical trends and signal comparisons",
    )

    dataset, label = get_active_dataset()
    region_name = st.sidebar.selectbox("Region", list(REGION_BOUNDS.keys()), index=0)
    baseline_a = st.sidebar.slider("Baseline start year", min_value=1950, max_value=2010, value=1961)
    baseline_b = st.sidebar.slider("Baseline end year", min_value=1965, max_value=2023, value=1990)
    compare_start = st.sidebar.slider("Comparison start year", min_value=1950, max_value=2020, value=2001)
    compare_end = st.sidebar.slider("Comparison end year", min_value=1955, max_value=2023, value=2023)
    baseline_b = max(baseline_b, baseline_a)
    compare_end = max(compare_end, compare_start)

    temp = to_display_array(dataset["t2m"], "t2m")
    precip = to_display_array(dataset["precipitation"], "precipitation")
    pressure = to_display_array(dataset["sea_level_pressure"], "sea_level_pressure")
    wind = to_display_array(dataset["wind_speed"], "wind_speed")

    temp_axes = detect_axes(temp)
    precip_axes = detect_axes(precip)
    pressure_axes = detect_axes(pressure)
    wind_axes = detect_axes(wind)

    temp_series = spatial_mean_series(temp, temp_axes, region_name, anomaly_mode=False)
    temp_frame = _to_frame(temp_series, temp_axes["time"])
    baseline_mask = (temp_frame["time"].dt.year >= baseline_a) & (temp_frame["time"].dt.year <= baseline_b)
    baseline_mean = float(temp_frame.loc[baseline_mask, "value"].mean())
    temp_frame["anomaly"] = temp_frame["value"] - baseline_mean

    precip_annual = annual_mean_series(precip, precip_axes, region_name, anomaly_mode=False)
    precip_frame = (
        precip_annual.mean(dim=[precip_axes["lat"], precip_axes["lon"]])
        .to_dataframe(name="value")
        .reset_index()
        .rename(columns={"year": "time"})
    )
    precip_frame["time"] = pd.to_datetime(precip_frame["time"].astype(str) + "-01-01")

    pressure_series = spatial_mean_series(pressure, pressure_axes, region_name, anomaly_mode=False)
    pressure_frame = _to_frame(pressure_series, pressure_axes["time"])

    wind_series = spatial_mean_series(wind, wind_axes, region_name, anomaly_mode=False)
    wind_frame = _to_frame(wind_series, wind_axes["time"])

    comparison_before = period_mean(temp, temp_axes, pd.Timestamp(f"{baseline_a}-01-01"), pd.Timestamp(f"{baseline_b}-12-01"), region_name)
    comparison_after = period_mean(temp, temp_axes, pd.Timestamp(f"{compare_start}-01-01"), pd.Timestamp(f"{compare_end}-12-01"), region_name)
    difference_map = comparison_after - comparison_before

    driver_snapshot = {
        "Temp anomaly": float(temp_frame["anomaly"].iloc[-1]),
        "Precip delta": float(precip_frame["value"].iloc[-1] - precip_frame["value"].mean()),
        "Pressure delta": float(pressure_frame["value"].iloc[-1] - pressure_frame["value"].mean()),
        "Wind delta": float(wind_frame["value"].iloc[-1] - wind_frame["value"].mean()),
    }

    render_info_banner(
        f"Signals are derived from the bundled or uploaded NetCDF workspace ({label}) and aggregated over {region_name}."
    )

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Latest anomaly", f"{temp_frame['anomaly'].iloc[-1]:+.2f} deg C", f"vs {baseline_a}-{baseline_b}")
    with metric_cols[1]:
        render_metric_card("Recent precipitation", f"{precip_frame['value'].iloc[-1]:.1f} mm/month", "Annualized regional mean")
    with metric_cols[2]:
        render_metric_card("Pressure pulse", f"{pressure_frame['value'].iloc[-1]:.1f} hPa", "Latest regional mean")
    with metric_cols[3]:
        render_metric_card("Wind transport", f"{wind_frame['value'].iloc[-1]:.2f} m/s", "Latest regional mean")

    top_left, top_right = st.columns(2)
    with top_left:
        render_section_intro(
            "Temperature anomaly trend",
            "The area line shows how far the regional temperature signal has moved away from its selected baseline window.",
            eyebrow="Signal 01",
        )
        anomaly_chart = temp_frame[["time", "anomaly"]].rename(columns={"anomaly": "value"})
        st.plotly_chart(
            create_timeline_figure(anomaly_chart, title="Temperature anomaly", value_column="value", y_label="deg C"),
            use_container_width=True,
        )
    with top_right:
        render_section_intro(
            "Anomaly bars",
            "Bars make regime shifts easier to read quickly by separating positive and negative departures.",
            eyebrow="Signal 02",
        )
        st.plotly_chart(
            create_anomaly_bar_figure(
                temp_frame.tail(36)[["time", "anomaly"]],
                title="Temperature anomaly bars",
                value_column="anomaly",
                y_label="deg C",
            ),
            use_container_width=True,
        )

    mid_left, mid_right = st.columns(2)
    with mid_left:
        render_section_intro(
            "Seasonal precipitation profile",
            "Monthly bars simplify the hydrologic cycle and make wet and dry seasons obvious in one glance.",
            eyebrow="Signal 03",
        )
        st.plotly_chart(
            create_seasonality_bar_figure(
                precip_frame,
                title="Seasonal precipitation signature",
                value_column="value",
                y_label="mm/month",
            ),
            use_container_width=True,
        )
    with mid_right:
        render_section_intro(
            "Driver snapshot",
            "Ranked deviations show which climate driver is furthest from its long-run average right now.",
            eyebrow="Signal 04",
        )
        st.plotly_chart(
            create_ranked_bar_figure(
                driver_snapshot,
                title="Latest driver deviations",
                x_label="Deviation from long-run mean",
                diverging=True,
            ),
            use_container_width=True,
        )

    lower_left, lower_right = st.columns(2)
    with lower_left:
        render_section_intro(
            "Pressure regime",
            "Sea-level pressure acts as a compact atmospheric circulation indicator across the region.",
            eyebrow="Signal 05",
        )
        st.plotly_chart(
            create_timeline_figure(
                pressure_frame,
                title="Pressure trend",
                value_column="value",
                y_label="hPa",
                color="#FF5C8A",
            ),
            use_container_width=True,
        )
    with lower_right:
        render_section_intro(
            "Wind transport",
            "Regional wind speed highlights circulation shifts that can support transport, storms, or fire weather.",
            eyebrow="Signal 06",
        )
        st.plotly_chart(
            create_timeline_figure(
                wind_frame,
                title="Wind trend",
                value_column="value",
                y_label="m/s",
                color="#6EFF9A",
            ),
            use_container_width=True,
        )

    render_section_intro(
        "Comparison heatmap",
        "The difference map makes it obvious where the later climate window has diverged most strongly from the baseline.",
        eyebrow="Compare",
    )
    st.plotly_chart(
        create_heatmap(
            difference_map,
            temp_axes,
            title=f"Temperature change map ({compare_start}-{compare_end} minus {baseline_a}-{baseline_b})",
            colorscale="RdBu_r",
            colorbar_title="deg C",
        ),
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
