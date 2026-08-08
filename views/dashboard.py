"""
views/dashboard.py — Dashboard (merged Home + Overview).

Thesis: "Customer Segmentation Analysis Using RFM Model and K-Means Clustering
on PlanetSports.Asia Website Using Streamlit" (CRISP-DM · Deployment phase).

This is the landing page of the storytelling flow:
Dashboard → RFM Analysis → K-Means Clustering → Customer Segments → Business
Recommendations.

It combines the former "Home" hero/KPI snapshot with the former "Overview"
live filters + customer directory, so there is exactly one KPI cockpit and
one revenue/segment snapshot in the whole app instead of two near-identical
copies.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from components import cards, charts
from components.metrics import compute_overview_kpis, format_rupiah
from components.tables import download_button, interactive_table
from utils import loader
from utils.i18n import t

# --------------------------------------------------------------------------- #
# Data — always the thesis-optimal k = 3 clustering.
# --------------------------------------------------------------------------- #
try:
    with st.spinner("Preparing customer intelligence…"):
        clustered_full = loader.load_clustered()
except Exception as exc:  # pragma: no cover - defensive
    st.error(f"❌ Failed to load data: {exc}")
    st.stop()

_src_key = "common.data_real" if loader.is_real_data() else "common.data_synth"

# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
cards.page_hero(eyebrow=t("home.eyebrow"), title=t("home.title"), subtitle=t("home.subtitle"))
st.markdown(
    f'<span class="pill">📦 {t(_src_key, n=f"{len(clustered_full):,}")}</span>',
    unsafe_allow_html=True,
)
st.write("")

# --------------------------------------------------------------------------- #
# Live filters — every visual + table below updates automatically.
# --------------------------------------------------------------------------- #
cards.section_header(t("ov.filters"), t("ov.filters_sub"))
f1, f2, f3 = st.columns([1.2, 1, 1])

rec_min, rec_max = int(clustered_full["Recency"].min()), int(clustered_full["Recency"].max())
with f1:
    rec_range = st.slider(
        t("ov.recency"), min_value=rec_min, max_value=rec_max, value=(rec_min, rec_max),
    )
with f2:
    segments = sorted(clustered_full["Segment"].unique().tolist())
    seg_filter = st.multiselect(t("ov.segment"), options=segments, default=segments)
with f3:
    cust_query = st.text_input(t("ov.search"), placeholder=t("ov.search_ph"))

view = clustered_full[
    (clustered_full["Recency"] >= rec_range[0]) & (clustered_full["Recency"] <= rec_range[1])
]
view = view[view["Segment"].isin(seg_filter)] if seg_filter else view.iloc[0:0]
if cust_query:
    q = cust_query.lower()
    view = view[
        view["CustomerID"].str.lower().str.contains(q)
        | view["HashID"].str.lower().str.contains(q)
    ]

if view.empty:
    cards.empty_state(t("ov.empty"), "🫙")
    cards.footer()
    st.stop()

# --------------------------------------------------------------------------- #
# KPIs (computed on the filtered slice)
# --------------------------------------------------------------------------- #
kpis = compute_overview_kpis(view)
cards.section_header(t("ov.key_metrics"))
cards.kpi_row(kpis[:3])
cards.kpi_row(kpis[3:])
st.write("")

# --------------------------------------------------------------------------- #
# Snapshot: revenue by recency + segment share (single instance — the
# duplicate copy that used to live on the old Overview page has been removed)
# --------------------------------------------------------------------------- #
c1, c2 = st.columns([1.4, 1])
with c1:
    cards.section_header(t("home.revenue_recency"), t("home.revenue_recency_sub"))
    charts.render(charts.revenue_by_recency(view), height=340)
with c2:
    cards.section_header(t("home.segment_share"), t("home.segment_share_sub"))
    charts.render(charts.segment_donut(view), height=340)

# --------------------------------------------------------------------------- #
# Customer directory
# --------------------------------------------------------------------------- #
cards.section_header(t("ov.directory"), t("ov.directory_sub"))
directory = (
    view.sort_values("Monetary", ascending=False)
    .head(300)[
        ["CustomerID", "Recency", "Frequency", "Monetary", "RFM_Score",
         "EngagementScore", "Segment"]
    ]
    .rename(columns={"EngagementScore": "Engagement"})
)
directory["Monetary"] = directory["Monetary"].round(0)
interactive_table(directory, height=380, page_size=10, key="dashboard_directory")
download_button(directory, "customer_directory.csv")

with st.expander(t("ov.summary")):
    st.markdown(
        f"""
        - **{t('ov.sum_customers')}:** {view['CustomerID'].nunique():,}
        - **{t('ov.sum_orders')}:** {int(view['Frequency'].sum()):,}
        - **{t('ov.sum_revenue')}:** {format_rupiah(view['Monetary'].sum(), short=False)}
        - **{t('ov.sum_aov')}:** {format_rupiah(view['Monetary'].sum() / max(1, view['Frequency'].sum()), short=False)}
        - **{t('ov.sum_segments')}:** {', '.join(sorted(view['Segment'].unique()))}
        """
    )

# --------------------------------------------------------------------------- #
# Navigation guide — real, working links into the rest of the story.
# --------------------------------------------------------------------------- #
cards.section_header(t("home.explore"), t("home.explore_sub"))
nav_cols = st.columns(2)
guide = [
    ("views/rfm_analysis.py", None, t("nav.rfm"), t("nav.rfm_desc")),
    ("views/kmeans_clustering.py", None, t("nav.cluster"), t("nav.cluster_desc")),
    ("views/customer_segments.py", None, t("nav.segments"), t("nav.segments_desc")),
    ("views/business_recommendations.py", None, t("nav.recommend"), t("nav.recommend_desc")),
]
for i, (path, icon, title, desc) in enumerate(guide):
    with nav_cols[i % 2]:
        cards.nav_link_card(path, icon, title, desc, key=f"navcard_{i}")

cards.footer()
