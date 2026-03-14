from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import xarray as xr

from utils.chart_factory import create_heatmap, create_prediction_figure
from utils.data_loader import (
    REGION_BOUNDS,
    clear_uploaded_file,
    detect_axes,
    get_active_dataset,
    get_dataset_choice,
    get_dataset_choices,
    get_time_values,
    prepare_map_slice,
    register_dataset_choice,
    register_uploaded_file,
    spatial_mean_series,
    to_display_array,
    variable_label_map,
    variable_options,
)
from utils.prediction_engine import build_forecast_frame
from utils.style import render_app_shell, render_feature_card, render_info_banner, render_metric_card, render_page_hero, render_section_intro


st.set_page_config(page_title="ATLAS | Research Lab", page_icon=":material/science:", layout="wide")


def _scenario_pattern(data_array, axes: dict[str, str | None]) -> np.ndarray:
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]
    lat_values = np.asarray(data_array[lat_axis].values, dtype=float)
    lon_values = np.asarray(data_array[lon_axis].values, dtype=float)
    lat_grid, lon_grid = np.meshgrid(lat_values, lon_values, indexing="ij")
    polar_amplification = 0.6 + 0.8 * (np.abs(lat_grid) / 90.0) ** 1.4
    wave_texture = 0.75 + 0.25 * np.cos(np.deg2rad(lon_grid * 1.8)) + 0.15 * np.sin(np.deg2rad(lat_grid * 3.0))
    return polar_amplification * wave_texture


