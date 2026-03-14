from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.chart_factory import create_globe, create_timeline_figure
from utils.data_loader import detect_axes, get_active_dataset, spatial_mean_series, to_display_array
from utils.live_data import fetch_air_quality, fetch_current_weather, get_default_location_query, get_deploy_source_count, get_source_status, resolve_location
from utils.style import (
    render_app_shell,
    render_feature_card,
    render_info_banner,
    render_metric_card,
    render_page_hero,
    render_section_intro,
    render_source_card,
)


st.set_page_config(
    page_title="ATLAS mini max v2 | Climate Intelligence Platform",
    page_icon=":material/public:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _load_live_snapshot(query: str) -> dict[str, object] | None:
    try:
        location, resolved_weather = resolve_location(query)
        weather = resolved_weather or fetch_current_weather(location["lat"], location["lon"])
        air_current, _ = fetch_air_quality(location["lat"], location["lon"])
        return {"location": location, "weather": weather, "air": air_current}
    except Exception:
        return None


def main() -> None:
    render_app_shell(
        "Landing",
        "Planetary climate intelligence, real-time monitoring, and research workflows in one premium control surface.",
        search_placeholder="Search dashboards, locations, or climate signals",
    )
    dataset, source_label = get_active_dataset()
    logo_path = Path(__file__).resolve().parent / "assets" / "atlas_logo.svg"
    live_snapshot = _load_live_snapshot(st.session_state.get("atlas_ops_location", get_default_location_query()))

    logo_col, hero_col = st.columns((0.12, 0.88))
    with logo_col:
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)

    with hero_col:
        render_page_hero(
            "Climate intelligence platform",
            "ATLAS mini max v2",
            (
                "ATLAS unifies live atmospheric signals, satellite imagery, historical climate grids, model-assisted "
                "forecasting, and research workflows inside a single mission-control interface."
            ),
            subtitle="Real-time data, climate signals, risk detection, and predictive insight",
        )

    cta_cols = st.columns(2)
    with cta_cols[0]:
        st.page_link("pages/00_Story_Mode.py", label="Start Story Mode", icon=":material/play_circle:")
    with cta_cols[1]:
        st.page_link("pages/01_Dashboard.py", label="Explore Dashboard", icon=":material/dashboard:")

    secondary_cta_cols = st.columns(2)
    with secondary_cta_cols[0]:
        st.page_link("pages/02_Global_Climate_Map.py", label="View Global Map", icon=":material/public:")
    with secondary_cta_cols[1]:
        st.page_link("pages/06_Data_Explorer.py", label="Open Data Explorer", icon=":material/travel_explore:")

    render_info_banner(
        (
            f"Historical baseline is running from {source_label}. The deploy profile uses server-side environment variables "
            "or Streamlit secrets so API keys never need to be exposed in the public UI."
        )
    )

    render_section_intro(
        "Live climate metrics",
        "Operational cards pull from the same live integrations that power the dashboard and risk workflows.",
        eyebrow="Now",
    )
    latest_temp = to_display_array(dataset["t2m"], "t2m")
    latest_axes = detect_axes(latest_temp)
    latest_series = spatial_mean_series(latest_temp, latest_axes, "Global", anomaly_mode=False)
    latest_value = float(latest_series.values[-1])
    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Global surface temperature", f"{latest_value:.2f} deg C", "Latest grid-wide mean from bundled climate baseline")
    with metric_cols[1]:
        if live_snapshot:
            render_metric_card(
                "Live city temperature",
                f"{live_snapshot['weather']['temperature_c']:.1f} deg C",
                str(live_snapshot["location"]["label"]),
            )
        else:
            render_metric_card("Live city temperature", "API ready", "Connect OpenWeather to enable this card")
    with metric_cols[2]:
        if live_snapshot:
            render_metric_card(
                "Air quality",
                f"AQI {live_snapshot['air']['aqi']}",
                str(live_snapshot["air"]["category"]),
            )
        else:
            render_metric_card("Air quality", "API ready", "Connect OpenWeather air data to enable this card")
    with metric_cols[3]:
        render_metric_card("Connected sources", str(get_deploy_source_count()), "NASA GIBS, NOAA, OpenWeather, and the NetCDF workspace")

    render_section_intro(
        "Global map preview",
        "A planetary preview of the historical climate field anchors the landing page with the same visual language used throughout the product.",
        eyebrow="Preview",
    )
    map_col, timeline_col = st.columns((1.25, 0.75))
    latest_slice = latest_temp.isel(time=-1)
    with map_col:
        st.plotly_chart(
            create_globe(
                latest_slice,
                latest_axes,
                title="Global surface field preview",
                colorscale="RdBu_r",
                colorbar_title="deg C",
                marker_size=4,
            ),
            use_container_width=True,
        )
    with timeline_col:
        timeline_df = latest_series.to_dataframe(name="temperature").reset_index().rename(columns={latest_axes["time"]: "time"})
        st.plotly_chart(
            create_timeline_figure(
                timeline_df,
                title="Global activity timeline",
                value_column="temperature",
                y_label="deg C",
            ),
            use_container_width=True,
        )

    render_section_intro(
        "Platform modules",
        "The product is organized around live monitoring, historical analysis, risk scoring, and delivery workflows.",
        eyebrow="Capabilities",
    )
    feature_cols = st.columns(3)
    features = [
        ("Dashboard", "A mission-control summary of live weather, AQI, climate baselines, and risk signals."),
        ("Global Map", "Interactive globe and 2D map layers with timeline controls and satellite context."),
        ("Climate Signals", "Long-range anomalies, trend analysis, and historical period comparisons."),
        ("Risk Intelligence", "Flood, wildfire, heatwave, and storm scoring driven by live and historical context."),
        ("Predictions", "Model-assisted outlooks, anomaly detection, and natural-language climate queries."),
        ("Research Lab", "Scenario testing, dataset upload, and lightweight climate simulations."),
    ]
    for column, (title, body) in zip(feature_cols * 2, features):
        with column:
            render_feature_card(title, body)

    render_section_intro(
        "Research highlights",
        "ATLAS is designed to feel polished enough for a product demo while staying transparent about where the data comes from.",
        eyebrow="Source fabric",
    )
    source_cols = st.columns(3)
    statuses = get_source_status()
    for column, status in zip(source_cols * 2, statuses):
        with column:
            render_source_card(status["name"], status["status"], status["detail"])

    render_section_intro(
        "Launch the workspace",
        "Jump directly into the module you need without leaving the climate intelligence shell.",
        eyebrow="CTA",
    )
    action_cols = st.columns(4)
    with action_cols[0]:
        st.page_link("pages/01_Dashboard.py", label="Open Dashboard", icon=":material/dashboard:")
    with action_cols[1]:
        st.page_link("pages/04_Risk_Intelligence.py", label="Open Risk Intel", icon=":material/warning:")
    with action_cols[2]:
        st.page_link("pages/05_AI_Predictions.py", label="Open Predictions", icon=":material/auto_graph:")
    with action_cols[3]:
        st.page_link("pages/09_Settings.py", label="Open Settings", icon=":material/settings:")


if __name__ == "__main__":
    main()
