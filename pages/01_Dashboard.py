from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.chart_factory import (
    create_air_quality_figure,
    create_anomaly_bar_figure,
    create_donut_figure,
    create_forecast_delta_figure,
    create_forecast_figure,
    create_gauge_figure,
    create_ranked_bar_figure,
    create_risk_radar,
    create_station_history_figure,
    create_timeline_figure,
)
from utils.data_loader import detect_axes, get_active_dataset, spatial_mean_series, to_display_array
from utils.live_data import fetch_air_quality, fetch_forecast, fetch_noaa_station_history, fetch_current_weather, get_default_location_query, resolve_location
from utils.risk_engine import build_risk_profile
from utils.style import render_app_shell, render_feature_card, render_info_banner, render_metric_card, render_page_hero, render_section_intro


st.set_page_config(page_title="ATLAS | Dashboard", page_icon=":material/dashboard:", layout="wide")


def main() -> None:
    render_app_shell(
        "Dashboard",
        "Global KPI summary, live location monitoring, and top-line climate risk signals.",
        search_placeholder="Search a city, signal, or climate KPI",
    )
    render_page_hero(
        "Mission control",
        "Dashboard",
        "A premium control surface for live weather, historical climate context, and risk signals.",
        subtitle="Live metrics, alerts, and long-range climate context",
    )

    with st.sidebar:
        st.header("Operational inputs")
        default_query = st.session_state.get("atlas_ops_location", get_default_location_query())
        location_query = st.text_input("Tracked location", value=default_query)
        st.session_state["atlas_ops_location"] = location_query
        history_days = st.slider("NOAA history window", min_value=14, max_value=90, value=45, step=1)

    dataset, source_label = get_active_dataset()
    data_array = to_display_array(dataset["t2m"], "t2m")
    axes = detect_axes(data_array)
    global_series = spatial_mean_series(data_array, axes, "Global", anomaly_mode=False)
    global_df = global_series.to_dataframe(name="temperature").reset_index().rename(columns={axes["time"]: "time"})
    recent_anomaly = float(global_df["temperature"].iloc[-1] - global_df["temperature"].tail(120).mean())
    anomaly_baseline = float(global_df["temperature"].tail(min(len(global_df), 240)).mean())
    anomaly_bars = global_df.tail(24).copy()
    anomaly_bars["anomaly"] = anomaly_bars["temperature"] - anomaly_baseline

    location = None
    weather = None
    forecast_df = pd.DataFrame()
    air_current = None
    air_forecast = pd.DataFrame()
    noaa_result = None
    live_error = None

    try:
        location, resolved_weather = resolve_location(location_query)
        weather = resolved_weather or fetch_current_weather(location["lat"], location["lon"])
        forecast_df = fetch_forecast(location["lat"], location["lon"])
        air_current, air_forecast = fetch_air_quality(location["lat"], location["lon"])
        try:
            noaa_result = fetch_noaa_station_history(location["lat"], location["lon"], days=history_days)
        except Exception:
            noaa_result = None
    except Exception as exc:
        live_error = str(exc)

    risk_profile = build_risk_profile(
        weather or {"temperature_c": 0.0, "humidity_pct": 0.0, "wind_mps": 0.0, "pressure_hpa": 1013.0},
        forecast_df,
        air_current or {"aqi": 1, "pm2_5": 0.0},
        noaa_result["history"] if noaa_result else None,
    )

    if live_error:
        render_info_banner(
            f"Live operations are not fully connected for '{location_query}'. Historical climate analytics remain active. Details: {live_error}"
        )
    else:
        render_info_banner(
            f"Tracking {location['label']} with live weather, AQI, and station context layered over the historical climate baseline from {source_label}."
        )

    metric_cols = st.columns(5)
    with metric_cols[0]:
        render_metric_card("Global temperature", f"{global_df['temperature'].iloc[-1]:.2f} deg C", "Latest historical grid mean")
    with metric_cols[1]:
        if weather:
            render_metric_card("Tracked city", f"{weather['temperature_c']:.1f} deg C", str(location["label"]))
        else:
            render_metric_card("Tracked city", "API ready", "Connect OpenWeather or use coordinates")
    with metric_cols[2]:
        if air_current:
            render_metric_card("Air quality", f"AQI {air_current['aqi']}", str(air_current["category"]))
        else:
            render_metric_card("Air quality", "API ready", "AQI becomes available with OpenWeather")
    with metric_cols[3]:
        render_metric_card("Climate anomaly", f"{recent_anomaly:+.2f} deg C", "Relative to the trailing 10-year mean")
    with metric_cols[4]:
        render_metric_card("Risk index", f"{risk_profile['composite']:.0f}/100", str(risk_profile["composite_label"]))

    render_section_intro(
        "Executive surface",
        "Top-level views combine live forecast dynamics with long-range global context.",
        eyebrow="Overview",
    )
    top_left, top_right = st.columns((1.18, 0.82))
    with top_left:
        st.plotly_chart(
            create_timeline_figure(
                global_df,
                title="Global activity timeline",
                value_column="temperature",
                y_label="Global mean temperature (deg C)",
            ),
            use_container_width=True,
        )
    with top_right:
        radar_tab, mix_tab = st.tabs(["Radar", "Mix"])
        with radar_tab:
            st.plotly_chart(
                create_risk_radar(risk_profile["scores"], title="Risk intelligence radar"),
                use_container_width=True,
            )
        with mix_tab:
            st.plotly_chart(
                create_donut_figure(risk_profile["scores"], title="Hazard share"),
                use_container_width=True,
            )

    chart_left, chart_mid, chart_right = st.columns(3)
    with chart_left:
        render_section_intro(
            "Composite risk gauge",
            "A single dial makes the overall operational climate posture easy to read during a fast demo.",
            eyebrow="Indicator",
        )
        st.plotly_chart(
            create_gauge_figure(risk_profile["composite"], title="Composite risk", suffix="/100"),
            use_container_width=True,
        )
    with chart_mid:
        render_section_intro(
            "Hazard ranking",
            "Ranked bars make it obvious which hazard is leading instead of hiding the signal in cards alone.",
            eyebrow="Ranking",
        )
        st.plotly_chart(
            create_ranked_bar_figure(risk_profile["scores"], title="Hazard scores", x_label="Risk score"),
            use_container_width=True,
        )
    with chart_right:
        render_section_intro(
            "Recent anomaly bars",
            "Monthly bars make short-term warming or cooling easier to read than a line alone.",
            eyebrow="Anomaly",
        )
        st.plotly_chart(
            create_anomaly_bar_figure(
                anomaly_bars[["time", "anomaly"]],
                title="Global anomaly bars",
                value_column="anomaly",
                y_label="Temperature anomaly (deg C)",
            ),
            use_container_width=True,
        )

    alerts_col, forecast_col = st.columns((0.82, 1.18))
    with alerts_col:
        render_section_intro(
            "Extreme weather alerts",
            "Risk panels synthesize live weather, forecast progression, station history, and AQI.",
            eyebrow="Alerts",
        )
        for title, panel in risk_profile["panels"].items():
            render_feature_card(title, f"Score {panel['score']:.0f}/100 - {panel['label']}")
        if risk_profile["alerts"]:
            for alert in risk_profile["alerts"]:
                render_info_banner(alert)
        else:
            render_info_banner("No elevated climate risk signals were triggered by the current ruleset.")

    with forecast_col:
        render_section_intro(
            "Forecast track",
            "OpenWeather three-hour forecasts feed the short-range operational outlook.",
            eyebrow="Nowcasting",
        )
        if forecast_df.empty:
            st.info("Forecast data is unavailable until a valid live location is resolved.")
        else:
            st.plotly_chart(
                create_forecast_figure(forecast_df, title=f"{location['label']} forecast"),
                use_container_width=True,
            )
            st.plotly_chart(
                create_forecast_delta_figure(forecast_df, title="Forecast change bars"),
                use_container_width=True,
            )

    lower_left, lower_right = st.columns(2)
    with lower_left:
        render_section_intro(
            "Air quality stack",
            "AQI and particulate trends provide a direct health-risk layer for the tracked location.",
            eyebrow="AQI",
        )
        if air_forecast.empty:
            st.info("Air quality forecast is unavailable for the current location.")
        else:
            st.plotly_chart(
                create_air_quality_figure(air_forecast, title=f"{location['label']} air quality"),
                use_container_width=True,
            )

    with lower_right:
        render_section_intro(
            "Ground truth",
            "Nearby NOAA station history helps ground the short-range dashboard in observed conditions.",
            eyebrow="Station",
        )
        if noaa_result and not noaa_result["history"].empty:
            station = noaa_result["station"]
            st.plotly_chart(
                create_station_history_figure(noaa_result["history"], title=f"{station['name']} recent history"),
                use_container_width=True,
            )
        else:
            st.info("NOAA station data is unavailable or no daily summaries were returned for the selected window.")


if __name__ == "__main__":
    main()
