from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st


OPENROUTER_SECRET_NAMES = (
    "OPENROUTER_API_KEY",
    "OPEN_ROUTER_API_KEY",
)
OPENROUTER_MODEL_NAMES = (
    "OPENROUTER_MODEL",
    "OPEN_ROUTER_MODEL",
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _secret_value(names: tuple[str, ...]) -> str | None:
    for name in names:
        env_value = os.getenv(name)
        if env_value:
            return env_value.strip()

    try:
        secrets = st.secrets
    except Exception:
        return None

    for name in names:
        if name in secrets and secrets[name]:
            return str(secrets[name]).strip()
        lowered = name.lower()
        if lowered in secrets and secrets[lowered]:
            return str(secrets[lowered]).strip()
    return None


def get_openrouter_api_key() -> str | None:
    return _secret_value(OPENROUTER_SECRET_NAMES)


def get_openrouter_model() -> str:
    return _secret_value(OPENROUTER_MODEL_NAMES) or "openrouter/auto"


def _frame_snapshot(frame: pd.DataFrame, value_column: str) -> str:
    if frame.empty:
        return "No data available."
    latest = frame.iloc[-1]
    earliest = frame.iloc[0]
    change = float(latest[value_column] - earliest[value_column])
    return (
        f"Latest value: {float(latest[value_column]):.2f}. "
        f"Series start: {float(earliest[value_column]):.2f}. "
        f"Net change across view: {change:+.2f}."
    )


@st.cache_data(show_spinner=False, ttl=900)
def generate_prediction_brief(
    query: str,
    region: str,
    variable: str,
    observed_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
) -> str:
    api_key = get_openrouter_api_key()
    if not api_key:
        raise RuntimeError("OpenRouter API key is not configured.")

    observed_summary = _frame_snapshot(observed_df, "value")
    forecast_summary = _frame_snapshot(forecast_df.rename(columns={"forecast": "value"}), "value")
    model = get_openrouter_model()
    payload: dict[str, Any] = {
        "model": model,
        "temperature": 0.3,
        "max_tokens": 350,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are ATLAS Copilot, a concise climate analytics assistant. "
                    "Summarize forecast risk, trend direction, and one action-oriented takeaway."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User query: {query}\n"
                    f"Region: {region}\n"
                    f"Variable: {variable}\n"
                    f"Observed summary: {observed_summary}\n"
                    f"Forecast summary: {forecast_summary}\n"
                    "Respond in 3 short bullet points."
                ),
            },
        ],
    }
    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://atlas-mini-max-v2.streamlit.app",
            "X-Title": "ATLAS mini max v2",
        },
        json=payload,
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("OpenRouter returned no choices.")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not content:
        raise RuntimeError("OpenRouter returned an empty response.")
    return str(content).strip()
