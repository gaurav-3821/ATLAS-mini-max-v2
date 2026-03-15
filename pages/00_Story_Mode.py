from __future__ import annotations

import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.real_climate import (
    get_real_global_temperature_frames,
    load_nasa_eonet_events,
    load_nasa_gistemp_gridded,
    load_nasa_gistemp_zonal_means,
)
from utils.style import render_app_shell, render_page_hero
from utils.story_content import STORY_MODE_CONFIG


st.set_page_config(page_title="ATLAS | Story Mode", page_icon=":material/play_circle:", layout="wide")


def _title_with_source(title: str, source: str) -> dict[str, object]:
    return {
        "text": f"{title}<br><sup>{html.escape(source)}</sup>",
        "x": 0.01,
        "xanchor": "left",
    }


def _build_demo_heatmap() -> go.Figure:
    grid = load_nasa_gistemp_gridded()
    if grid is not None:
        latest = grid.isel(time=-1)
        lat_name = "lat" if "lat" in latest.dims else latest.dims[-2]
        lon_name = "lon" if "lon" in latest.dims else latest.dims[-1]
        lat = latest[lat_name].values
        lon = latest[lon_name].values
        values = latest.values
        source_label = f"NASA GISTEMP gridded anomaly ({pd.to_datetime(grid['time'].values[-1]).strftime('%Y-%m')})"
    else:
        lat = np.linspace(-90, 90, 61)
        lon = np.linspace(-180, 180, 121)
        lon_mesh, lat_mesh = np.meshgrid(lon, lat)
        values = (
            0.2
            + 0.55 * np.sin(np.deg2rad(lat_mesh)) ** 2
            + 0.18 * np.cos(np.deg2rad(lon_mesh / 1.7))
            + 0.12 * np.sin(np.deg2rad((lat_mesh + lon_mesh) / 2.8))
        )
        source_label = "Illustrative anomaly field used when gridded source is unavailable"

    figure = go.Figure(
        data=[
            go.Heatmap(
                z=values,
                x=lon,
                y=lat,
                colorscale="Turbo",
                zsmooth="best",
                colorbar=dict(title="Temp anomaly (deg C)"),
                hovertemplate="Lat %{y:.1f}<br>Lon %{x:.1f}<br>Anomaly %{z:.2f}<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        title=_title_with_source("Global Temperature Heatmap", source_label),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Longitude",
        yaxis_title="Latitude",
    )
    return figure


def _global_temperature_line_chart() -> go.Figure:
    _, annual_frame, source_name = get_real_global_temperature_frames()
    if annual_frame is not None and not annual_frame.empty:
        years = annual_frame["time"].dt.year.tolist()
        values = annual_frame["anomaly"].astype(float).tolist()
        subtitle = f"Source: {source_name}"
    else:
        years = [1900, 1920, 1940, 1960, 1980, 2000, 2010, 2020, 2024]
        values = [-0.08, -0.26, 0.05, 0.03, 0.26, 0.39, 0.72, 1.01, 1.28]
        subtitle = "Source: NASA GISTEMP-aligned fallback"

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=years,
            y=values,
            mode="lines+markers",
            line=dict(color="#00E5FF", width=3, shape="spline"),
            marker=dict(size=9, color="#FFD84D"),
            fill="tozeroy",
            fillcolor="rgba(0,229,255,0.12)",
            name="Global anomaly",
        )
    )
    figure.update_layout(
        title=_title_with_source("Global Temperature Anomaly", subtitle),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Year",
        yaxis_title="Temperature anomaly (deg C)",
    )
    return figure


