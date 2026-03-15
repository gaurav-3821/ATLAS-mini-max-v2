from __future__ import annotations


STORY_MODE_CONFIG = {
    "feature": "ATLAS Story Mode",
    "data_sources": {
        "global_temperature": {
            "source": "NASA GISTEMP",
            "type": "timeseries",
            "description": "NASA GISS global land-ocean temperature index",
        },
        "arctic_amplification": {
            "source": "NASA GISTEMP zonal annual anomalies",
            "description": "Global mean compared with the Arctic 64N-90N band",
        },
        "extreme_events": {
            "source": "NOAA NCEI U.S. Billion-Dollar Weather and Climate Disasters",
            "description": "Decadal annual averages plus current-decade average through 2024",
        },
        "future_projection": {
            "source": "IPCC CMIP6 projections",
            "description": "Illustrative AR6 scenario warming levels relative to 1850-1900",
        },
    },
    "story_steps": [
        {
            "id": "warming_overview",
            "title": "A Planet That Is Warming",
            "visual_panel": {
                "component": "heatmap + line_chart",
                "data_source": "global_temperature",
                "render_location": "right_visual_canvas",
            },
            "narrative_panel": {
                "location": "below_visual_panel",
                "text": "Global temperatures have increased markedly over the past century, with the strongest rise concentrated in recent decades.",
                "ai_insight": "NASA GISTEMP now shows 2024 at about +1.28 deg C above the late-19th-century baseline, above 2023 and far above early 20th-century values.",
            },
        },
        {
            "id": "regional_patterns",
            "title": "Warming Is Not Equal Everywhere",
            "visual_panel": {
                "component": "comparison_chart",
                "data_source": "arctic_amplification",
                "render_location": "right_visual_canvas",
            },
            "narrative_panel": {
                "location": "below_visual_panel",
                "text": "Polar regions warm faster than the global average because sea-ice loss, snow feedbacks, and circulation changes amplify the signal.",
                "ai_insight": "The Arctic anomaly in NASA's zonal record is several times larger than the global mean in recent decades.",
            },
        },
        {
            "id": "temperature_trend",
            "title": "Climate Change Over Time",
            "visual_panel": {
                "component": "line_chart",
                "data_source": "global_temperature",
                "render_location": "right_visual_canvas",
            },
            "narrative_panel": {
                "location": "below_visual_panel",
                "text": "Temperature anomalies reveal a steady upward trend since the mid-20th century.",
                "ai_insight": "The long-run trend line makes the modern warming regime unmistakable.",
            },
        },
        {
            "id": "extreme_events",
            "title": "More Frequent Extreme Events",
            "visual_panel": {
                "component": "bar_chart",
                "data_source": "extreme_events",
                "render_location": "right_visual_canvas",
            },
            "narrative_panel": {
                "location": "below_visual_panel",
                "text": "NOAA's U.S. billion-dollar disaster record shows a strong increase in costly extreme events compared with the 1980s baseline.",
                "ai_insight": "This is a U.S.-specific indicator, not a global event count, so the chart now labels that scope clearly.",
            },
        },
        {
            "id": "future_projection",
            "title": "Future Climate Scenarios",
            "visual_panel": {
                "component": "scenario_projection_chart",
                "data_source": "future_projection",
                "render_location": "right_visual_canvas",
            },
            "narrative_panel": {
                "location": "below_visual_panel",
                "text": "IPCC AR6 scenarios show that late-century warming depends strongly on future emissions choices.",
                "ai_insight": "Lower-emissions pathways flatten the curve near the upper-1-degree range, while higher-emissions pathways continue toward multi-degree warming by 2100.",
            },
        },
    ],
}
