from __future__ import annotations

import streamlit as st

from utils.data_loader import detect_axes, get_active_dataset, spatial_mean_series, to_display_array
from utils.live_data import fetch_air_quality, fetch_current_weather, get_default_location_query, resolve_location
from utils.report_builder import build_report_markdown, build_report_pdf
from utils.style import render_app_shell, render_feature_card, render_info_banner, render_metric_card, render_page_hero, render_section_intro


st.set_page_config(page_title="ATLAS | Reports", page_icon=":material/description:", layout="wide")


def main() -> None:
    render_app_shell(
        "Reports",
        "Generate shareable climate briefs with markdown and PDF exports.",
        search_placeholder="Search briefing sections, metrics, or location",
    )
    render_page_hero(
        "Delivery layer",
        "Reports",
        "Build investor-grade or stakeholder-ready climate briefs from the same live and historical data used across the product.",
        subtitle="Report builder, export pipeline, and presentation mode",
    )

    with st.sidebar:
        st.header("Report settings")
        location_query = st.text_input("Location", value=st.session_state.get("atlas_ops_location", get_default_location_query()))
        st.session_state["atlas_ops_location"] = location_query
        report_title = st.text_input("Report title", value="ATLAS Climate Brief")
        presentation_mode = st.toggle("Presentation mode", value=False)

    dataset, label = get_active_dataset()
    temp = to_display_array(dataset["t2m"], "t2m")
    axes = detect_axes(temp)
    global_series = spatial_mean_series(temp, axes, "Global", anomaly_mode=False)
    latest_global = float(global_series.values[-1])

    live_summary = "Live services not available."
    bullets = [
        f"Historical climate baseline source: {label}.",
        f"Latest global temperature mean in the historical workspace: {latest_global:.2f} deg C.",
        "Operational risk and live AQI sections can be added automatically when APIs are connected.",
    ]

    try:
        location, resolved_weather = resolve_location(location_query)
        weather = resolved_weather or fetch_current_weather(location["lat"], location["lon"])
        air_current, _ = fetch_air_quality(location["lat"], location["lon"])
        live_summary = (
            f"{location['label']} is currently {weather['description']} at {weather['temperature_c']:.1f} deg C "
            f"with AQI {air_current['aqi']} ({air_current['category']})."
        )
        bullets.insert(0, live_summary)
        location_label = str(location["label"])
    except Exception:
        location_label = location_query

    source_notes = [
        "OpenWeather powers live weather and AQI when credentials are configured.",
        "NOAA Climate Data Online adds nearby station history in the operational pages.",
        "NASA GIBS provides date-specific satellite imagery overlays.",
        "The bundled NetCDF climate grid keeps the historical workspace and reports online.",
    ]
    markdown_text = build_report_markdown(
        title=report_title,
        location_label=location_label,
        executive_summary=live_summary,
        bullets=bullets,
        source_notes=source_notes,
    )
    pdf_bytes = build_report_pdf(report_title, markdown_text)

    if presentation_mode:
        render_info_banner("Presentation mode is active. The report preview is expanded for screen sharing.")

    metric_cols = st.columns(3)
    with metric_cols[0]:
        render_metric_card("Report title", report_title, "Current report configuration")
    with metric_cols[1]:
        render_metric_card("Location", location_label, "Current report focus")
    with metric_cols[2]:
        render_metric_card("Global baseline", f"{latest_global:.2f} deg C", "Latest historical grid mean")

    render_section_intro(
        "Report preview",
        "The preview below is the same content exported through markdown and PDF download actions.",
        eyebrow="Preview",
    )
    st.markdown(markdown_text)

    export_cols = st.columns(2)
    with export_cols[0]:
        st.download_button(
            "Download markdown report",
            data=markdown_text.encode("utf-8"),
            file_name=f"{report_title.lower().replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with export_cols[1]:
        st.download_button(
            "Download PDF report",
            data=pdf_bytes,
            file_name=f"{report_title.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    render_section_intro(
        "Presentation mode",
        "Use the same briefing content during demos, review meetings, or stakeholder updates without rebuilding it elsewhere.",
        eyebrow="Present",
    )
    render_feature_card("Live summary", "When APIs are connected, the report automatically pulls in the current weather and AQI snapshot.")
    render_feature_card("Historical context", "Every report includes the latest global climate baseline from the bundled or uploaded NetCDF workspace.")
    render_feature_card("Export path", "Reports are available in markdown and PDF so the handoff works both for product and research teams.")


if __name__ == "__main__":
    main()