def main() -> None:
    render_app_shell(
        "Research Lab",
        "Dataset upload, scenario simulation, and lightweight model testing.",
        search_placeholder="Search scenarios, uploaded datasets, or variables",
    )
    render_page_hero(
        "Experiment layer",
        "Research Lab",
        "Upload datasets, run quick climate scenarios, and test lightweight predictive workflows without leaving the product shell.",
        subtitle="Simulation runner and model sandbox",
    )

    with st.sidebar:
        st.header("Lab setup")
        dataset_choice = st.selectbox(
            "Dataset preset",
            get_dataset_choices(),
            index=get_dataset_choices().index(get_dataset_choice()),
        )
        register_dataset_choice(dataset_choice)
        uploaded = st.file_uploader("Upload NetCDF", type=["nc", "nc4", "cdf", "netcdf"])
        if uploaded is not None:
            register_uploaded_file(uploaded)
        if st.button("Use bundled dataset", use_container_width=True):
            clear_uploaded_file()

    dataset, label = get_active_dataset()
    variables = variable_options(dataset)
    labels = variable_label_map(dataset)
    variable = st.sidebar.selectbox("Variable", variables, format_func=lambda name: labels.get(name, name))
    region_name = st.sidebar.selectbox("Region", list(REGION_BOUNDS.keys()), index=0)
    temp_offset = st.sidebar.slider("Temperature offset (deg C)", min_value=-3.0, max_value=6.0, value=1.5, step=0.1)
    precip_scale = st.sidebar.slider("Precipitation scale", min_value=0.5, max_value=2.0, value=1.1, step=0.05)
    wind_scale = st.sidebar.slider("Wind scale", min_value=0.5, max_value=2.0, value=1.05, step=0.05)

    data_array = to_display_array(dataset[variable], variable)
    axes = detect_axes(data_array)
    time_values = get_time_values(data_array, axes)
    selected_time = st.sidebar.select_slider(
        "Scenario time",
        options=list(time_values),
        value=time_values[-1],
        format_func=lambda ts: pd.Timestamp(ts).strftime("%Y-%m"),
    )

    scenario_array = data_array.copy()
    pattern_field = xr.DataArray(
        _scenario_pattern(data_array, axes),
        dims=(axes["lat"], axes["lon"]),
        coords={axes["lat"]: data_array[axes["lat"]], axes["lon"]: data_array[axes["lon"]]},
    )
    if variable == "t2m":
        scenario_array = scenario_array + pattern_field * temp_offset
    elif variable == "precipitation":
        scenario_array = scenario_array * (1.0 + (precip_scale - 1.0) * pattern_field)
    elif variable == "wind_speed":
        scenario_array = scenario_array * (1.0 + (wind_scale - 1.0) * (0.65 + 0.35 * pattern_field))

    baseline_slice = prepare_map_slice(data_array, axes, pd.Timestamp(selected_time), region_name, anomaly_mode=False)
    scenario_slice = prepare_map_slice(scenario_array, axes, pd.Timestamp(selected_time), region_name, anomaly_mode=False)
    delta_slice = scenario_slice - baseline_slice

    baseline_series = spatial_mean_series(data_array, axes, region_name, anomaly_mode=False)
    baseline_df = baseline_series.to_dataframe(name="value").reset_index().rename(columns={axes["time"]: "time"})
    scenario_series = spatial_mean_series(scenario_array, axes, region_name, anomaly_mode=False)
    scenario_df = scenario_series.to_dataframe(name="value").reset_index().rename(columns={axes["time"]: "time"})
    forecast_df = build_forecast_frame(scenario_df, time_column="time", value_column="value", horizon=24)

    render_info_banner(
        f"Research Lab source: {label}. Variable under test: {variable}. Region: {region_name}. Scenario time: {pd.Timestamp(selected_time).strftime('%B %Y')}."
    )

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Dataset source", dataset_choice, label)
    with metric_cols[1]:
        render_metric_card("Variables", str(len(dataset.data_vars)), "Upload a richer NetCDF file to expand the lab")
    with metric_cols[2]:
        render_metric_card("Scenario delta", f"{float(delta_slice.mean().values):+.2f}", "Average map shift under the current scenario")
    with metric_cols[3]:
        render_metric_card("Prediction horizon", "24 months", "Trend-plus-seasonality scenario outlook")

    top_left, top_right = st.columns(2)
    with top_left:
        render_section_intro(
            "Simulation runner",
            "The lab applies spatially varying perturbations so the scenario delta map stays visible and readable instead of collapsing into a uniform blank field.",
            eyebrow="Scenario",
        )
        st.plotly_chart(
            create_heatmap(
                delta_slice,
                axes,
                title="Scenario delta map",
                colorscale="RdBu_r",
                colorbar_title="Delta",
            ),
            use_container_width=True,
        )
    with top_right:
        render_section_intro(
            "Scenario outlook",
            "The current scenario feeds a lightweight predictive model so you can test directional impact over the next two years.",
            eyebrow="Outlook",
        )
        st.plotly_chart(
            create_prediction_figure(
                observed_df=scenario_df,
                forecast_df=forecast_df,
                title="Scenario projection",
                value_column="value",
                y_label=variable,
            ),
            use_container_width=True,
        )

    render_section_intro(
        "Model testing",
        "This build keeps the lab transparent and fast. It is designed for iteration and comparison, not for opaque black-box runs.",
        eyebrow="Testing",
    )
    holdout = baseline_df.tail(24).copy()
    train = baseline_df.iloc[:-24].copy() if len(baseline_df) > 24 else baseline_df.copy()
    model_forecast = build_forecast_frame(train, time_column="time", value_column="value", horizon=min(24, len(holdout)))
    if not holdout.empty and not model_forecast.empty:
        merged = holdout.reset_index(drop=True).copy()
        merged["forecast"] = model_forecast["forecast"].values[: len(merged)]
        rmse = float(np.sqrt(np.mean((merged["value"] - merged["forecast"]) ** 2)))
        render_feature_card("Holdout test", f"Approximate RMSE on the latest holdout window: {rmse:.3f}.")
    render_feature_card("Scenario knobs", "Temperature offset, precipitation scale, and wind scale now drive a spatially varying perturbation pattern.")
    render_feature_card("Dataset upload", "Uploaded NetCDF files become available immediately in the same historical analytics pipeline.")


if __name__ == "__main__":
    main()
