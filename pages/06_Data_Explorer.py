from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.chart_factory import create_animated_heatmap, create_heatmap, create_spatial_map, create_time_series
from utils.data_loader import (
    REGION_BOUNDS,
    annual_mean_series,
    detect_axes,
    format_variable_label,
    format_variable_units,
    get_active_dataset,
    get_time_values,
    nearest_point_series,
    period_mean,
    prepare_map_slice,
    subset_region,
    to_display_array,
    variable_label_map,
    variable_options,
)
from utils.stats_engine import build_trend_series, compute_linear_trend, detect_anomalies, summarize_values
from utils.style import render_app_shell, render_info_banner, render_metric_card, render_page_hero, render_section_intro


st.set_page_config(page_title="ATLAS | Data Explorer", page_icon=":material/travel_explore:", layout="wide")


def _resolve_colorscale(variable_name: str, anomaly_mode: bool) -> str:
    if anomaly_mode:
        return "RdBu_r"
    if variable_name == "precipitation":
        return "YlGnBu"
    if variable_name == "wind_speed":
        return "Tealgrn"
    if variable_name == "sea_level_pressure":
        return "Viridis"
    return "Turbo"


def main() -> None:
    render_app_shell(
        "Data Explorer",
        "Freeform dataset browsing, map analytics, local time-series extraction, and exports.",
        search_placeholder="Search variable, region, or timeline",
    )
    render_page_hero(
        "Scientific workspace",
        "Data Explorer",
        "Explore gridded climate datasets with multiple map styles, local extraction, comparisons, and animated historical playback.",
        subtitle="Flexible analysis on top of the bundled or uploaded NetCDF grid",
    )

    dataset, label = get_active_dataset()
    variables = variable_options(dataset)
    labels = variable_label_map(dataset)

    with st.sidebar:
        st.header("Explorer controls")
        selected_var = st.selectbox("Variable", variables, format_func=lambda name: labels.get(name, name))
        data_array = to_display_array(dataset[selected_var], selected_var)
        axes = detect_axes(data_array)
        time_values = get_time_values(data_array, axes)
        selected_time = st.select_slider(
            "Time step",
            options=list(time_values),
            value=time_values[-1],
            format_func=lambda ts: pd.Timestamp(ts).strftime("%Y-%m"),
        )
        region_name = st.selectbox("Region", list(REGION_BOUNDS.keys()), index=0)
        projection = st.selectbox("Projection", ["Equirectangular", "Robinson", "Orthographic"], index=1)
        anomaly_mode = st.toggle("Anomaly mode", value=False)
        compare_start = st.slider("Compare window A start", min_value=1950, max_value=2004, value=1961)
        compare_end = st.slider("Compare window B end", min_value=1980, max_value=2023, value=2023)
        compare_end = max(compare_end, compare_start + 19)

    region_view = subset_region(data_array, axes, region_name)
    lat_values = region_view[axes["lat"]].values
    lon_values = region_view[axes["lon"]].values
    selected_lat = st.sidebar.slider("Latitude", min_value=float(lat_values.min()), max_value=float(lat_values.max()), value=float(lat_values[len(lat_values) // 2]), step=2.5)
    selected_lon = st.sidebar.slider("Longitude", min_value=float(lon_values.min()), max_value=float(lon_values.max()), value=float(lon_values[len(lon_values) // 2]), step=2.5)

    map_slice = prepare_map_slice(data_array, axes, pd.Timestamp(selected_time), region_name, anomaly_mode)
    series = nearest_point_series(data_array, axes, selected_lat, selected_lon, anomaly_mode)
    series_df = series.to_dataframe(name=selected_var).reset_index().rename(columns={axes["time"]: "time"})
    trend = compute_linear_trend(series, axes["time"])
    trend_df = build_trend_series(series, axes["time"], trend)
    anomalies = detect_anomalies(series)
    summary = summarize_values(map_slice)
    colorscale = _resolve_colorscale(selected_var, anomaly_mode)

    render_info_banner(f"Explorer source: {label}. Variable: {format_variable_label(data_array, selected_var)}. Region: {region_name}.")

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Mean", f"{summary['mean']:.2f}", format_variable_units(data_array) or "units")
    with metric_cols[1]:
        render_metric_card("Max", f"{summary['max']:.2f}", "Current slice maximum")
    with metric_cols[2]:
        render_metric_card("Min", f"{summary['min']:.2f}", "Current slice minimum")
    with metric_cols[3]:
        render_metric_card("Trend", f"{trend['slope_per_year']:+.3f}/yr", f"{int(anomalies['count'])} anomalies at selected point")

    tab_explore, tab_compare, tab_timelapse = st.tabs(["Explore", "Compare", "Timelapse"])

    with tab_explore:
        map_col, series_col = st.columns((1.28, 0.92))
        with map_col:
            st.plotly_chart(
                create_spatial_map(
                    map_slice,
                    axes,
                    title=f"{format_variable_label(data_array, selected_var)} · {pd.Timestamp(selected_time).strftime('%B %Y')}",
                    colorscale=colorscale,
                    colorbar_title=format_variable_units(data_array) or selected_var,
                    projection=projection,
                ),
                use_container_width=True,
            )
            st.plotly_chart(
                create_heatmap(
                    map_slice,
                    axes,
                    title="Grid heatmap",
                    colorscale=colorscale,
                    colorbar_title=format_variable_units(data_array) or selected_var,
                ),
                use_container_width=True,
            )
        with series_col:
            st.plotly_chart(
                create_time_series(
                    series_df=series_df,
                    value_column=selected_var,
                    trend_df=trend_df,
                    anomaly_mask=anomalies["mask"],
                    title=f"Local signal near ({selected_lat:.1f}, {selected_lon:.1f})",
                    y_label=f"{format_variable_label(data_array, selected_var)} ({format_variable_units(data_array)})",
                ),
                use_container_width=True,
            )
            st.download_button(
                "Download local series CSV",
                data=series_df.to_csv(index=False).encode("utf-8"),
                file_name=f"atlas_series_{selected_var}_{selected_lat:.1f}_{selected_lon:.1f}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with tab_compare:
        before_slice = period_mean(data_array, axes, pd.Timestamp(f"{compare_start}-01-01"), pd.Timestamp(f"{compare_start + 19}-12-01"), region_name)
        after_slice = period_mean(data_array, axes, pd.Timestamp(f"{compare_end - 19}-01-01"), pd.Timestamp(f"{compare_end}-12-01"), region_name)
        difference = after_slice - before_slice
        row_a, row_b = st.columns(2)
        with row_a:
            st.plotly_chart(
                create_heatmap(before_slice, axes, title=f"Window A ({compare_start}-{compare_start + 19})", colorscale="Turbo", colorbar_title=format_variable_units(data_array) or selected_var),
                use_container_width=True,
            )
        with row_b:
            st.plotly_chart(
                create_heatmap(after_slice, axes, title=f"Window B ({compare_end - 19}-{compare_end})", colorscale="Turbo", colorbar_title=format_variable_units(data_array) or selected_var),
                use_container_width=True,
            )
        st.plotly_chart(
            create_heatmap(
                difference,
                axes,
                title="Difference map",
                colorscale="RdBu_r",
                colorbar_title=format_variable_units(data_array) or selected_var,
            ),
            use_container_width=True,
        )

    with tab_timelapse:
        annual_view = annual_mean_series(data_array, axes, region_name, anomaly_mode)
        st.plotly_chart(
            create_animated_heatmap(
                annual_view,
                axes,
                title=f"Annual timelapse · {format_variable_label(data_array, selected_var)}",
                colorscale=colorscale,
                colorbar_title=format_variable_units(data_array) or selected_var,
            ),
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
