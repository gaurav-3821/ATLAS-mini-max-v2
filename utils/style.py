from __future__ import annotations

from datetime import datetime, timezone
import html

import streamlit as st


NAV_ITEMS = [
    {"label": "Story Mode", "path": "pages/00_Story_Mode.py", "icon": ":material/play_circle:"},
    {"label": "Dashboard", "path": "pages/01_Dashboard.py", "icon": ":material/dashboard:"},
    {"label": "Global Map", "path": "pages/02_Global_Climate_Map.py", "icon": ":material/public:"},
    {"label": "Climate Signals", "path": "pages/03_Climate_Signals.py", "icon": ":material/query_stats:"},
    {"label": "Risk Intelligence", "path": "pages/04_Risk_Intelligence.py", "icon": ":material/warning:"},
    {"label": "Predictions", "path": "pages/05_AI_Predictions.py", "icon": ":material/auto_graph:"},
    {"label": "Data Explorer", "path": "pages/06_Data_Explorer.py", "icon": ":material/travel_explore:"},
    {"label": "Research Lab", "path": "pages/07_Research_Lab.py", "icon": ":material/science:"},
    {"label": "Reports", "path": "pages/08_Reports.py", "icon": ":material/description:"},
    {"label": "Settings", "path": "pages/09_Settings.py", "icon": ":material/settings:"},
]


THEMES = {
    "dark": {
        "bg_primary": "#0B0F1A",
        "bg_secondary": "#111827",
        "card_bg": "rgba(21, 26, 46, 0.86)",
        "card_glass": "rgba(17, 24, 39, 0.72)",
        "border": "#000000",
        "cyan": "#00E5FF",
        "yellow": "#FFD84D",
        "green": "#6EFF9A",
        "pink": "#FF5C8A",
        "text": "#FFFFFF",
        "muted": "#9CA3AF",
        "shadow_hard": "6px 6px 0px #000000",
        "shadow_soft": "0 10px 30px rgba(0,0,0,0.25)",
        "grid_line": "rgba(255,255,255,0.04)",
        "app_background": """
            radial-gradient(circle at 14% 18%, rgba(0,229,255,0.12), transparent 24%),
            radial-gradient(circle at 88% 10%, rgba(255,92,138,0.12), transparent 20%),
            radial-gradient(circle at 50% 100%, rgba(110,255,154,0.08), transparent 26%),
            linear-gradient(180deg, #09101d 0%, #0b0f1a 42%, #101827 100%)
        """,
        "button_bg": "linear-gradient(135deg, #12233a 0%, #0f172a 100%)",
        "button_text": "#FFFFFF",
        "button_border": "rgba(0,229,255,0.28)",
        "input_bg": "rgba(17,24,39,0.92)",
        "input_text": "#FFFFFF",
        "sidebar_bg": "linear-gradient(180deg, rgba(11,15,26,0.96) 0%, rgba(17,24,39,0.97) 100%)",
        "hero_bg": """
            radial-gradient(circle at top right, rgba(0,229,255,0.14), transparent 32%),
            radial-gradient(circle at 18% 0%, rgba(255,92,138,0.12), transparent 20%),
            linear-gradient(135deg, rgba(21,26,46,0.98) 0%, rgba(11,15,26,1) 100%)
        """,
    },
    "light": {
        "bg_primary": "#F6F7FF",
        "bg_secondary": "#FFFFFF",
        "card_bg": "rgba(255, 255, 255, 0.96)",
        "card_glass": "rgba(255, 255, 255, 0.92)",
        "border": "#000000",
        "cyan": "#5AD7FF",
        "yellow": "#FFD84D",
        "green": "#7FFFA1",
        "pink": "#FF6B9A",
        "text": "#000000",
        "muted": "#374151",
        "shadow_hard": "6px 6px 0px #000000",
        "shadow_soft": "0 10px 30px rgba(0,0,0,0.10)",
        "grid_line": "rgba(0,0,0,0.05)",
        "app_background": """
            radial-gradient(circle at 16% 18%, rgba(90,215,255,0.18), transparent 24%),
            radial-gradient(circle at 84% 12%, rgba(255,107,154,0.16), transparent 22%),
            linear-gradient(180deg, #fffdf5 0%, #f6f7ff 48%, #eef6ff 100%)
        """,
        "button_bg": "#FFD84D",
        "button_text": "#000000",
        "button_border": "#000000",
        "input_bg": "#FFF6CC",
        "input_text": "#000000",
        "sidebar_bg": "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(246,247,255,1) 100%)",
        "hero_bg": """
            radial-gradient(circle at top right, rgba(90,215,255,0.18), transparent 30%),
            radial-gradient(circle at 10% 0%, rgba(255,107,154,0.16), transparent 18%),
            linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(246,247,255,1) 100%)
        """,
    },
}


