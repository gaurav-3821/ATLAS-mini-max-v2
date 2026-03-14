from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.chart_factory import create_globe, create_heatmap, create_prediction_figure, create_spatial_map, create_time_series
from utils.data_loader import detect_axes, get_active_dataset, period_mean, prepare_map_slice, spatial_mean_series, to_display_array
from utils.prediction_engine import build_forecast_frame
from utils.story_content import STORY_STEPS
from utils.style import render_app_shell, render_feature_card, render_info_banner, render_page_hero, render_section_intro, render_story_stepper


st.set_page_config(page_title="ATLAS | Story Mode", page_icon=":material/play_circle:", layout="wide")


def _story_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"event": "Delhi heat wave", "lat": 28.61, "lon": 77.21, "severity": 92},
            {"event": "Pacific marine heat", "lat": 0.0, "lon": 210.0, "severity": 84},
            {"event": "Arctic thaw zone", "lat": 77.0, "lon": 40.0, "severity": 88},
            {"event": "Mediterranean drought", "lat": 39.0, "lon": 15.0, "severity": 73},
            {"event": "Atlantic storm corridor", "lat": 22.0, "lon": 305.0, "severity": 78},
        ]
    )


def _build_projection_frames(base_slice):
    low = base_slice + 0.8
    medium = base_slice + 1.6
    high = base_slice + 2.8
    return {"low_emissions": low, "medium_emissions": medium, "high_emissions": high}


def _render_event_map(base_slice, axes, title: str):
    figure = create_globe(base_slice, axes, title=title, colorscale="Turbo", colorbar_title="deg C")
    events = _story_events()
    lat_r = np.deg2rad(events["lat"].astype(float).to_numpy())
    lon_r = np.deg2rad(events["lon"].astype(float).to_numpy())
    radius = 1.03
    figure.add_scatter3d(
        x=radius * np.cos(lat_r) * np.cos(lon_r),
        y=radius * np.cos(lat_r) * np.sin(lon_r),
        z=radius * np.sin(lat_r),
        mode="markers+text",
        marker=dict(size=events["severity"] / 8.0, color=events["severity"], colorscale="YlOrRd", line=dict(color="#FFFFFF", width=1)),
        text=events["event"],
        textposition="top center",
        hovertemplate="%{text}<br>Severity %{marker.color:.0f}<extra></extra>",
        name="Extreme events",
    )
    return figure


