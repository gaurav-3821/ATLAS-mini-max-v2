from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from utils.chart_factory import (
    create_air_quality_figure,
    create_donut_figure,
    create_forecast_figure,
    create_gauge_figure,
    create_ranked_bar_figure,
    create_risk_radar,
    create_station_history_figure,
)
from utils.live_data import (
    fetch_air_quality,
    fetch_forecast,
    fetch_historical_climate_context,
    fetch_current_weather,
    get_default_location_query,
    resolve_location,
)
from utils.risk_engine import build_risk_profile, build_risk_timeline
from utils.style import render_app_shell, render_feature_card, render_info_banner, render_metric_card, render_page_hero, render_section_intro


st.set_page_config(page_title="ATLAS | Risk Intelligence", page_icon=":material/warning:", layout="wide")


def _risk_timeline_chart(timeline_df) -> go.Figure:
    figure = go.Figure()
    for column, color in [("heatwave", "#FF5C8A"), ("flood", "#00E5FF"), ("storm", "#FFD84D")]:
        figure.add_trace(
            go.Scatter(
                x=timeline_df["time"],
                y=timeline_df[column],
                mode="lines",
                name=column.title(),
                line=dict(color=color, width=2.4),
            )
        )
    figure.update_layout(
        title="Short-range risk timeline",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.86)",
        font=dict(color="#FFFFFF", family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=56, b=12),
        xaxis_title="Time",
        yaxis_title="Risk score",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0),
    )
    figure.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    figure.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False, range=[0, 100])
    return figure


def main() -> None:
    render_app_shell(
        "Risk Intelligence",
        "Hazard scoring, AQI context, and short-range operational alerts for a selected location.",
        search_placeholder="Search heatwave, flood, wildfire, storm, or city",
    )
    render_page_hero(
        "Hazard layer",
        "Risk Intelligence",
        "Flood, wildfire, heatwave, and storm scoring driven by live forecast, AQI, and station context.",
        subtitle="Operational risk scoring with transparent drivers",
    )

    with st.sidebar:
        st.header("Risk controls")
        default_query = st.session_state.get("atlas_ops_location", get_default_location_query())
        location_query = st.text_input("Target location", value=default_query)
        st.session_state["atlas_ops_location"] = location_query
        history_days = st.slider("History lookback", min_value=14, max_value=90, value=45, step=1)

    try:
        location, resolved_weather = resolve_location(location_query)
        weather = resolved_weather or fetch_current_weather(location["lat"], location["lon"])
        forecast_df = fetch_forecast(location["lat"], location["lon"])
        air_current, air_forecast = fetch_air_quality(location["lat"], location["lon"])
        climate_result = fetch_historical_climate_context(location["lat"], location["lon"], days=history_days)
        history_df = climate_result["history"] if climate_result else None
        history_source = climate_result["source"] if climate_result else "No historical source"
    except Exception as exc:
        st.warning(f"Risk Intelligence could not connect to the live stack: {exc}")
        st.info("Add valid API credentials in Settings or use coordinates for the target location.")
        return

    risk_profile = build_risk_profile(weather, forecast_df, air_current, history_df)
    risk_timeline = build_risk_timeline(forecast_df)
    render_info_banner(
        f"Risk scoring for {location['label']} is blending live weather, AQI, forecast progression, and historical context from {history_source}."
    )

    metric_cols = st.columns(5)
    for column, title in zip(metric_cols, ["Heatwave", "Flood", "Wildfire", "Storm", "Composite"]):
        with column:
            if title == "Composite":
                render_metric_card("Composite risk", f"{risk_profile['composite']:.0f}/100", str(risk_profile["composite_label"]))
            else:
                panel = risk_profile["panels"][title]
                render_metric_card(title, f"{panel['score']:.0f}/100", str(panel["label"]))

    top_left, top_right = st.columns((1.15, 0.85))
    with top_left:
        render_section_intro(
            "Risk trajectory",
            "Short-range forecast data is converted into scenario-style risk scores so operators can see direction, not just the latest point.",
            eyebrow="Timeline",
        )
        if risk_timeline.empty:
            st.info("Forecast data is required to build the risk timeline.")
        else:
            st.plotly_chart(_risk_timeline_chart(risk_timeline), use_container_width=True)
    with top_right:
        render_section_intro(
            "Risk mix",
            "The radar chart makes the balance of hazard types easy to understand at a glance.",
            eyebrow="Radar",
        )
        radar_tab, mix_tab = st.tabs(["Radar", "Mix"])
        with radar_tab:
            st.plotly_chart(create_risk_radar(risk_profile["scores"], title="Hazard distribution"), use_container_width=True)
        with mix_tab:
            st.plotly_chart(create_donut_figure(risk_profile["scores"], title="Hazard share"), use_container_width=True)

    mid_left, mid_right = st.columns(2)
    with mid_left:
        render_section_intro(
            "Composite indicator",
            "The gauge turns the full hazard model into a single demo-friendly signal for operators and judges.",
            eyebrow="Indicator",
        )
        st.plotly_chart(
            create_gauge_figure(risk_profile["composite"], title="Composite risk", suffix="/100"),
            use_container_width=True,
        )
    with mid_right:
        render_section_intro(
            "Hazard ranking",
            "Horizontal bars make it easy to see which hazard is dominating the current score profile.",
            eyebrow="Ranking",
        )
        st.plotly_chart(
            create_ranked_bar_figure(risk_profile["scores"], title="Hazard ranking", x_label="Risk score"),
            use_container_width=True,
        )

    alert_col, aq_col = st.columns(2)
    with alert_col:
        render_section_intro(
            "Alert feed",
            "Every alert is rule-based and traceable to the current weather and forecast profile.",
            eyebrow="Alerts",
        )
        if risk_profile["alerts"]:
            for alert in risk_profile["alerts"]:
                render_feature_card("Triggered alert", alert)
        else:
            render_feature_card("No elevated alerts", "Current hazard rules are not flagging major operational concern.")
        if climate_result and history_df is not None and not history_df.empty:
            st.plotly_chart(
                create_station_history_figure(history_df, title=f"{climate_result['station']['name']} station history"),
                use_container_width=True,
            )

    with aq_col:
        render_section_intro(
            "AQI and forecast",
            "Air quality adds a public-health dimension to the broader hazard picture.",
            eyebrow="Health",
        )
        st.plotly_chart(create_forecast_figure(forecast_df, title=f"{location['label']} weather track"), use_container_width=True)
        if not air_forecast.empty:
            st.plotly_chart(create_air_quality_figure(air_forecast, title=f"{location['label']} AQI outlook"), use_container_width=True)


if __name__ == "__main__":
    main()
