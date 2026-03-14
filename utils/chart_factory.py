from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


FONT_FAMILY = "Inter, sans-serif"
PAPER_BG = "rgba(0,0,0,0)"
PLOT_BG = "rgba(17,24,39,0.86)"
GRID_COLOR = "rgba(255,255,255,0.08)"
TEXT_COLOR = "#FFFFFF"
MUTED_COLOR = "#9CA3AF"
CYAN = "#00E5FF"
YELLOW = "#FFD84D"
PINK = "#FF5C8A"
GREEN = "#6EFF9A"
SLATE = "#94A3B8"
CRIMSON = "#FF5C8A"


def _apply_chart_style(
    figure: go.Figure,
    *,
    title: str,
    xaxis_title: str | None = None,
    yaxis_title: str | None = None,
    show_legend: bool = True,
) -> go.Figure:
    figure.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=56, b=12),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family=FONT_FAMILY, color=TEXT_COLOR),
        title_font=dict(family="Space Grotesk, sans-serif", size=18, color=TEXT_COLOR),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0.0,
            bgcolor="rgba(11,15,26,0.55)",
            bordercolor="rgba(255,255,255,0.06)",
            borderwidth=1,
            font=dict(color=TEXT_COLOR),
        ),
        showlegend=show_legend,
    )
    if xaxis_title is not None:
        figure.update_xaxes(
            title=xaxis_title,
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
            color=TEXT_COLOR,
            title_font=dict(color=MUTED_COLOR),
        )
    if yaxis_title is not None:
        figure.update_yaxes(
            title=yaxis_title,
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
            color=TEXT_COLOR,
            title_font=dict(color=MUTED_COLOR),
        )
    return figure


def create_heatmap(
    map_slice,
    axes: dict[str, str | None],
    title: str,
    colorscale: str,
    colorbar_title: str,
) -> go.Figure:
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]
    figure = go.Figure(
        data=[
            go.Heatmap(
                z=map_slice.values,
                x=map_slice[lon_axis].values,
                y=map_slice[lat_axis].values,
                colorscale=colorscale,
                zsmooth="best",
                colorbar=dict(title=dict(text=colorbar_title, font=dict(color=TEXT_COLOR)), tickfont=dict(color=TEXT_COLOR)),
                hovertemplate="Lon %{x:.1f}<br>Lat %{y:.1f}<br>Value %{z:.2f}<extra></extra>",
            )
        ]
    )
    return _apply_chart_style(
        figure,
        title=title,
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        show_legend=False,
    )


def create_spatial_map(
    map_slice,
    axes: dict[str, str | None],
    title: str,
    colorscale: str,
    colorbar_title: str,
    projection: str,
) -> go.Figure:
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]
    lon_values = np.asarray(map_slice[lon_axis].values)
    lon_values = np.where(lon_values > 180.0, lon_values - 360.0, lon_values)
    lat_values = np.asarray(map_slice[lat_axis].values)
    z_values = np.asarray(map_slice.values)
    figure = go.Figure()
    figure.add_trace(
        go.Contour(
            z=z_values,
            x=lon_values,
            y=lat_values,
            colorscale=colorscale,
            contours=dict(coloring="heatmap", showlines=False),
            line=dict(width=0),
            colorbar=dict(title=dict(text=colorbar_title, font=dict(color=TEXT_COLOR)), tickfont=dict(color=TEXT_COLOR)),
            hovertemplate="Lon %{x:.1f}<br>Lat %{y:.1f}<br>Value %{z:.2f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Contour(
            z=z_values,
            x=lon_values,
            y=lat_values,
            showscale=False,
            contours=dict(coloring="none", showlines=True),
            line=dict(color="rgba(255,255,255,0.16)", width=0.8),
            hoverinfo="skip",
        )
    )
    subtitle = f"{title} - {projection} view" if projection else title
    return _apply_chart_style(
        figure,
        title=subtitle,
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        show_legend=False,
    )


