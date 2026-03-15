from __future__ import annotations

import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.style import render_app_shell, render_page_hero
from utils.story_content import STORY_MODE_CONFIG


st.set_page_config(page_title="ATLAS | Story Mode", page_icon=":material/play_circle:", layout="wide")


def _build_demo_heatmap() -> go.Figure:
    lat = np.linspace(-90, 90, 61)
    lon = np.linspace(-180, 180, 121)
    lon_mesh, lat_mesh = np.meshgrid(lon, lat)
    values = (
        0.2
        + 0.55 * np.sin(np.deg2rad(lat_mesh)) ** 2
        + 0.18 * np.cos(np.deg2rad(lon_mesh / 1.7))
        + 0.12 * np.sin(np.deg2rad((lat_mesh + lon_mesh) / 2.8))
    )

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
        title="Global Temperature Heatmap",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Longitude",
        yaxis_title="Latitude",
    )
    return figure


def _global_temperature_line_chart() -> go.Figure:
    source = STORY_MODE_CONFIG["data_sources"]["global_temperature"]
    years = source["years"]
    values = source["temperature_anomaly_c"]

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
        title="Global Temperature Anomaly",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Year",
        yaxis_title="Temperature anomaly (deg C)",
    )
    return figure


def _arctic_comparison_chart() -> go.Figure:
    source = STORY_MODE_CONFIG["data_sources"]["arctic_amplification"]
    years = source["years"]
    figure = go.Figure()
    for region, color in [("Global", "#00E5FF"), ("Arctic", "#FF5C8A")]:
        figure.add_trace(
            go.Scatter(
                x=years,
                y=source["anomaly_c"][region],
                mode="lines+markers",
                line=dict(color=color, width=3, shape="spline"),
                marker=dict(size=8),
                name=region,
            )
        )
    figure.update_layout(
        title="Global vs Arctic Warming",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Year",
        yaxis_title="Temperature anomaly (deg C)",
    )
    return figure


def _extreme_events_chart() -> go.Figure:
    records = STORY_MODE_CONFIG["data_sources"]["extreme_events"]["events"]
    frame = pd.DataFrame(records)
    figure = go.Figure(
        data=[
            go.Bar(
                x=frame["year"],
                y=frame["events"],
                marker=dict(color="#FFD84D", line=dict(color="#000000", width=1)),
                hovertemplate="Year %{x}<br>Events %{y}<extra></extra>",
                name="Severe events",
            )
        ]
    )
    figure.update_layout(
        title="Extreme Weather Events Over Time",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Year",
        yaxis_title="Event count",
    )
    return figure


def _future_projection_chart() -> go.Figure:
    scenarios = STORY_MODE_CONFIG["data_sources"]["future_projection"]["scenarios"]
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
        title="Future Warming Scenarios",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Year",
        yaxis_title="Projected warming (deg C)",
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
        st.plotly_chart(_extreme_events_chart(), use_container_width=True)
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
