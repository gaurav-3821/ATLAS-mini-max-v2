from __future__ import annotations

import streamlit as st

from utils.ai_copilot import generate_prediction_brief, get_openrouter_api_key
from utils.chart_factory import (
    create_anomaly_bar_figure,
    create_forecast_delta_figure,
    create_prediction_figure,
    create_seasonality_bar_figure,
)
from utils.data_loader import REGION_BOUNDS, detect_axes, get_active_dataset, spatial_mean_series, to_display_array
from utils.prediction_engine import build_forecast_frame, compute_model_diagnostics, parse_natural_language_query
from utils.style import render_app_shell, render_feature_card, render_info_banner, render_metric_card, render_page_hero, render_section_intro


st.set_page_config(page_title="ATLAS | AI Predictions", page_icon=":material/auto_graph:", layout="wide")


def main() -> None:
    render_app_shell(
        "Predictions",
        "Model-assisted climate outlooks, anomaly detection, and natural-language signal steering.",
        search_placeholder="Ask about future warming, rainfall, wind, or pressure",
    )
    render_page_hero(
        "Model-assisted outlooks",
        "AI Predictions",
        "Trend and seasonal projections built from the historical climate workspace, with natural-language steering for faster exploration.",
        subtitle="Forecast surfaces for temperature, rainfall, wind, and pressure signals",
    )

    dataset, label = get_active_dataset()
    user_query = st.sidebar.text_area(
        "Natural-language query",
        value="Show the future warming outlook for the Arctic temperature anomaly.",
        height=120,
    )
    parsed = parse_natural_language_query(user_query)
    horizon = st.sidebar.slider("Forecast horizon (months)", min_value=6, max_value=60, value=24, step=6)
    variable = st.sidebar.selectbox(
        "Climate variable",
        ["t2m", "precipitation", "sea_level_pressure", "wind_speed"],
        index=["t2m", "precipitation", "sea_level_pressure", "wind_speed"].index(str(parsed["variable"])),
    )
    region_name = st.sidebar.selectbox(
        "Region",
        list(REGION_BOUNDS.keys()),
        index=list(REGION_BOUNDS.keys()).index(str(parsed["region"])),
    )
    anomaly_mode = st.sidebar.toggle("Forecast anomaly mode", value=bool(parsed["anomaly_mode"]))

    data_array = to_display_array(dataset[variable], variable)
    axes = detect_axes(data_array)
    series = spatial_mean_series(data_array, axes, region_name, anomaly_mode=anomaly_mode)
    observed_df = series.to_dataframe(name="value").reset_index().rename(columns={axes["time"]: "time"})
    forecast_df = build_forecast_frame(observed_df, time_column="time", value_column="value", horizon=horizon)
    diagnostics = compute_model_diagnostics(observed_df, "value")
    projected_change = float(forecast_df["forecast"].iloc[-1] - observed_df["value"].iloc[-1]) if not forecast_df.empty else 0.0

    render_info_banner(
        f"Parsed query -> variable: {variable}, region: {region_name}, anomaly mode: {anomaly_mode}. Source: {label}."
    )

    if get_openrouter_api_key():
        with st.spinner("Generating AI climate brief..."):
            try:
                ai_brief = generate_prediction_brief(user_query, region_name, variable, observed_df.tail(120), forecast_df)
            except Exception as exc:
                ai_brief = f"AI briefing unavailable: {exc}"
        render_feature_card("ATLAS Copilot", ai_brief)
    else:
        render_feature_card("ATLAS Copilot", "Add an OpenRouter API key in server-side secrets to enable a live AI forecast summary.")

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Latest value", f"{diagnostics['latest']:.2f}", f"{region_name} regional mean")
    with metric_cols[1]:
        render_metric_card("Long-run mean", f"{diagnostics['mean']:.2f}", "Historical baseline from selected series")
    with metric_cols[2]:
        render_metric_card("Volatility", f"{diagnostics['volatility']:.2f}", "Standard deviation of observed series")
    with metric_cols[3]:
        render_metric_card("Projected change", f"{projected_change:+.2f}", f"{horizon}-month change vs latest")

    render_section_intro(
        "Prediction surface",
        "ATLAS fits a simple trend-plus-seasonality model so the output remains interpretable and fast to recompute inside the product.",
        eyebrow="Forecast",
    )
    st.plotly_chart(
        create_prediction_figure(
            observed_df=observed_df,
            forecast_df=forecast_df,
            title=f"{region_name} {variable} outlook",
            value_column="value",
            y_label=variable,
        ),
        use_container_width=True,
    )

    top_left, top_right = st.columns(2)
    with top_left:
        render_section_intro(
            "Forecast change bars",
            "Bars surface where the model expects acceleration or cooling from one forecast step to the next.",
            eyebrow="Momentum",
        )
        st.plotly_chart(
            create_forecast_delta_figure(forecast_df, title="Forecast momentum"),
            use_container_width=True,
        )
    with top_right:
        render_section_intro(
            "Seasonal pattern",
            "Monthly average bars explain the recurring seasonal signature that the model is carrying forward.",
            eyebrow="Seasonality",
        )
        st.plotly_chart(
            create_seasonality_bar_figure(
                observed_df,
                title="Observed seasonal pattern",
                value_column="value",
                y_label=variable,
            ),
            use_container_width=True,
        )

    lower_left, lower_right = st.columns((1.1, 0.9))
    with lower_left:
        render_section_intro(
            "Recent signal bars",
            "Recent observations are shown as bars so short-term momentum is easy to compare with the forecast cone above.",
            eyebrow="Observed",
        )
        st.plotly_chart(
            create_anomaly_bar_figure(
                observed_df.tail(30),
                title="Recent observed values",
                value_column="value",
                y_label=variable,
            ),
            use_container_width=True,
        )
        render_section_intro(
            "Natural-language query",
            "The parser maps plain language onto the available historical variables and regions so teams can move faster.",
            eyebrow="Query",
        )
        st.code(
            "\n".join(
                [
                    f"query = {user_query}",
                    f"variable = {parsed['variable']}",
                    f"region = {parsed['region']}",
                    f"anomaly_mode = {parsed['anomaly_mode']}",
                ]
            ),
            language="text",
        )
    with lower_right:
        render_section_intro(
            "Model notes",
            "This release uses an interpretable baseline model instead of a black-box service so teams can trust what changed and why.",
            eyebrow="Model",
        )
        render_feature_card("Forecast model", "Linear trend plus month-of-year seasonal adjustment with widening confidence bounds.")
        render_feature_card("Anomaly detection", "Anomaly mode forecasts the centered signal rather than the absolute field.")
        render_feature_card("Product fit", "Fast enough for interactive work, transparent enough for research handoff.")


if __name__ == "__main__":
    main()
