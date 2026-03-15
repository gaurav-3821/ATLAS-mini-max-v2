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
    create_live_signal_figure,
    create_ranked_bar_figure,
    create_risk_timeline_figure,
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
        "A premium control surface for live weather, historical climate context, and risk signals focused on Delhi operations by default.",
        subtitle="Delhi live metrics, alerts, and long-range climate context",
    )

    with st.sidebar:
        st.header("Operational inputs")
        default_query = st.session_state.get("atlas_ops_location", "Delhi, IN")
        location_query = st.text_input("Tracked location", value=default_query)
        st.session_state["atlas_ops_location"] = location_query
        history_days = st.slider("History window", min_value=14, max_value=120, value=60, step=1)

    location = None
    weather = None
    forecast_df = pd.DataFrame()
    air_current = None
    air_forecast = pd.DataFrame()
    climate_result = None
    live_error = None

    try:
        location, resolved_weather = resolve_location(location_query)
        weather = resolved_weather or fetch_current_weather(location["lat"], location["lon"])
        forecast_df = fetch_forecast(location["lat"], location["lon"])
        air_current, air_forecast = fetch_air_quality(location["lat"], location["lon"])
        try:
            climate_result = fetch_historical_climate_context(location["lat"], location["lon"], days=history_days)
        except Exception:
            climate_result = None
    except Exception as exc:
        live_error = str(exc)

    history_df = climate_result["history"] if climate_result else pd.DataFrame()
    history_source = climate_result["source"] if climate_result else "No historical source"
    current_temp = float(weather["temperature_c"]) if weather else 0.0
    current_humidity = float(weather["humidity_pct"]) if weather else 0.0
    current_wind = float(weather["wind_mps"]) if weather else 0.0
    current_pressure = float(weather["pressure_hpa"]) if weather else 0.0
    recent_mean = float(history_df["TAVG"].dropna().mean()) if not history_df.empty and "TAVG" in history_df else current_temp
    recent_max = float(history_df["TMAX"].dropna().max()) if not history_df.empty and "TMAX" in history_df else current_temp
    recent_min = float(history_df["TMIN"].dropna().min()) if not history_df.empty and "TMIN" in history_df else current_temp
    recent_rain = float(history_df["PRCP"].fillna(0).tail(7).sum()) if not history_df.empty and "PRCP" in history_df else 0.0
    heat_departure = current_temp - recent_mean

    anomaly_bars = pd.DataFrame(columns=["time", "anomaly"])
    if not history_df.empty and {"date", "TAVG"}.issubset(history_df.columns):
        anomaly_bars = history_df[["date", "TAVG"]].copy().rename(columns={"date": "time"})
        anomaly_bars["anomaly"] = anomaly_bars["TAVG"] - recent_mean

    risk_profile = build_risk_profile(
        weather or {"temperature_c": 0.0, "humidity_pct": 0.0, "wind_mps": 0.0, "pressure_hpa": 1013.0},
        forecast_df,
        air_current or {"aqi": 1, "pm2_5": 0.0},
        history_df if not history_df.empty else None,
    )
    risk_timeline = build_risk_timeline(forecast_df)

    if live_error:
        render_info_banner(
            f"Live operations are not fully connected for '{location_query}'. Historical climate analytics remain active. Details: {live_error}"
        )
    else:
        render_info_banner(
            f"Tracking {location['label']} with live OpenWeather signals and historical Delhi context from {history_source}."
        )
    render_feature_card("Operational target", f"Primary dashboard context is pinned to {location['label'] if location else 'Delhi, IN'} so the live and historical views point to the same place.")

    metric_cols = st.columns(5)
    with metric_cols[0]:
        render_metric_card("Delhi current temp", f"{current_temp:.1f} deg C", str(location["label"]) if location else "Delhi, IN")
    with metric_cols[1]:
        render_metric_card("Feels like humidity", f"{current_humidity:.0f}%", "Current relative humidity")
    with metric_cols[2]:
        if air_current:
            render_metric_card("Air quality", f"AQI {air_current['aqi']}", str(air_current["category"]))
        else:
            render_metric_card("Air quality", "API ready", "AQI becomes available with OpenWeather")
    with metric_cols[3]:
        render_metric_card("Heat departure", f"{heat_departure:+.1f} deg C", f"Vs last {history_days} days mean")
    with metric_cols[4]:
        render_metric_card("Risk index", f"{risk_profile['composite']:.0f}/100", str(risk_profile["composite_label"]))

    render_section_intro(
        "Executive surface",
        "Top-level views now center on real Delhi forecast dynamics, air quality, and risk progression instead of treating Delhi as a side input.",
        eyebrow="Overview",
    )
    top_left, top_right = st.columns((1.18, 0.82))
    with top_left:
        if not forecast_df.empty and location:
            st.plotly_chart(
                create_live_signal_figure(forecast_df, title=f"{location['label']} live signal ribbon"),
                use_container_width=True,
            )
        else:
            st.info("Live forecast data is unavailable for the selected location.")
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
            "Risk pulse timeline",
            "Stacked risk curves make the next Delhi forecast window feel more operational and easier to scan at a glance.",
            eyebrow="Pulse",
        )
        if not risk_timeline.empty:
            st.plotly_chart(
                create_risk_timeline_figure(risk_timeline, title="Delhi forecast risk pulse"),
                use_container_width=True,
            )
        else:
            if not anomaly_bars.empty:
                st.plotly_chart(
                    create_anomaly_bar_figure(
                        anomaly_bars[["time", "anomaly"]],
                        title="Delhi daily mean departures",
                        value_column="anomaly",
                        y_label="Departure (deg C)",
                    ),
                    use_container_width=True,
                )
            else:
                st.info("Historical departure bars are unavailable for the selected location.")

    alerts_col, forecast_col = st.columns((0.82, 1.18))
    with alerts_col:
        render_section_intro(
            "Extreme weather alerts",
            "Risk panels synthesize live Delhi weather, forecast progression, historical city context, and AQI.",
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
            "OpenWeather three-hour forecasts feed the short-range Delhi outlook with smoother chart styling and clearer change signals.",
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
            "AQI and particulate trends provide a direct Delhi health-risk layer using the live air-pollution feed.",
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
            "Observed climate context",
            "Historical daily temperature and rainfall now use a real Delhi-area archive before any fallback is considered.",
            eyebrow="History",
        )
        if climate_result and not climate_result["history"].empty:
            station = climate_result["station"]
            render_feature_card(
                "Historical source",
                f"{history_source} centered near {station['latitude']:.2f}, {station['longitude']:.2f}. Recent max {recent_max:.1f} deg C, min {recent_min:.1f} deg C, rainfall last 7 days {recent_rain:.1f} mm.",
            )
            st.plotly_chart(
                create_station_history_figure(climate_result["history"], title=f"{station['name']} recent history"),
                use_container_width=True,
            )
        else:
            st.info("Historical Delhi climate data is unavailable for the selected window.")


if __name__ == "__main__":
    main()
