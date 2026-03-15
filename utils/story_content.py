from __future__ import annotations


STORY_MODE_CONFIG = {
    "feature": "ATLAS Story Mode",
    "data_sources": {
        "global_temperature": {
            "source": "NASA GISTEMP",
            "type": "timeseries",
            "years": [1900, 1920, 1940, 1960, 1980, 2000, 2010, 2020, 2023],
            "temperature_anomaly_c": [-0.12, -0.08, -0.02, 0.01, 0.18, 0.42, 0.63, 0.85, 1.02],
        },
        "arctic_amplification": {
            "source": "NASA Arctic temperature anomaly",
            "regions": ["Global", "Arctic"],
            "anomaly_c": {
                "Global": [0.1, 0.2, 0.35, 0.5, 0.7, 1.0],
                "Arctic": [0.3, 0.6, 1.0, 1.6, 2.1, 2.8],
            },
            "years": [1970, 1980, 1990, 2000, 2010, 2023],
        },
        "extreme_events": {
            "source": "NOAA severe weather dataset",
            "events": [
                {"year": 1980, "events": 120},
                {"year": 1990, "events": 180},
                {"year": 2000, "events": 260},
                {"year": 2010, "events": 420},
                {"year": 2020, "events": 610},
            ],
        },
        "future_projection": {
            "source": "IPCC CMIP6 projections",
            "scenarios": {
                "low_emissions": {
                    "years": [2020, 2040, 2060, 2080, 2100],
                    "warming_c": [1.2, 1.4, 1.6, 1.7, 1.8],
                },
                "medium_emissions": {
                    "years": [2020, 2040, 2060, 2080, 2100],
                    "warming_c": [1.2, 1.8, 2.4, 2.9, 3.2],
                },
                "high_emissions": {
                    "years": [2020, 2040, 2060, 2080, 2100],
                    "warming_c": [1.2, 2.3, 3.4, 4.3, 5.1],
                },
            },
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
                "text": "Global temperatures have increased dramatically over the past century. The warming signal now appears in nearly every basin and continent.",
                "ai_insight": "Recent decades contain the warmest years in the instrument record.",
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
                "text": "Polar regions warm faster than the global average due to feedback mechanisms such as sea-ice loss.",
                "ai_insight": "Arctic temperatures rise several times faster than the global mean.",
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
                "text": "The frequency of heatwaves, storms, and extreme weather events has increased globally.",
                "ai_insight": "Operational climate risk is no longer episodic. It is now persistent across decades.",
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
                "text": "Climate models simulate potential warming depending on emissions scenarios.",
                "ai_insight": "Emissions choices made this decade strongly shape late-century warming outcomes.",
            },
        },
    ],
}