def _arctic_comparison_chart() -> go.Figure:
    zonal_frame = load_nasa_gistemp_zonal_means()
    if zonal_frame is not None and {"time", "Glob", "64N-90N"}.issubset(zonal_frame.columns):
        filtered = zonal_frame[zonal_frame["year"] >= 1970].copy()
        years = filtered["year"].tolist()
        series_map = {
            "Global": filtered["Glob"].astype(float).tolist(),
            "Arctic": filtered["64N-90N"].astype(float).tolist(),
        }
        subtitle = "Source: NASA GISTEMP zonal annual anomalies"
    else:
        years = [1970, 1980, 1990, 2000, 2010, 2020, 2024]
        series_map = {
            "Global": [0.03, 0.26, 0.44, 0.62, 0.72, 1.01, 1.28],
            "Arctic": [0.14, 0.77, 1.07, 1.63, 2.18, 3.11, 3.32],
        }
        subtitle = "Source: NASA GISTEMP-aligned fallback"

    figure = go.Figure()
    for region, color in [("Global", "#00E5FF"), ("Arctic", "#FF5C8A")]:
        figure.add_trace(
            go.Scatter(
                x=years,
                y=series_map[region],
                mode="lines+markers",
                line=dict(color=color, width=3, shape="spline"),
                marker=dict(size=8),
                name=region,
            )
        )
    figure.update_layout(
        title=_title_with_source("Global vs Arctic Warming", subtitle),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Year",
        yaxis_title="Temperature anomaly (deg C)",
    )
    return figure


