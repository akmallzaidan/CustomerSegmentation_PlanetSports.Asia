"""
components/charts.py
--------------------
All Plotly figure builders. Every function returns a themed `go.Figure`
(rounded, dark/light aware, hover + zoom + PNG export enabled via config).

Render helper `render()` wraps a figure in a glass container.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components import theme
from utils.i18n import t
from utils.preprocessing import sample_for_plot

RFM = ["Recency", "Frequency", "Monetary"]

# Recency bands used across the dashboard (days since last transaction).
RECENCY_BINS = [0, 30, 90, 180, 270, 366]
RECENCY_LABELS = ["0–30 d", "31–90 d", "91–180 d", "181–270 d", "271–365 d"]


# --------------------------------------------------------------------------- #
# Rendering helper
# --------------------------------------------------------------------------- #
def render(fig: go.Figure, height: int = 380, key: str | None = None) -> None:
    """Theme + display a figure inside a rounded glass card."""
    theme.apply_chart_theme(fig, height=height)
    st.plotly_chart(fig, use_container_width=True, config=theme.CHART_CONFIG, key=key)


# --------------------------------------------------------------------------- #
# RFM analysis charts
# --------------------------------------------------------------------------- #
def rfm_histogram(rfm: pd.DataFrame, column: str, color: str) -> go.Figure:
    if column == "Frequency":
        # Frequency is a small integer count (post High-Value split, typically
        # 1-6). Continuous binning fragments that narrow range into partial
        # bars; one bin per whole number reads far better and spreads the
        # x-axis across clean, evenly spaced integer ticks.
        lo, hi = int(rfm[column].min()), int(rfm[column].max())
        fig = px.histogram(rfm, x=column, opacity=0.9)
        fig.update_traces(xbins=dict(start=lo - 0.5, end=hi + 0.5, size=1))
        fig.update_xaxes(dtick=1, tick0=lo)
    else:
        fig = px.histogram(rfm, x=column, nbins=30, opacity=0.9)
    fig.update_traces(marker_color=color, marker_line_width=0, marker=dict(cornerradius=6))
    fig.update_layout(
        title=t("chart.dist", col=column),
        bargap=0.06,
        xaxis_title=column,
        yaxis_title=t("chart.customers"),
    )
    return fig


def rfm_boxplot(rfm: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, color in zip(RFM, theme.CATEGORICAL):
        # Normalise to 0-100 so the three metrics share one axis.
        series = rfm[col]
        norm = (series - series.min()) / (series.max() - series.min() + 1e-9) * 100
        fig.add_trace(
            go.Box(
                y=norm, name=col, marker_color=color, boxmean=True,
                line_width=1.5, fillcolor="rgba(46,110,247,0.12)",
            )
        )
    fig.update_layout(title=t("chart.rfm_spread"), yaxis_title=t("chart.norm_value"))
    return fig


def correlation_heatmap(rfm: pd.DataFrame) -> go.Figure:
    corr = rfm[RFM].corr().round(2)
    fig = px.imshow(
        corr, text_auto=True, aspect="auto",
        color_continuous_scale=theme.SEQUENTIAL, zmin=-1, zmax=1,
    )
    fig.update_layout(title=t("chart.corr"))
    fig.update_xaxes(side="bottom")
    return fig


def rfm_score_distribution(rfm: pd.DataFrame) -> go.Figure:
    counts = rfm["RFM_Sum"].value_counts().sort_index()
    fig = go.Figure(
        go.Bar(
            x=counts.index.astype(str), y=counts.values,
            marker=dict(color=counts.values, colorscale=theme.SEQUENTIAL, cornerradius=8),
        )
    )
    fig.update_layout(
        title=t("chart.combined_score"),
        xaxis_title=t("chart.score_x"), yaxis_title=t("chart.customers"),
    )
    return fig


def density_curve(rfm: pd.DataFrame, column: str, color: str) -> go.Figure:
    """Smoothed distribution (histogram + KDE-like line)."""
    values = rfm[column].dropna()
    hist, edges = np.histogram(values, bins=30, density=True)
    centers = (edges[:-1] + edges[1:]) / 2
    fig = go.Figure()
    fig.add_trace(go.Bar(x=centers, y=hist, marker_color=color, opacity=0.35, name=t("chart.histogram")))
    fig.add_trace(go.Scatter(x=centers, y=_smooth(hist), mode="lines", line=dict(color=color, width=3), name=t("chart.density_y")))
    fig.update_layout(title=t("chart.density", col=column), xaxis_title=column, yaxis_title=t("chart.density_y"))
    return fig


def _smooth(y: np.ndarray, window: int = 5) -> np.ndarray:
    if len(y) < window:
        return y
    kernel = np.ones(window) / window
    return np.convolve(y, kernel, mode="same")


# --------------------------------------------------------------------------- #
# Cluster-selection charts
# --------------------------------------------------------------------------- #
def elbow_chart(elbow: pd.DataFrame, chosen_k: int) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=elbow["k"], y=elbow["inertia"], mode="lines+markers",
            line=dict(color=theme.ACCENT, width=3), marker=dict(size=9, color=theme.ACCENT_2),
            name=t("chart.inertia"),
        )
    )
    fig.add_vline(x=chosen_k, line_dash="dash", line_color=theme.WARNING,
                  annotation_text=f"k = {chosen_k}", annotation_position="top")
    fig.update_layout(title=t("chart.elbow"), xaxis_title=t("chart.k_axis"), yaxis_title=t("chart.inertia"))
    return fig


def silhouette_chart(sil: pd.DataFrame, chosen_k: int) -> go.Figure:
    best_k = int(sil.loc[sil["silhouette"].idxmax(), "k"])
    colors = [theme.SUCCESS if k == best_k else theme.ACCENT for k in sil["k"]]
    fig = go.Figure(
        go.Bar(x=sil["k"], y=sil["silhouette"], marker=dict(color=colors, cornerradius=8))
    )
    fig.add_vline(x=chosen_k, line_dash="dash", line_color=theme.WARNING,
                  annotation_text=t("chart.selected_k", k=chosen_k), annotation_position="top")
    fig.update_layout(title=t("chart.sil_title"), xaxis_title=t("chart.k_axis"), yaxis_title=t("chart.silhouette"))
    return fig


# --------------------------------------------------------------------------- #
# Cluster charts
# --------------------------------------------------------------------------- #
def cluster_distribution(clustered: pd.DataFrame) -> go.Figure:
    counts = (
        clustered.groupby(["Segment", "SegmentEmoji"]).size()
        .reset_index(name="Customers").sort_values("Customers", ascending=True)
    )
    labels = counts["SegmentEmoji"] + " " + counts["Segment"]
    bar_colors = [theme.CATEGORICAL[i % len(theme.CATEGORICAL)] for i in range(len(counts))]
    fig = go.Figure(
        go.Bar(
            y=labels, x=counts["Customers"], orientation="h",
            marker=dict(color=bar_colors, cornerradius=8),
            text=counts["Customers"], textposition="outside",
        )
    )
    fig.update_layout(title=t("chart.cust_per_seg"), xaxis_title=t("chart.customers"), yaxis_title="")
    return fig


def cluster_scatter(clustered: pd.DataFrame) -> go.Figure:
    data = sample_for_plot(clustered, 4000)
    fig = px.scatter(
        data, x="Recency", y="Monetary", color="Segment", size="Frequency",
        color_discrete_sequence=theme.CATEGORICAL, size_max=22,
        hover_data=["CustomerName", "Frequency"], log_y=True,
    )
    fig.update_traces(marker=dict(line=dict(width=0.4, color="rgba(255,255,255,0.2)")))
    fig.update_layout(title=t("chart.scatter_title"))
    return fig


def pca_scatter(pca_df: pd.DataFrame) -> go.Figure:
    data = sample_for_plot(pca_df, 4000)
    fig = px.scatter(
        data, x="PC1", y="PC2", color="Segment",
        color_discrete_sequence=theme.CATEGORICAL,
        hover_data=["CustomerName", "Recency", "Frequency", "Monetary"],
    )
    fig.update_traces(marker=dict(size=7, line=dict(width=0.4, color="rgba(255,255,255,0.2)")))
    fig.update_layout(title=t("chart.pca_title"))
    return fig


def scatter_3d(clustered: pd.DataFrame) -> go.Figure:
    data = sample_for_plot(clustered, 3000)
    fig = px.scatter_3d(
        data, x="Recency", y="Frequency", z="Monetary", color="Segment",
        color_discrete_sequence=theme.CATEGORICAL,
        hover_data=["CustomerName"],
    )
    fig.update_traces(marker=dict(size=4, line=dict(width=0)))
    fig.update_layout(
        title=t("chart.d3_title"),
        scene=dict(
            xaxis_title="Recency", yaxis_title="Frequency", zaxis_title="Monetary",
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)"),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)"),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)"),
        ),
    )
    return fig


def avg_rfm_bars(profile: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    metrics = [("Avg_Recency", "Recency", theme.CATEGORICAL[3]),
               ("Avg_Frequency", "Frequency", theme.CATEGORICAL[2]),
               ("Avg_Monetary", "Monetary", theme.CATEGORICAL[0])]
    labels = profile["SegmentEmoji"] + " " + profile["Segment"]
    for col, name, color in metrics:
        # Scale to 0-100 within each metric for comparability on one axis.
        vals = profile[col]
        norm = (vals - vals.min()) / (vals.max() - vals.min() + 1e-9) * 100
        fig.add_trace(go.Bar(name=name, x=labels, y=norm, marker=dict(color=color, cornerradius=6)))
    fig.update_layout(title=t("chart.avg_rfm"), barmode="group", yaxis_title=t("chart.norm_0_100"))
    return fig


def radar_chart(profile: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    metrics = ["Avg_Recency", "Avg_Frequency", "Avg_Monetary"]
    axis = ["Recency", "Frequency", "Monetary"]
    norm = profile.copy()
    for col in metrics:
        v = norm[col]
        norm[col] = (v - v.min()) / (v.max() - v.min() + 1e-9) * 100
    # Invert recency so "outward = better" is intuitive.
    norm["Avg_Recency"] = 100 - norm["Avg_Recency"]
    fresh = t("chart.radar_fresh")
    for i, row in norm.iterrows():
        color = theme.CATEGORICAL[i % len(theme.CATEGORICAL)]
        fig.add_trace(
            go.Scatterpolar(
                r=[row["Avg_Recency"], row["Avg_Frequency"], row["Avg_Monetary"], row["Avg_Recency"]],
                theta=[fresh, "Frequency", "Monetary", fresh],
                fill="toself", name=f"{row['SegmentEmoji']} {row['Segment']}",
                line=dict(color=color, width=2), opacity=0.75,
            )
        )
    fig.update_layout(
        title=t("chart.radar"),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(148,163,184,0.2)"),
            angularaxis=dict(gridcolor="rgba(148,163,184,0.2)"),
        ),
    )
    return fig


def parallel_coordinates(clustered: pd.DataFrame) -> go.Figure:
    data = sample_for_plot(clustered, 4000)
    fig = px.parallel_coordinates(
        data, dimensions=RFM, color="Cluster",
        color_continuous_scale=theme.SEQUENTIAL,
    )
    fig.update_layout(title=t("chart.parallel"))
    return fig


# --------------------------------------------------------------------------- #
# Customer-insight charts
# --------------------------------------------------------------------------- #
def segment_treemap(clustered: pd.DataFrame) -> go.Figure:
    from components.metrics import format_rupiah

    grp = (
        clustered.groupby(["Segment", "SegmentEmoji"])
        .agg(Customers=("CustomerID", "count"), Revenue=("Monetary", "sum"))
        .reset_index()
    )
    grp["Label"] = grp["SegmentEmoji"] + " " + grp["Segment"]
    grp["RevenueLabel"] = grp["Revenue"].apply(lambda v: format_rupiah(v, short=False))
    fig = px.treemap(
        grp, path=["Label"], values="Revenue", color="Customers",
        color_continuous_scale=theme.SEQUENTIAL,
        custom_data=["RevenueLabel"],
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{customdata[0]}<br>%{percentRoot}",
        textfont_size=13,
        marker=dict(cornerradius=8),
        hovertemplate=(
            "%{label}<br>Revenue: %{customdata[0]}<br>"
            "Customers: %{color:,.0f}<br>Share: %{percentRoot}<extra></extra>"
        ),
    )
    fig.update_layout(title=t("chart.treemap"))
    return fig


def segment_donut(clustered: pd.DataFrame) -> go.Figure:
    grp = clustered["Segment"].value_counts()
    fig = go.Figure(
        go.Pie(
            labels=grp.index, values=grp.values, hole=0.62,
            marker=dict(colors=theme.CATEGORICAL, line=dict(color="rgba(8,20,40,0.6)", width=2)),
            textinfo="percent", textfont_size=13,
        )
    )
    fig.update_layout(
        title=t("chart.donut"),
        annotations=[dict(text=f"{grp.sum():,}<br>{t('chart.customers')}", x=0.5, y=0.5,
                          font_size=15, showarrow=False, font_color="#E2E8F0")],
    )
    return fig


def segment_sunburst(clustered: pd.DataFrame) -> go.Figure:
    df = clustered.copy()
    tiers = [t("chart.low_spend"), t("chart.mid_spend"), t("chart.high_spend")]
    # Quantile-based (not equal-width) bins: Monetary spans from ~15K to
    # hundreds of millions once the High Value Segment is included, so
    # equal-width bins would collapse almost everyone into a single tier.
    try:
        df["ValueTier"] = pd.qcut(df["Monetary"], q=3, labels=tiers, duplicates="drop").astype(str)
    except ValueError:
        df["ValueTier"] = pd.cut(df["Monetary"], bins=3, labels=tiers).astype(str)
    grp = (
        df.groupby(["Segment", "ValueTier"]).size().reset_index(name="Customers")
    )
    fig = px.sunburst(
        grp, path=["Segment", "ValueTier"], values="Customers",
        color="Customers", color_continuous_scale=theme.SEQUENTIAL,
    )
    fig.update_traces(marker=dict(line=dict(color="rgba(8,20,40,0.6)", width=1)))
    fig.update_layout(title=t("chart.sunburst"))
    return fig


def _recency_band(df: pd.DataFrame) -> pd.Series:
    return pd.cut(df["Recency"], bins=RECENCY_BINS, labels=RECENCY_LABELS, include_lowest=True)


def revenue_by_recency(clustered: pd.DataFrame) -> go.Figure:
    """Revenue distribution across recency bands (replaces the time trend, since
    the source data is customer-level, not transaction-level)."""
    df = clustered.copy()
    df["Band"] = _recency_band(df)
    grp = df.groupby("Band", observed=False)["Monetary"].sum().reindex(RECENCY_LABELS)
    fig = go.Figure(
        go.Bar(
            x=RECENCY_LABELS, y=grp.values,
            marker=dict(color=grp.values, colorscale=theme.SEQUENTIAL, cornerradius=8),
            text=[f"Rp {v/1e9:.1f}B" for v in grp.values], textposition="outside",
        )
    )
    fig.update_layout(
        title=t("chart.rev_recency"),
        xaxis_title=t("chart.days_since"), yaxis_title=t("chart.revenue_rp"),
    )
    return fig


def customers_by_recency(clustered: pd.DataFrame) -> go.Figure:
    df = clustered.copy()
    df["Band"] = _recency_band(df)
    grp = df.groupby("Band", observed=False).size().reindex(RECENCY_LABELS)
    fig = go.Figure(
        go.Scatter(
            x=RECENCY_LABELS, y=grp.values, mode="lines+markers",
            line=dict(color=theme.ACCENT, width=3, shape="spline"),
            marker=dict(size=9, color=theme.ACCENT_2),
            fill="tozeroy", fillcolor="rgba(46,110,247,0.15)",
        )
    )
    fig.update_layout(title=t("chart.cust_recency"), xaxis_title="", yaxis_title=t("chart.customers"))
    return fig


def engagement_by_segment(clustered: pd.DataFrame) -> go.Figure:
    """Average marketing-engagement score per segment (from real engagement data)."""
    grp = (
        clustered.groupby(["Segment", "SegmentEmoji"])
        .agg(Engagement=("EngagementScore", "mean"), OpenRate=("EmailOpenRate", "mean"))
        .reset_index().sort_values("Engagement", ascending=True)
    )
    labels = grp["SegmentEmoji"] + " " + grp["Segment"]
    bar_colors = [theme.CATEGORICAL[i % len(theme.CATEGORICAL)] for i in range(len(grp))]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=grp["Engagement"], orientation="h", name=t("chart.engagement"),
        marker=dict(color=bar_colors, cornerradius=8),
        text=[f"{v:.0f}" for v in grp["Engagement"]], textposition="outside",
    ))
    fig.update_layout(title=t("chart.engagement"), xaxis_title=t("chart.engagement_x"), yaxis_title="")
    return fig