def create_time_series(
    series_df: pd.DataFrame,
    value_column: str,
    trend_df: pd.DataFrame,
    anomaly_mask,
    title: str,
    y_label: str,
) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=series_df["time"],
            y=series_df[value_column],
            mode="lines+markers",
            name="Observed",
            line=dict(color=CYAN, width=2.6),
            marker=dict(size=4.5, color=CYAN),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=trend_df["time"],
            y=trend_df["trend"],
            mode="lines",
            name="Trend",
            line=dict(color=YELLOW, width=2.2, dash="dash"),
        )
    )
    if anomaly_mask is not None and np.any(anomaly_mask):
        anomaly_df = series_df.loc[anomaly_mask]
        figure.add_trace(
            go.Scatter(
                x=anomaly_df["time"],
                y=anomaly_df[value_column],
                mode="markers",
                name="Anomalies",
                marker=dict(color=PINK, size=8, symbol="diamond"),
            )
        )
    return _apply_chart_style(figure, title=title, xaxis_title="Time", yaxis_title=y_label)


def create_globe(
    map_slice,
    axes: dict[str, str | None],
    title: str,
    colorscale: str,
    colorbar_title: str,
    marker_size: int = 5,
) -> go.Figure:
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]
    lon_values = np.asarray(map_slice[lon_axis].values)
    lat_values = np.asarray(map_slice[lat_axis].values)
    lon_radians = np.deg2rad(lon_values)
    lat_radians = np.deg2rad(lat_values)
    lon_mesh, lat_mesh = np.meshgrid(lon_radians, lat_radians)

    radius = 1.0
    x = radius * np.cos(lat_mesh) * np.cos(lon_mesh)
    y = radius * np.cos(lat_mesh) * np.sin(lon_mesh)
    z = radius * np.sin(lat_mesh)
    customdata = np.dstack((np.rad2deg(lat_mesh), np.rad2deg(lon_mesh)))

    figure = go.Figure(
        data=[
            go.Surface(
                x=x,
                y=y,
                z=z,
                surfacecolor=np.asarray(map_slice.values),
                colorscale=colorscale,
                colorbar=dict(title=dict(text=colorbar_title, font=dict(color=TEXT_COLOR)), tickfont=dict(color=TEXT_COLOR)),
                customdata=customdata,
                showscale=True,
                hovertemplate="Lat %{customdata[0]:.1f}<br>Lon %{customdata[1]:.1f}<br>Value %{surfacecolor:.2f}<extra></extra>",
                lighting=dict(ambient=0.7, diffuse=0.75, roughness=0.9, specular=0.05),
            )
        ]
    )
    figure.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=56, b=12),
        paper_bgcolor=PAPER_BG,
        font=dict(family=FONT_FAMILY, color=TEXT_COLOR),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor="rgba(0,0,0,0)",
            aspectmode="data",
            camera=dict(eye=dict(x=1.55, y=1.2, z=0.8)),
        ),
    )
    return figure


def create_latitude_profile(
    map_slice,
    axes: dict[str, str | None],
    title: str,
    x_label: str,
) -> go.Figure:
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]
    profile = map_slice.mean(dim=lon_axis)

    figure = go.Figure(
        data=[
            go.Scatter(
                x=profile.values,
                y=profile[lat_axis].values,
                mode="lines",
                line=dict(color=GREEN, width=3),
                fill="tozerox",
                fillcolor="rgba(110,255,154,0.12)",
                hovertemplate=f"{x_label} %{{x:.2f}}<br>Lat %{{y:.1f}}<extra></extra>",
            )
        ]
    )
    return _apply_chart_style(
        figure,
        title=title,
        xaxis_title=x_label,
        yaxis_title="Latitude",
        show_legend=False,
    )


