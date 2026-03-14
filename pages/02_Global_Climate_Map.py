from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from utils.chart_factory import create_globe, create_heatmap, create_latitude_profile, create_spatial_map
from utils.data_loader import (
    REGION_BOUNDS,
    detect_axes,
    format_variable_label,
    format_variable_units,
    get_active_dataset,
    get_time_values,
    prepare_map_slice,
    subset_region,
    to_display_array,
    top_signal_hotspots,
    variable_label_map,
    variable_options,
)
from utils.live_data import SATELLITE_LAYERS, fetch_satellite_snapshot, get_default_location_query, resolve_location
from utils.style import render_app_shell, render_feature_card, render_info_banner, render_metric_card, render_page_hero, render_section_intro


st.set_page_config(page_title="ATLAS | Global Climate Map", page_icon=":material/public:", layout="wide")


def _layer_palette(variable_name: str, anomaly_mode: bool) -> str:
    if anomaly_mode:
        return "RdBu_r"
    if variable_name == "precipitation":
        return "Viridis"
    if variable_name == "wind_speed":
        return "Tealgrn"
    return "Turbo"


def main() -> None:
    render_app_shell(
        "Global Map",
        "Interactive global field views with better 2D readability, orbital context, timeline scrubbing, and satellite overlays.",
        search_placeholder="Search a region, layer, or hotspot",
    )
    render_page_hero(
        "Planet view",
        "Global Climate Map",
        "A clearer climate map built around an analyst-friendly 2D surface, a cinematic orbital globe, hotspot ranking, and NASA imagery context.",
        subtitle="Readable 2D fields, orbital globe context, and satellite overlays",
    )

    dataset, label = get_active_dataset()
    variables = variable_options(dataset)
    labels = variable_label_map(dataset)

    with st.sidebar:
        st.header("Map controls")
        selected_var = st.selectbox("Climate layer", variables, format_func=lambda name: labels.get(name, name))
        data_array = to_display_array(dataset[selected_var], selected_var)
        axes = detect_axes(data_array)
        time_values = get_time_values(data_array, axes)
        selected_time = st.select_slider(
            "Timeline scrubber",
            options=list(time_values),
            value=time_values[-1],
            format_func=lambda ts: pd.Timestamp(ts).strftime("%Y-%m"),
        )
        region_name = st.selectbox("Region filter", list(REGION_BOUNDS.keys()), index=0)
        projection = st.selectbox("2D map style", ["Analyst contour", "Dense field", "Regional focus"], index=0)
        anomaly_mode = st.toggle("Anomaly mode", value=False)
        satellite_layer = st.selectbox("Satellite overlay", list(SATELLITE_LAYERS.keys()), index=0)
        satellite_date = st.date_input("Satellite date", value=date.today() - timedelta(days=1), max_value=date.today())

    map_slice = prepare_map_slice(data_array, axes, pd.Timestamp(selected_time), region_name, anomaly_mode)
    colorscale = _layer_palette(selected_var, anomaly_mode)
    hotspots = top_signal_hotspots(map_slice, axes, top_n=10, absolute=True)
    region_view = subset_region(data_array, axes, region_name)
    lat_values = region_view[axes["lat"]].values
    lon_values = region_view[axes["lon"]].values

    render_info_banner(
        f"Map layer: {format_variable_label(data_array, selected_var)}. Source: {label}. Region filter currently targets {region_name}."
    )

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Layer", format_variable_label(data_array, selected_var), "Current climate field")
    with metric_cols[1]:
        render_metric_card("Timeline", pd.Timestamp(selected_time).strftime("%b %Y"), "Historical timeline scrubber")
    with metric_cols[2]:
        render_metric_card("Hotspots", str(len(hotspots)), "Top-ranked cells by absolute signal strength")
    with metric_cols[3]:
        render_metric_card("Region extent", region_name, f"{len(lat_values)} lat cells x {len(lon_values)} lon cells")

    left_col, right_col = st.columns((1.35, 0.85))
    with left_col:
        render_section_intro(
            "Interactive map surface",
            "Use the clearer 2D analyst surface for fast pattern reading, then switch to the orbital globe for broader spatial context.",
            eyebrow="Surface",
        )
        tab_map, tab_globe = st.tabs(["2D map", "Orbital globe"])
        with tab_map:
            st.plotly_chart(
                create_spatial_map(
                    map_slice,
                    axes,
                    title=f"{format_variable_label(data_array, selected_var)} - {pd.Timestamp(selected_time).strftime('%B %Y')}",
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
                    title="Grid intensity view",
                    colorscale=colorscale,
                    colorbar_title=format_variable_units(data_array) or selected_var,
                ),
                use_container_width=True,
            )
        with tab_globe:
            st.plotly_chart(
                create_globe(
                    map_slice,
                    axes,
                    title="Orbital climate layer",
                    colorscale=colorscale,
                    colorbar_title=format_variable_units(data_array) or selected_var,
                    marker_size=5,
                ),
                use_container_width=True,
            )
            st.plotly_chart(
                create_latitude_profile(
                    map_slice,
                    axes,
                    title="Latitudinal signature",
                    x_label=format_variable_units(data_array) or selected_var,
                ),
                use_container_width=True,
            )

    with right_col:
        render_section_intro(
            "Signal hotspots",
            "These ranked cells highlight where the selected layer is strongest or most unusual inside the current region window.",
            eyebrow="Hotspots",
        )
        render_feature_card("Map readout", f"Current view: {region_name} in {projection.lower()} mode for {pd.Timestamp(selected_time).strftime('%B %Y')}.")
        if hotspots.empty:
            st.info("No hotspot cells were generated for the current slice.")
        else:
            st.dataframe(hotspots.head(10), use_container_width=True, hide_index=True)
        render_feature_card(
            "Region logic",
            "This build uses region filters instead of heavy country polygons so the historical NetCDF workflow stays fast and portable."
        )
        try:
            location_query = st.session_state.get("atlas_ops_location", get_default_location_query())
            location, _ = resolve_location(location_query)
            satellite_bytes, satellite_meta = fetch_satellite_snapshot(
                location["lat"],
                location["lon"],
                image_date=satellite_date,
                layer_name=satellite_layer,
                span_degrees=10.0,
            )
            st.image(satellite_bytes, caption=f"{satellite_meta['layer_name']} around {location['label']}", use_container_width=True)
            st.link_button("Open in NASA Worldview", satellite_meta["worldview_url"], use_container_width=True)
        except Exception:
            st.info("Satellite overlay becomes available when a live location and NASA imagery request succeed.")


if __name__ == "__main__":
    main()
