"""
components/metrics.py
---------------------
Formatting helpers and KPI aggregation logic. Keeps number formatting and the
Overview KPI definitions in one place so every page is consistent.
"""

from __future__ import annotations

import pandas as pd


def format_rupiah(value: float, short: bool = True) -> str:
    """Format a number as Indonesian Rupiah, optionally abbreviated."""
    if short:
        if abs(value) >= 1_000_000_000:
            return f"Rp {value / 1_000_000_000:.2f} B"
        if abs(value) >= 1_000_000:
            return f"Rp {value / 1_000_000:.1f} M"
        if abs(value) >= 1_000:
            return f"Rp {value / 1_000:.0f} K"
    return f"Rp {value:,.0f}"


def format_number(value: float, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}"


def compute_overview_kpis(clustered: pd.DataFrame) -> list[dict]:
    """Build the six KPI-card definitions for the Dashboard page."""
    from utils.i18n import t

    total_customers = clustered["CustomerID"].nunique()
    total_revenue = clustered["Monetary"].sum()
    avg_monetary = clustered["Monetary"].mean()
    avg_frequency = clustered["Frequency"].mean()
    avg_recency = clustered["Recency"].mean()
    n_clusters = clustered["Cluster"].nunique()
    total_orders = int(clustered["Frequency"].sum())

    return [
        {
            "label": t("kpi.total_customers"),
            "value": format_number(total_customers),
            "icon": "groups",
            "delta": t("kpi.active_base"),
            "direction": "up",
        },
        {
            "label": t("kpi.total_revenue"),
            "value": format_rupiah(total_revenue),
            "icon": "payments",
            "delta": t("kpi.orders", n=f"{total_orders:,}"),
            "direction": "up",
        },
        {
            "label": t("kpi.avg_monetary"),
            "value": format_rupiah(avg_monetary),
            "icon": "account_balance_wallet",
            "delta": t("kpi.per_customer"),
            "direction": "flat",
        },
        {
            "label": t("kpi.avg_frequency"),
            "value": f"{avg_frequency:.1f}",
            "icon": "repeat",
            "delta": t("kpi.orders_per_customer"),
            "direction": "flat",
        },
        {
            "label": t("kpi.avg_recency"),
            "value": f"{avg_recency:.0f} d",
            "icon": "schedule",
            "delta": t("kpi.since_last_buy"),
            "direction": "down",
        },
        {
            "label": t("kpi.segments"),
            "value": str(n_clusters),
            "icon": "hub",
            "delta": t("kpi.kmeans_clusters"),
            "direction": "flat",
        },
    ]
