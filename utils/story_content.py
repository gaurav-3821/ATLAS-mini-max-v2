from __future__ import annotations


STORY_STEPS = [
    {
        "slug": "Baseline",
        "title": "Baseline Climate Window",
        "year_range": ("1951-01-01", "1970-12-01"),
        "variable": "t2m",
        "region": "Global",
        "caption": (
            "This multi-decade average establishes the reference state used throughout the rest of the briefing."
        ),
        "map_type": "heatmap",
        "highlight": None,
    },
    {
        "slug": "El Nino",
        "title": "1997-1998 El Nino Signal",
        "year_range": ("1997-07-01", "1998-12-01"),
        "variable": "t2m",
        "region": "Global",
        "caption": (
            "The 1997-98 El Nino elevated temperatures rapidly and concentrated some of the strongest anomalies in the tropical Pacific."
        ),
        "map_type": "anomaly_map",
        "highlight": "Tropical Pacific focus zone",
    },
    {
        "slug": "Arctic",
        "title": "Arctic Amplification Pattern",
        "year_range": ("2000-01-01", "2023-12-01"),
        "comparison_range": ("1951-01-01", "1970-12-01"),
        "variable": "t2m",
        "region": "Arctic",
        "caption": (
            "The Arctic has warmed faster than the global average. This difference view shows how concentrated that shift has become."
        ),
        "map_type": "difference_map",
        "highlight": "High-latitude warming corridor",
    },
    {
        "slug": "2023",
        "title": "2023 Heat Surge",
        "year_range": ("2023-01-01", "2023-12-01"),
        "variable": "t2m",
        "region": "Global",
        "caption": (
            "The 2023 field makes the accumulated warming signal immediately visible at the global scale."
        ),
        "map_type": "anomaly_map",
        "highlight": None,
    },
]