ATLAS_CSS_TEMPLATE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&family=Space+Grotesk:wght@500;700&display=swap');

    :root {
        --atlas-bg-primary: __BG_PRIMARY__;
        --atlas-bg-secondary: __BG_SECONDARY__;
        --atlas-card-bg: __CARD_BG__;
        --atlas-card-glass: __CARD_GLASS__;
        --atlas-border: __BORDER__;
        --atlas-cyan: __CYAN__;
        --atlas-yellow: __YELLOW__;
        --atlas-green: __GREEN__;
        --atlas-pink: __PINK__;
        --atlas-text: __TEXT__;
        --atlas-muted: __MUTED__;
        --atlas-shadow-hard: __SHADOW_HARD__;
        --atlas-shadow-soft: __SHADOW_SOFT__;
        --atlas-radius: 14px;
        --atlas-border-width: 3px;
        --atlas-grid-line: __GRID_LINE__;
    }

    html, body, [class*="css"] {
        font-family: "Inter", sans-serif;
    }

    .stApp {
        background: __APP_BACKGROUND__;
        color: var(--atlas-text);
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(var(--atlas-grid-line) 1px, transparent 1px),
            linear-gradient(90deg, var(--atlas-grid-line) 1px, transparent 1px);
        background-size: 48px 48px;
        pointer-events: none;
        opacity: 0.5;
        mask-image: linear-gradient(180deg, rgba(0,0,0,0.45), rgba(0,0,0,0.05));
    }

    #MainMenu, footer, header[data-testid="stHeader"] {
        visibility: hidden;
    }

    [data-testid="stSidebarNav"] {
        display: none;
    }

    [data-testid="stAppViewContainer"] > .main {
        color: var(--atlas-text);
    }

    .main .block-container {
        max-width: 1400px;
        padding-top: 1.6rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: "Space Grotesk", sans-serif;
        color: var(--atlas-text);
        letter-spacing: -0.03em;
    }

    p, li, label, div[data-testid="stMarkdownContainer"], span {
        color: var(--atlas-text);
    }

    code, pre, .atlas-data-font {
        font-family: "JetBrains Mono", monospace !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: __SIDEBAR_BG__;
        border-right: var(--atlas-border-width) solid var(--atlas-border);
        box-shadow: 10px 0 30px rgba(0,0,0,0.22);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    [data-testid="stSidebar"] a {
        color: var(--atlas-text) !important;
        text-decoration: none !important;
    }

    .atlas-shell-topbar {
        display: grid;
        grid-template-columns: 1.2fr 1.05fr 0.75fr;
        gap: 0.9rem;
        margin-bottom: 1rem;
        animation: atlasFadeUp 0.45s ease-out;
    }

    .atlas-topbar-card,
    .atlas-hero,
    .atlas-panel,
    .atlas-feature-card,
    .atlas-info-banner,
    .atlas-metric-card,
    .atlas-source-card,
    .atlas-section-head,
    .atlas-story-panel,
    .atlas-nav-panel,
    .atlas-stat-card,
    .atlas-source-mini {
        background: var(--atlas-card-bg);
        border: var(--atlas-border-width) solid var(--atlas-border);
        border-radius: var(--atlas-radius);
        box-shadow: var(--atlas-shadow-hard), var(--atlas-shadow-soft);
        backdrop-filter: blur(14px);
    }

    .atlas-topbar-card {
        padding: 0.95rem 1rem;
        min-height: 92px;
    }

    .atlas-topbar-card h2 {
        margin: 0;
        font-size: 1.2rem;
    }

    .atlas-topbar-card p {
        margin: 0.28rem 0 0 0;
        color: var(--atlas-muted);
        line-height: 1.5;
    }

    .atlas-chip-row {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        align-items: center;
    }

    .atlas-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.45rem 0.72rem;
        border-radius: 999px;
        border: 2px solid var(--atlas-border);
        background: rgba(0,0,0,0.35);
        color: var(--atlas-text);
        box-shadow: 3px 3px 0px #000000;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .atlas-chip.cyan { color: var(--atlas-cyan); }
    .atlas-chip.yellow { color: var(--atlas-yellow); }
    .atlas-chip.green { color: var(--atlas-green); }
    .atlas-chip.pink { color: var(--atlas-pink); }

    .atlas-side-brand {
        padding: 1rem;
        margin-bottom: 0.9rem;
        border: var(--atlas-border-width) solid var(--atlas-border);
        border-radius: var(--atlas-radius);
        background:
            radial-gradient(circle at top right, rgba(0,229,255,0.16), transparent 30%),
            linear-gradient(135deg, rgba(21,26,46,0.96) 0%, rgba(11,15,26,0.98) 100%);
        box-shadow: var(--atlas-shadow-hard), var(--atlas-shadow-soft);
    }

    .atlas-side-brand .atlas-kicker {
        margin-bottom: 0.45rem;
    }

    .atlas-side-brand h3 {
        margin: 0;
        font-size: 1.65rem;
    }

    .atlas-side-brand p {
        margin: 0.35rem 0 0 0;
        color: var(--atlas-muted);
        line-height: 1.5;
    }

    .atlas-side-section {
        margin: 1rem 0 0.55rem 0;
        padding-left: 0.1rem;
        font-size: 0.74rem;
        color: var(--atlas-muted);
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
    }

    .atlas-active-page {
        padding: 0.75rem 0.9rem;
        border: var(--atlas-border-width) solid var(--atlas-border);
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(0,229,255,0.18) 0%, rgba(255,92,138,0.12) 100%);
        box-shadow: 4px 4px 0px #000000;
        font-family: "JetBrains Mono", monospace;
        margin-bottom: 0.65rem;
    }

    .stButton > button,
    .stDownloadButton > button,
    .stLinkButton > a,
    .stFormSubmitButton > button {
        border-radius: 12px !important;
        border: var(--atlas-border-width) solid __BUTTON_BORDER__ !important;
        background: __BUTTON_BG__ !important;
        color: __BUTTON_TEXT__ !important;
        font-weight: 800 !important;
        box-shadow: var(--atlas-shadow-hard) !important;
        min-height: 2.9rem !important;
        transition: transform 120ms ease, box-shadow 120ms ease !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stLinkButton > a:hover,
    .stFormSubmitButton > button:hover {
        transform: translate(-2px, -2px) scale(1.01);
        box-shadow: 8px 8px 0px #000000 !important;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stDateInput input,
    .stSelectbox [data-baseweb="select"],
    .stMultiSelect [data-baseweb="select"] {
        color: __INPUT_TEXT__ !important;
        background: __INPUT_BG__ !important;
        border: var(--atlas-border-width) solid var(--atlas-border) !important;
        border-radius: 12px !important;
        box-shadow: 3px 3px 0px #000000 !important;
    }

    .stSlider [data-baseweb="slider"] {
        padding-top: 0.55rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.55rem;
        margin-bottom: 0.75rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(21,26,46,0.94);
        border: var(--atlas-border-width) solid var(--atlas-border);
        border-radius: 999px;
        box-shadow: 3px 3px 0px #000000;
        color: var(--atlas-text);
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0,229,255,0.16) 0%, rgba(255,92,138,0.14) 100%);
    }

    [data-testid="stMetric"] {
        background: var(--atlas-card-bg);
        border: var(--atlas-border-width) solid var(--atlas-border);
        border-radius: 12px;
        box-shadow: var(--atlas-shadow-hard), var(--atlas-shadow-soft);
        padding: 0.85rem 1rem;
    }

    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"],
    [data-testid="stImage"],
    [data-testid="stExpander"] {
        background: transparent;
        border-radius: 12px;
        animation: atlasFadeUp 0.55s ease-out;
    }

    .atlas-hero {
        padding: 2.3rem;
        margin-bottom: 1.2rem;
        background: __HERO_BG__;
        animation: atlasFadeUp 0.5s ease-out;
    }

    .atlas-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.36rem 0.72rem;
        border-radius: 999px;
        background: rgba(0,0,0,0.32);
        border: 2px solid var(--atlas-border);
        color: var(--atlas-cyan);
        box-shadow: 3px 3px 0px #000000;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }

    .atlas-hero h1 {
        margin: 0.85rem 0 0.4rem 0;
        font-size: clamp(2.9rem, 5vw, 5.4rem);
        line-height: 0.95;
    }

    .atlas-tagline {
        margin: 0;
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--atlas-yellow);
    }

    .atlas-subtitle {
        margin-top: 0.95rem;
        max-width: 780px;
        color: var(--atlas-muted);
        font-size: 1.03rem;
        line-height: 1.8;
    }

    .atlas-section-head,
    .atlas-feature-card,
    .atlas-panel,
    .atlas-info-banner,
    .atlas-story-panel,
    .atlas-source-card,
    .atlas-metric-card,
    .atlas-stat-card,
    .atlas-source-mini {
        padding: 1.15rem;
        margin-bottom: 1rem;
    }

    .atlas-section-head h3,
    .atlas-feature-card h4,
    .atlas-panel h4,
    .atlas-story-panel h4,
    .atlas-source-card h4 {
        margin: 0 0 0.45rem 0;
    }

    .atlas-section-head p,
    .atlas-feature-card p,
    .atlas-panel p,
    .atlas-info-banner p,
    .atlas-story-panel p,
    .atlas-source-card p {
        margin: 0;
        color: var(--atlas-muted);
        line-height: 1.65;
    }

    .atlas-info-banner {
        background:
            linear-gradient(135deg, rgba(0,229,255,0.10) 0%, rgba(21,26,46,0.98) 100%);
    }

    .atlas-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.95rem;
    }

    .atlas-stat-label,
    .atlas-source-label,
    .atlas-metric-label {
        display: block;
        font-size: 0.76rem;
        color: var(--atlas-muted);
        text-transform: uppercase;
        letter-spacing: 0.10em;
        margin-bottom: 0.35rem;
        font-weight: 700;
    }

    .atlas-stat-value,
    .atlas-source-value,
    .atlas-metric-value {
        display: block;
        color: var(--atlas-text);
        font-family: "Space Grotesk", sans-serif;
        font-weight: 700;
    }

    .atlas-metric-value {
        font-size: 1.85rem;
        line-height: 1.05;
    }

    .atlas-metric-sub {
        margin-top: 0.45rem;
        color: var(--atlas-muted);
        font-size: 0.92rem;
        line-height: 1.5;
    }

    .atlas-story-label {
        color: var(--atlas-pink);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .atlas-stepper {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.75rem;
        margin: 0.2rem 0 1.15rem 0;
    }

    .atlas-step-chip {
        padding: 0.9rem;
        border: var(--atlas-border-width) solid var(--atlas-border);
        border-radius: 12px;
        background: rgba(21,26,46,0.94);
        box-shadow: 4px 4px 0px #000000;
    }

    .atlas-step-chip.active {
        background: linear-gradient(135deg, rgba(0,229,255,0.16) 0%, rgba(255,216,77,0.12) 100%);
    }

    .atlas-step-chip span {
        color: var(--atlas-muted);
        font-size: 0.84rem;
    }

    .atlas-story-panel {
        border-left: 6px solid var(--atlas-cyan);
    }

    .atlas-status {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.36rem 0.65rem;
        border-radius: 999px;
        border: 2px solid var(--atlas-border);
        box-shadow: 3px 3px 0px #000000;
        background: rgba(0,0,0,0.28);
        color: var(--atlas-green);
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .atlas-status.warning {
        color: var(--atlas-yellow);
    }

    .atlas-status.neutral {
        color: var(--atlas-muted);
    }

    .atlas-nav-caption {
        color: var(--atlas-muted);
        font-size: 0.84rem;
        line-height: 1.5;
    }

    @keyframes atlasFadeUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @media (max-width: 1100px) {
        .atlas-shell-topbar {
            grid-template-columns: 1fr;
        }

        .main .block-container {
            padding-top: 1.2rem;
        }
    }

    @media (max-width: 800px) {
        .atlas-hero {
            padding: 1.5rem;
        }

        .atlas-hero h1 {
            font-size: 2.8rem;
        }
    }
</style>
"""


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _theme_key() -> str:
    return st.session_state.get("atlas_theme", "dark")


def _build_atlas_css(theme_key: str) -> str:
    theme = THEMES[theme_key]
    css = ATLAS_CSS_TEMPLATE
    replacements = {
        "__BG_PRIMARY__": theme["bg_primary"],
        "__BG_SECONDARY__": theme["bg_secondary"],
        "__CARD_BG__": theme["card_bg"],
        "__CARD_GLASS__": theme["card_glass"],
        "__BORDER__": theme["border"],
        "__CYAN__": theme["cyan"],
        "__YELLOW__": theme["yellow"],
        "__GREEN__": theme["green"],
        "__PINK__": theme["pink"],
        "__TEXT__": theme["text"],
        "__MUTED__": theme["muted"],
        "__SHADOW_HARD__": theme["shadow_hard"],
        "__SHADOW_SOFT__": theme["shadow_soft"],
        "__GRID_LINE__": theme["grid_line"],
        "__APP_BACKGROUND__": theme["app_background"].strip(),
        "__BUTTON_BG__": theme["button_bg"],
        "__BUTTON_TEXT__": theme["button_text"],
        "__BUTTON_BORDER__": theme["button_border"],
        "__INPUT_BG__": theme["input_bg"],
        "__INPUT_TEXT__": theme["input_text"],
        "__SIDEBAR_BG__": theme["sidebar_bg"],
        "__HERO_BG__": theme["hero_bg"].strip(),
    }
    for key, value in replacements.items():
        css = css.replace(key, value)
    return css


def apply_atlas_theme() -> None:
    st.markdown(_build_atlas_css(_theme_key()), unsafe_allow_html=True)


def render_sidebar_navigation(active_page: str) -> None:
    with st.sidebar:
        st.session_state.setdefault("atlas_theme", "dark")
        st.markdown(
            """
            <div class="atlas-side-brand">
                <div class="atlas-kicker">ATLAS</div>
                <h3>ATLAS mini max v2</h3>
                <p>Operational climate monitoring, prediction workflows, and research-grade analysis.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link("app.py", label="Landing", icon=":material/rocket_launch:")
        theme_label = st.radio(
            "Theme",
            options=["Dark Orbital", "Light Brutal"],
            index=0 if st.session_state.get("atlas_theme", "dark") == "dark" else 1,
            key=f"atlas_theme_selector_{active_page.lower().replace(' ', '_')}",
            horizontal=False,
        )
        st.session_state["atlas_theme"] = "dark" if theme_label == "Dark Orbital" else "light"
        st.text_input(
            "Sidebar Search",
            key="atlas_sidebar_search",
            placeholder="Search modules",
            label_visibility="collapsed",
        )
        st.markdown("<div class='atlas-side-section'>Workspace</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='atlas-active-page'>Active: {_escape(active_page)}</div>", unsafe_allow_html=True)
        for item in NAV_ITEMS:
            st.page_link(item["path"], label=item["label"], icon=item["icon"])
        st.markdown("<div class='atlas-side-section'>System</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="atlas-nav-panel">
                <p class="atlas-nav-caption">Theme: {theme_name}</p>
                <p class="atlas-nav-caption">Layout: 12-column responsive shell</p>
                <p class="atlas-nav-caption">UI mix: NASA science + Apple glass + neobrutal cards</p>
            </div>
            """.format(theme_name="Dark orbital mode" if st.session_state["atlas_theme"] == "dark" else "Light neobrutal mode"),
            unsafe_allow_html=True,
        )


def render_topbar(active_page: str, subtitle: str, search_placeholder: str = "Search climate signals, regions, or datasets") -> str:
    utc_stamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
    left, center, right = st.columns((1.15, 1.0, 0.7))
    with left:
        st.markdown(
            f"""
            <div class="atlas-topbar-card">
                <div class="atlas-kicker">Active View</div>
                <h2>{_escape(active_page)}</h2>
                <p>{_escape(subtitle)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with center:
        search_value = st.text_input(
            "Global Search",
            placeholder=search_placeholder,
            key=f"atlas_topbar_search_{active_page.lower().replace(' ', '_')}",
            label_visibility="collapsed",
        )
    with right:
        st.markdown(
            f"""
            <div class="atlas-topbar-card">
                <div class="atlas-chip-row">
                    <span class="atlas-chip cyan">Live</span>
                    <span class="atlas-chip yellow">{_escape(utc_stamp)}</span>
                    <span class="atlas-chip pink">Analyst</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return search_value


def render_app_shell(active_page: str, subtitle: str, search_placeholder: str = "Search climate signals, regions, or datasets") -> str:
    render_sidebar_navigation(active_page)
    apply_atlas_theme()
    return render_topbar(active_page, subtitle, search_placeholder)


def render_page_hero(kicker: str, title: str, body: str, subtitle: str | None = None) -> None:
    subtitle_html = f"<p class='atlas-tagline'>{_escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <section class="atlas-hero">
            <div class="atlas-kicker">{_escape(kicker)}</div>
            <h1>{_escape(title)}</h1>
            {subtitle_html}
            <p class="atlas-subtitle">{_escape(body)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_intro(title: str, body: str, eyebrow: str | None = None) -> None:
    eyebrow_html = f"<div class='atlas-kicker'>{_escape(eyebrow)}</div>" if eyebrow else ""
    st.markdown(
        f"""
        <div class="atlas-section-head">
            {eyebrow_html}
            <h3>{_escape(title)}</h3>
            <p>{_escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feature_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="atlas-feature-card">
            <h4>{_escape(title)}</h4>
            <p>{_escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_banner(message: str) -> None:
    st.markdown(
        f"""
        <div class="atlas-info-banner">
            <p>{_escape(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title: str, value: str, subtext: str) -> None:
    st.markdown(
        f"""
        <div class="atlas-metric-card">
            <div class="atlas-metric-label">{_escape(title)}</div>
            <div class="atlas-metric-value">{_escape(value)}</div>
            <div class="atlas-metric-sub">{_escape(subtext)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_story_panel(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="atlas-story-panel">
            <h4>{_escape(title)}</h4>
            <p>{_escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_source_card(title: str, status: str, detail: str) -> None:
    tone = "warning" if "need" in status.lower() else "neutral" if status.lower() in {"ready", "optional"} else ""
    status_class = f"atlas-status {tone}".strip()
    st.markdown(
        f"""
        <div class="atlas-source-card">
            <span class="{status_class}">{_escape(status)}</span>
            <h4>{_escape(title)}</h4>
            <p>{_escape(detail)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_story_stepper(steps: list[dict[str, str]], active_index: int) -> None:
    chips: list[str] = []
    for idx, step in enumerate(steps):
        active_class = "active" if idx == active_index else ""
        sublabel = step.get("region") or step.get("title") or ""
        chips.append(
            f"""
            <div class="atlas-step-chip {active_class}">
                <strong>{idx + 1}. {_escape(step["slug"])}</strong>
                <span>{_escape(sublabel)}</span>
            </div>
            """
        )
    st.markdown(f"<div class='atlas-stepper'>{''.join(chips)}</div>", unsafe_allow_html=True)