def create_animated_heatmap(
    annual_data,
    axes: dict[str, str | None],
    title: str,
    colorscale: str,
    colorbar_title: str,
) -> go.Figure:
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]
    years = annual_data["year"].values.tolist()
    first = annual_data.isel(year=0)

    figure = go.Figure(
        data=[
            go.Heatmap(
                z=first.values,
                x=first[lon_axis].values,
                y=first[lat_axis].values,
                colorscale=colorscale,
                colorbar=dict(title=dict(text=colorbar_title, font=dict(color=TEXT_COLOR)), tickfont=dict(color=TEXT_COLOR)),
                hovertemplate="Lon %{x:.1f}<br>Lat %{y:.1f}<br>Value %{z:.2f}<extra></extra>",
            )
        ],
        frames=[
            go.Frame(
                data=[
                    go.Heatmap(
                        z=annual_data.sel(year=year).values,
                        x=annual_data[lon_axis].values,
                        y=annual_data[lat_axis].values,
                        colorscale=colorscale,
                    )
                ],
                name=str(year),
            )
            for year in years
        ],
    )
    figure.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=56, b=12),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family=FONT_FAMILY, color=TEXT_COLOR),
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "x": 1.0,
                "y": 1.14,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 240, "redraw": True}, "fromcurrent": True}],
                    }
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "currentvalue": {"prefix": "Year: "},
                "steps": [
                    {
                        "label": str(year),
                        "method": "animate",
                        "args": [[str(year)], {"mode": "immediate", "frame": {"duration": 0, "redraw": True}}],
                    }
                    for year in years
                ],
            }
        ],
    )
    figure.update_xaxes(showgrid=True, gridcolor=GRID_COLOR, zeroline=False)
    figure.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, zeroline=False)
    return figure


def create_forecast_figure(forecast_df: pd.DataFrame, title: str) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=forecast_df["time"],
            y=forecast_df["temperature_c"],
            mode="lines+markers",
            name="Temperature",
            line=dict(color=CYAN, width=2.8),
            marker=dict(size=4),
        )
    )
    figure.add_trace(
        go.Bar(
            x=forecast_df["time"],
            y=forecast_df["precip_probability_pct"],
            name="Precipitation chance",
            marker_color="rgba(255,216,77,0.45)",
            yaxis="y2",
            opacity=0.9,
        )
    )
    figure.update_layout(
        yaxis2=dict(
            title="Precipitation chance (%)",
            overlaying="y",
            side="right",
            range=[0, 100],
            showgrid=False,
            color=TEXT_COLOR,
        )
    )
    return _apply_chart_style(figure, title=title, xaxis_title="Time", yaxis_title="Temperature (deg C)")


def create_air_quality_figure(aq_df: pd.DataFrame, title: str) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=aq_df["time"],
            y=aq_df["pm2_5"],
            mode="lines",
            name="PM2.5",
            line=dict(color=PINK, width=2.6),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=aq_df["time"],
            y=aq_df["pm10"],
            mode="lines",
            name="PM10",
            line=dict(color=YELLOW, width=2.4),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=aq_df["time"],
            y=aq_df["aqi"],
            mode="lines",
            name="AQI band",
            line=dict(color=SLATE, width=2, dash="dash"),
            yaxis="y2",
        )
    )
    figure.update_layout(
        yaxis2=dict(
            title="AQI",
            overlaying="y",
            side="right",
            range=[0.5, 5.5],
            tickmode="array",
            tickvals=[1, 2, 3, 4, 5],
            showgrid=False,
            color=TEXT_COLOR,
        )
    )
    return _apply_chart_style(figure, title=title, xaxis_title="Time", yaxis_title="Concentration (ug/m3)")


def create_station_history_figure(history_df: pd.DataFrame, title: str) -> go.Figure:
    figure = go.Figure()
    if "TMAX" in history_df:
        figure.add_trace(
            go.Scatter(
                x=history_df["date"],
                y=history_df["TMAX"],
                mode="lines",
                name="Max temp",
                line=dict(color=PINK, width=2.5),
            )
        )
    if "TMIN" in history_df:
        figure.add_trace(
            go.Scatter(
                x=history_df["date"],
                y=history_df["TMIN"],
                mode="lines",
                name="Min temp",
                line=dict(color=CYAN, width=2.3),
            )
        )
    if "PRCP" in history_df:
        figure.add_trace(
            go.Bar(
                x=history_df["date"],
                y=history_df["PRCP"],
                name="Precipitation",
                marker_color="rgba(110,255,154,0.36)",
                opacity=0.85,
                yaxis="y2",
            )
        )
    figure.update_layout(
        yaxis2=dict(
            title="Precipitation (mm)",
            overlaying="y",
            side="right",
            showgrid=False,
            color=TEXT_COLOR,
        )
    )
    return _apply_chart_style(figure, title=title, xaxis_title="Date", yaxis_title="Temperature (deg C)")