def _extreme_events_chart() -> go.Figure:
    frame = pd.DataFrame(
        [
            {"period": "1980-2024 avg", "events": 9.0},
            {"period": "2020-2024 avg", "events": 23.0},
        ]
    )
    figure = go.Figure(
        data=[
            go.Bar(
                x=frame["period"],
                y=frame["events"],
                marker=dict(color="#FFD84D", line=dict(color="#000000", width=1)),
                hovertemplate="Period %{x}<br>Avg events/year %{y:.1f}<extra></extra>",
                name="U.S. billion-dollar disasters",
            )
        ]
    )
    figure.update_layout(
        title=_title_with_source("NOAA U.S. Billion-Dollar Disasters", "Source: NOAA NCEI annual averages by period"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Period",
        yaxis_title="Average events per year",
    )
    return figure


def _future_projection_chart() -> go.Figure:
    scenarios = {
        "low_emissions": {"years": [2020, 2040, 2060, 2080, 2100], "warming_c": [1.2, 1.5, 1.6, 1.7, 1.8]},
        "medium_emissions": {"years": [2020, 2040, 2060, 2080, 2100], "warming_c": [1.2, 1.6, 2.0, 2.4, 2.7]},
        "high_emissions": {"years": [2020, 2040, 2060, 2080, 2100], "warming_c": [1.2, 1.7, 2.4, 3.4, 4.4]},
    }
    colors = {
        "low_emissions": "#6EFF9A",
        "medium_emissions": "#FFD84D",
        "high_emissions": "#FF5C8A",
    }
    figure = go.Figure()
    for name, payload in scenarios.items():
        figure.add_trace(
            go.Scatter(
                x=payload["years"],
                y=payload["warming_c"],
                mode="lines+markers",
                line=dict(color=colors[name], width=3, shape="spline"),
                marker=dict(size=8),
                name=name.replace("_", " ").title(),
            )
        )
    figure.update_layout(
        title=_title_with_source("Future Warming Scenarios", "Source: IPCC AR6 illustrative scenario ranges"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Year",
        yaxis_title="Projected warming (deg C)",
    )
    return figure


def _extreme_events_map() -> go.Figure | None:
    events = load_nasa_eonet_events(limit=30)
    if events.empty:
        return None

    figure = go.Figure(
        data=[
            go.Scattergeo(
                lon=events["lon"],
                lat=events["lat"],
                text=events["title"],
                customdata=events[["category", "date"]].astype(str).to_numpy(),
                mode="markers",
                marker=dict(size=8, color="#FF5C8A", line=dict(color="#FFFFFF", width=0.5), opacity=0.8),
                hovertemplate="%{text}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
                name="Open events",
            )
        ]
    )
    figure.update_layout(
        title=_title_with_source("Open Extreme Events", "Source: NASA EONET open severe storms and wildfires"),
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="#111827",
            showocean=True,
            oceancolor="#08111F",
            showcountries=True,
            countrycolor="rgba(255,255,255,0.24)",
            coastlinecolor="rgba(255,255,255,0.34)",
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
    )
    return figure


def _render_step_chips(steps: list[dict[str, object]], active_index: int) -> None:
    columns = st.columns(len(steps))
    for index, (column, step) in enumerate(zip(columns, steps)):
        active_class = "active" if index == active_index else ""
        title = html.escape(str(step["title"]))
        component = html.escape(str(step["visual_panel"]["component"]))
        with column:
            st.markdown(
                f"""
                <div class="atlas-step-chip {active_class}">
                    <strong>{index + 1}. {title}</strong>
                    <span>{component}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_visual(step: dict[str, object]) -> None:
    component = str(step["visual_panel"]["component"])
    if component == "heatmap + line_chart":
        map_col, chart_col = st.columns((1.05, 0.95))
        with map_col:
            st.plotly_chart(_build_demo_heatmap(), use_container_width=True)
        with chart_col:
            st.plotly_chart(_global_temperature_line_chart(), use_container_width=True)
        return
    if component == "comparison_chart":
        st.plotly_chart(_arctic_comparison_chart(), use_container_width=True)
        return
    if component == "line_chart":
        st.plotly_chart(_global_temperature_line_chart(), use_container_width=True)
        return
    if component == "bar_chart":
        top_col, bottom_col = st.columns((0.95, 1.05))
        with top_col:
            st.plotly_chart(_extreme_events_chart(), use_container_width=True)
        with bottom_col:
            event_map = _extreme_events_map()
            if event_map is None:
                st.warning("Live NASA EONET event map is unavailable right now")
            else:
                st.plotly_chart(event_map, use_container_width=True)
        return
    if component == "scenario_projection_chart":
        st.plotly_chart(_future_projection_chart(), use_container_width=True)
        return
    st.warning("Visualization not implemented yet")


def main() -> None:
    render_app_shell(
        "Story Mode",
        "Interactive climate narrative with stable scene navigation, visible narrative text, and reliable visual rendering.",
        search_placeholder="Search story chapters",
    )
    render_page_hero(
        "Interactive narrative",
        "ATLAS Story Mode",
        "A guided climate story built with reliable Streamlit rendering, chapter chips, and fallback demo visuals.",
        subtitle="Narrative text, AI insight, and visual scenes that always render",
    )

    story_steps = STORY_MODE_CONFIG["story_steps"]

    if "step_index" not in st.session_state:
        st.session_state.step_index = 0

    step_index = min(st.session_state.step_index, len(story_steps) - 1)
    step = story_steps[step_index]

    control_cols = st.columns((1, 1, 4))
    with control_cols[0]:
        if st.button("Previous", use_container_width=True, disabled=step_index == 0):
            st.session_state.step_index -= 1
            st.rerun()
    with control_cols[1]:
        if st.button("Next", use_container_width=True, disabled=step_index == len(story_steps) - 1):
            st.session_state.step_index += 1
            st.rerun()
    with control_cols[2]:
        st.progress((step_index + 1) / len(story_steps), text=f"Chapter {step_index + 1} of {len(story_steps)}")

    _render_step_chips(story_steps, step_index)

    selected_index = st.radio(
        "Story navigation",
        options=list(range(len(story_steps))),
        index=step_index,
        format_func=lambda index: story_steps[index]["title"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected_index != step_index:
        st.session_state.step_index = selected_index
        st.rerun()

    st.markdown("### Visualization")
    _render_visual(step)

    st.markdown("### " + str(step["title"]))
    st.write(step["narrative_panel"]["text"])
    st.info("AI Insight: " + str(step["narrative_panel"].get("ai_insight", "No AI insight available for this scene.")))


if __name__ == "__main__":
    main()