def main() -> None:
    render_app_shell(
        "Story Mode",
        "An interactive climate narrative that moves from global warming context to regional signals, extreme events, and future scenarios.",
        search_placeholder="Search story scenes or climate narratives",
    )
    render_page_hero(
        "Interactive narrative",
        "ATLAS Story Mode",
        "A guided climate story built as a split-screen experience with chapter navigation, AI insight callouts, and cinematic climate visuals.",
        subtitle="Guided timeline scenes with maps, charts, and scenario projections",
    )

    dataset, label = get_active_dataset()
    scene_index = st.session_state.get("atlas_story_scene_index", 0)

    control_cols = st.columns((1, 1, 1, 1, 3))
    with control_cols[0]:
        if st.button("Previous", use_container_width=True, disabled=scene_index == 0):
            scene_index = max(scene_index - 1, 0)
            st.session_state["atlas_story_scene_index"] = scene_index
            st.rerun()
    with control_cols[1]:
        if st.button("Next", use_container_width=True, disabled=scene_index == len(STORY_STEPS) - 1):
            scene_index = min(scene_index + 1, len(STORY_STEPS) - 1)
            st.session_state["atlas_story_scene_index"] = scene_index
            st.rerun()
    with control_cols[2]:
        paused = st.toggle("Pause", key="atlas_story_pause")
    with control_cols[3]:
        if st.button("Exit", use_container_width=True):
            st.switch_page("app.py")
    with control_cols[4]:
        st.progress((scene_index + 1) / len(STORY_STEPS), text=f"Chapter {scene_index + 1} of {len(STORY_STEPS)}")

    render_story_stepper(STORY_STEPS, scene_index)
    selected_slug = st.radio(
        "Chapter navigation",
        options=list(range(len(STORY_STEPS))),
        index=scene_index,
        format_func=lambda idx: STORY_STEPS[idx]["title"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected_slug != scene_index:
        st.session_state["atlas_story_scene_index"] = selected_slug
        st.rerun()

    step = STORY_STEPS[scene_index]
    data_array = to_display_array(dataset[step["variable"]], step["variable"])
    axes = detect_axes(data_array)
    start_date, end_date = step["year_range"]
    base_slice = period_mean(data_array, axes, pd.Timestamp(start_date), pd.Timestamp(end_date), step["region"])
    colorbar_title = str(data_array.attrs.get("units", step["variable"]))

    left_col, right_col = st.columns((0.42, 0.58))
    with left_col:
        render_section_intro("Chapter", "Narrative context, AI interpretation, and scene controls live on the left panel.", eyebrow="Story")
        render_feature_card(step["title"], step["narrative_text"])
        render_info_banner(f"AI insight: {step['ai_insight']}")
        render_feature_card("Scene source", f"Using {label} as the narrative data fabric for this scene.")
        render_feature_card("Playback state", "Paused" if paused else "Ready for manual scene stepping")
        if "scenarios" in step:
            render_feature_card("Scenario set", ", ".join(step["scenarios"]).replace("_", " "))

    with right_col:
        render_section_intro("Visualization canvas", "The right panel reuses climate views dynamically depending on the active chapter.", eyebrow="Visual")
        if step["visual_component"] == "heatmap_layer":
            st.plotly_chart(
                create_spatial_map(
                    base_slice,
                    axes,
                    title=f"{step['title']} ({pd.Timestamp(end_date).year})",
                    colorscale="RdBu_r",
                    colorbar_title=colorbar_title,
                    projection="Orbital map",
                ),
                use_container_width=True,
            )
        elif step["visual_component"] == "3d_globe":
            comparison_start, comparison_end = step["comparison_range"]
            comparison_slice = period_mean(data_array, axes, pd.Timestamp(comparison_start), pd.Timestamp(comparison_end), step["region"])
            st.plotly_chart(
                create_globe(
                    base_slice - comparison_slice,
                    axes,
                    title=step["title"],
                    colorscale="RdBu_r",
                    colorbar_title=f"Delta {colorbar_title}",
                ),
                use_container_width=True,
            )
        elif step["visual_component"] == "line_chart":
            series = spatial_mean_series(data_array, axes, step["region"], anomaly_mode=False)
            series_df = series.to_dataframe(name="value").reset_index().rename(columns={axes["time"]: "time"})
            trend_df = series_df[["time", "value"]].rename(columns={"value": "trend"})
            st.plotly_chart(
                create_time_series(
                    series_df=series_df,
                    value_column="value",
                    trend_df=trend_df,
                    anomaly_mask=None,
                    title=step["title"],
                    y_label=colorbar_title,
                ),
                use_container_width=True,
            )
        elif step["visual_component"] == "event_markers":
            st.plotly_chart(_render_event_map(base_slice, axes, step["title"]), use_container_width=True)
        elif step["visual_component"] == "projection_map":
            frames = _build_projection_frames(base_slice)
            scenario_name = st.segmented_control(
                "Scenario",
                options=list(frames.keys()),
                default="medium_emissions",
                format_func=lambda value: value.replace("_", " ").title(),
            )
            forecast_series = spatial_mean_series(data_array, axes, "Global", anomaly_mode=False)
            observed_df = forecast_series.to_dataframe(name="value").reset_index().rename(columns={axes["time"]: "time"})
            forecast_df = build_forecast_frame(observed_df, time_column="time", value_column="value", horizon=36)
            st.plotly_chart(
                create_spatial_map(
                    frames[scenario_name],
                    axes,
                    title=f"{step['title']} - {scenario_name.replace('_', ' ').title()}",
                    colorscale="Turbo",
                    colorbar_title=colorbar_title,
                    projection="Projection map",
                ),
                use_container_width=True,
            )
            st.plotly_chart(
                create_prediction_figure(
                    observed_df=observed_df.tail(120),
                    forecast_df=forecast_df,
                    title="Global temperature pathway",
                    value_column="value",
                    y_label=colorbar_title,
                ),
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