def create_timeline_figure(series_df: pd.DataFrame, title: str, value_column: str, y_label: str, color: str = CYAN) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Scatter(
                x=series_df["time"],
                y=series_df[value_column],
                mode="lines",
                line=dict(color=color, width=2.7),
                fill="tozeroy",
                fillcolor="rgba(0,229,255,0.10)" if color == CYAN else "rgba(255,92,138,0.12)",
                name=y_label,
            )
        ]
    )
    return _apply_chart_style(figure, title=title, xaxis_title="Time", yaxis_title=y_label, show_legend=False)


def create_prediction_figure(
    observed_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    title: str,
    value_column: str,
    y_label: str,
) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=observed_df["time"],
            y=observed_df[value_column],
            mode="lines",
            name="Observed",
            line=dict(color=CYAN, width=2.6),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast_df["time"],
            y=forecast_df["forecast"],
            mode="lines",
            name="Forecast",
            line=dict(color=YELLOW, width=2.6),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=pd.concat([forecast_df["time"], forecast_df["time"][::-1]]),
            y=pd.concat([forecast_df["upper"], forecast_df["lower"][::-1]]),
            fill="toself",
            fillcolor="rgba(255,216,77,0.16)",
            line=dict(color="rgba(255,216,77,0.0)"),
            hoverinfo="skip",
            showlegend=True,
            name="Confidence band",
        )
    )
    return _apply_chart_style(figure, title=title, xaxis_title="Time", yaxis_title=y_label)


def create_anomaly_bar_figure(
    series_df: pd.DataFrame,
    title: str,
    value_column: str,
    y_label: str,
) -> go.Figure:
    values = series_df[value_column].astype(float)
    colors = [PINK if value >= 0 else CYAN for value in values]
    figure = go.Figure(
        data=[
            go.Bar(
                x=series_df["time"],
                y=values,
                marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.08)", width=1)),
                hovertemplate="Time %{x}<br>Value %{y:.2f}<extra></extra>",
            )
        ]
    )
    _apply_chart_style(figure, title=title, xaxis_title="Time", yaxis_title=y_label, show_legend=False)
    figure.update_yaxes(zeroline=True, zerolinecolor="rgba(255,255,255,0.35)")
    return figure


def create_ranked_bar_figure(
    values: dict[str, float],
    title: str,
    x_label: str,
    *,
    diverging: bool = False,
) -> go.Figure:
    ordered = sorted(values.items(), key=lambda item: item[1], reverse=True)
    labels = [item[0] for item in ordered]
    scores = [float(item[1]) for item in ordered]
    palette = [PINK, YELLOW, CYAN, GREEN, SLATE]
    if diverging:
        colors = [PINK if score >= 0 else CYAN for score in scores]
    else:
        colors = [palette[index % len(palette)] for index in range(len(scores))]

    figure = go.Figure(
        data=[
            go.Bar(
                x=scores,
                y=labels,
                orientation="h",
                marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.08)", width=1)),
                text=[f"{score:.1f}" for score in scores],
                textposition="outside",
                hovertemplate="%{y}: %{x:.2f}<extra></extra>",
            )
        ]
    )
    _apply_chart_style(figure, title=title, xaxis_title=x_label, yaxis_title=None, show_legend=False)
    figure.update_yaxes(showgrid=False, autorange="reversed", color=TEXT_COLOR)
    if diverging:
        figure.update_xaxes(zeroline=True, zerolinecolor="rgba(255,255,255,0.35)")
    return figure


def create_gauge_figure(
    value: float,
    title: str,
    *,
    suffix: str = "",
    max_value: float = 100.0,
) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Indicator(
                mode="gauge+number",
                value=float(value),
                number={"suffix": suffix, "font": {"color": TEXT_COLOR, "size": 34}},
                gauge={
                    "axis": {"range": [0, max_value], "tickcolor": MUTED_COLOR},
                    "bar": {"color": PINK},
                    "bgcolor": PLOT_BG,
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, max_value * 0.35], "color": "rgba(0,229,255,0.18)"},
                        {"range": [max_value * 0.35, max_value * 0.7], "color": "rgba(255,216,77,0.20)"},
                        {"range": [max_value * 0.7, max_value], "color": "rgba(255,92,138,0.22)"},
                    ],
                    "threshold": {"line": {"color": TEXT_COLOR, "width": 4}, "value": float(value)},
                },
            )
        ]
    )
    figure.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family=FONT_FAMILY, color=TEXT_COLOR),
        margin=dict(l=24, r=24, t=56, b=18),
    )
    return figure


