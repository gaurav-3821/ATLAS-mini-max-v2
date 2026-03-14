from __future__ import annotations

import streamlit as st

from utils.live_data import (
    NASA_SESSION_KEY,
    NOAA_SESSION_KEY,
    OPENWEATHER_SESSION_KEY,
    get_deferred_integrations,
    get_source_status,
    run_live_diagnostics,
    runtime_credential_entry_enabled,
)
from utils.style import render_app_shell, render_feature_card, render_info_banner, render_page_hero, render_section_intro, render_source_card


st.set_page_config(page_title="ATLAS | Settings", page_icon=":material/settings:", layout="wide")


def _render_diagnostic_cards(results: list[dict[str, str]]) -> None:
    columns = st.columns(3)
    for column, item in zip(columns * 3, results):
        with column:
            render_source_card(item["name"], item["status"], item["detail"])


def main() -> None:
    render_app_shell(
        "Settings",
        "Deployment-safe source configuration, diagnostics, and integration policy for the hackathon build.",
        search_placeholder="Search deployment settings or integration status",
    )
    render_page_hero(
        "Control plane",
        "Settings",
        "This release is tuned for server-side secrets, stable live APIs, and low-friction deployment rather than user-entered credentials in the public UI.",
        subtitle="Deploy-safe configuration and live health checks",
    )

    with st.sidebar:
        st.header("Deploy profile")
        st.caption("The public demo should use server-side secrets or environment variables.")
        if runtime_credential_entry_enabled():
            st.text_input("OpenWeather API key", key=OPENWEATHER_SESSION_KEY, type="password")
            st.text_input("NOAA API token", key=NOAA_SESSION_KEY, type="password")
            st.text_input("NASA Earthdata token", key=NASA_SESSION_KEY, type="password")
            st.caption("Runtime key entry is enabled for local development.")
        else:
            st.success("Runtime key entry is disabled.")
            st.caption("This keeps credentials out of the public interface during deployment.")

    render_info_banner(
        "ATLAS now defaults to server-side secrets only. Enable runtime credential inputs only for local development by setting ATLAS_ENABLE_RUNTIME_CREDENTIAL_INPUTS=true."
    )

    render_section_intro(
        "Deployable source status",
        "Only the integrations that are reliable enough for a public hackathon demo are surfaced as active sources.",
        eyebrow="Status",
    )
    _render_diagnostic_cards(get_source_status())

    render_section_intro(
        "Live diagnostics",
        "Run a real connectivity check against the configured providers before deployment so you know exactly what will work on stage.",
        eyebrow="Health",
    )
    if st.button("Run live diagnostics", use_container_width=True):
        with st.spinner("Checking live providers..."):
            st.session_state["atlas_live_diagnostics"] = run_live_diagnostics()

    diagnostic_results = st.session_state.get("atlas_live_diagnostics")
    if diagnostic_results:
        _render_diagnostic_cards(diagnostic_results)
    else:
        render_feature_card(
            "Diagnostics ready",
            "Trigger the health check to validate OpenWeather, NOAA, and NASA GIBS against the current server-side configuration.",
        )

    render_section_intro(
        "Deferred integrations",
        "Some integrations were intentionally kept out of the deploy profile because they add setup complexity without improving demo reliability.",
        eyebrow="Scope",
    )
    for item in get_deferred_integrations():
        render_feature_card(item["name"], item["detail"])

    render_section_intro(
        "Deployment secrets",
        "Use these server-side variables for local testing or hosted deployment. The hackathon build only needs OpenWeather and NOAA keys for the live data paths.",
        eyebrow="Secrets",
    )
    st.code(
        "\n".join(
            [
                "OPENWEATHER_API_KEY=<your key>",
                "NOAA_API_TOKEN=<your token>",
                "ATLAS_DEFAULT_LOCATION=New Delhi, IN",
                "ATLAS_ENABLE_RUNTIME_CREDENTIAL_INPUTS=false",
            ]
        ),
        language="bash",
    )

    render_section_intro(
        "Integration notes",
        "NASA imagery stays live without a frontend key, while the historical workspace continues to function even if live providers are temporarily unavailable.",
        eyebrow="Notes",
    )
    render_feature_card("OpenWeatherMap", "Used for current conditions, short-range forecast, and air-quality intelligence with a single backend key.")
    render_feature_card("NOAA Climate API", "Used for nearby station lookup and recent daily observations where the station network has coverage.")
    render_feature_card("NASA GIBS", "Used for satellite imagery overlays without exposing credentials in the public UI.")


if __name__ == "__main__":
    main()