def create_donut_figure(values: dict[str, float], title: str) -> go.Figure:
    labels = list(values.keys())
    scores = [max(float(score), 0.01) for score in values.values()]
    palette = [PINK, YELLOW, CYAN, GREEN, SLATE]
    figure = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=scores,
                hole=0.62,
                marker=dict(colors=palette[: len(labels)], line=dict(color=PLOT_BG, width=3)),
                textinfo="label+percent",
                textfont=dict(color=TEXT_COLOR),
                sort=False,
            )
        ]
    )
    figure.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family=FONT_FAMILY, color=TEXT_COLOR),
        margin=dict(l=18, r=18, t=56, b=18),
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, x=0.0),
    )
    return figure


def create_seasonality_bar_figure(
    series_df: pd.DataFrame,
    title: str,
    value_column: str,
    y_label: str,
) -> go.Figure:
    seasonal = series_df.copy()
    seasonal["time"] = pd.to_datetime(seasonal["time"])
    seasonal["month_number"] = seasonal["time"].dt.month
    seasonal["month_label"] = seasonal["time"].dt.strftime("%b")
    grouped = (
        seasonal.groupby(["month_number", "month_label"], as_index=False)[value_column]
        .mean()
        .sort_values("month_number")
    )
    colors = [CYAN, GREEN, YELLOW, PINK] * 3
    figure = go.Figure(
        data=[
            go.Bar(
                x=grouped["month_label"],
                y=grouped[value_column],
                marker=dict(color=colors[: len(grouped)], line=dict(color="rgba(255,255,255,0.08)", width=1)),
                hovertemplate="%{x}: %{y:.2f}<extra></extra>",
            )
        ]
    )
    return _apply_chart_style(figure, title=title, xaxis_title="Month", yaxis_title=y_label, show_legend=False)


def create_forecast_delta_figure(forecast_df: pd.DataFrame, title: str) -> go.Figure:
    frame = forecast_df.copy()
    value_column = "temperature_c" if "temperature_c" in frame.columns else "forecast"
    frame["temp_delta_c"] = frame[value_column].diff().fillna(0.0)
    colors = [PINK if value >= 0 else CYAN for value in frame["temp_delta_c"]]
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=frame["time"],
            y=frame["temp_delta_c"],
            name="Temperature shift",
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.08)", width=1)),
            hovertemplate="Time %{x}<br>Temp shift %{y:.2f} C<extra></extra>",
        )
    )
    if "precip_probability_pct" in frame.columns:
        figure.add_trace(
            go.Scatter(
                x=frame["time"],
                y=frame["precip_probability_pct"],
                mode="lines",
                name="Precipitation chance",
                line=dict(color=YELLOW, width=2.2),
                yaxis="y2",
                hovertemplate="Time %{x}<br>Precip %{y:.0f}%<extra></extra>",
            )
        )
        figure.update_layout(
            yaxis2=dict(
                title="Precipitation chance (%)",
                overlaying="y",
                side="right",
                range=[0, 100],
                showgrid=False,
                color=TEXT_COLOR,
            )
        )
    _apply_chart_style(figure, title=title, xaxis_title="Time", yaxis_title="Temperature shift (C)")
    figure.update_yaxes(zeroline=True, zerolinecolor="rgba(255,255,255,0.35)")
    return figure


def create_risk_radar(risk_scores: dict[str, float], title: str) -> go.Figure:
    categories = list(risk_scores.keys())
    values = list(risk_scores.values())
    if categories:
        categories.append(categories[0])
        values.append(values[0])
    figure = go.Figure(
        data=[
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill="toself",
                line=dict(color=PINK, width=2.5),
                fillcolor="rgba(255,92,138,0.18)",
                name="Risk score",
            )
        ]
    )
    figure.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family=FONT_FAMILY, color=TEXT_COLOR),
        polar=dict(
            bgcolor=PLOT_BG,
            radialaxis=dict(range=[0, 100], gridcolor=GRID_COLOR, color=TEXT_COLOR),
            angularaxis=dict(gridcolor=GRID_COLOR, color=TEXT_COLOR),
        ),
        margin=dict(l=18, r=18, t=56, b=18),
    )
    return figure
