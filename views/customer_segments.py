"""
views/customer_segments.py — Customer insight: top customers, composition,
detail table with search & export.

Step 4 of the story: Dashboard → RFM Analysis → K-Means Clustering →
**Customer Segments** → Business Recommendations.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from components import cards, charts
from components.metrics import format_rupiah
from components.tables import download_button, interactive_table
from utils import loader
from utils.i18n import t

clustered = loader.load_clustered()

cards.page_hero(eyebrow=t("cs.eyebrow"), title=t("cs.title"), subtitle=t("cs.subtitle"))

# --------------------------------------------------------------------------- #
# Top customers
# --------------------------------------------------------------------------- #
cards.section_header(t("cs.top"), t("cs.top_sub"))
t1, t2, t3 = st.columns(3)

with t1:
    st.markdown(f'<div class="pill">{t("cs.largest")}</div>', unsafe_allow_html=True)
    top_money = clustered.nlargest(5, "Monetary")[["CustomerName", "Segment", "Monetary"]]
    for _, r in top_money.iterrows():
        st.markdown(
            f"""<div class="glass-card" style="margin:8px 0;padding:12px 16px;">
            <b>{r['CustomerName']}</b><br>
            <span class="muted" style="font-size:0.8rem;">{r['Segment']}</span>
            <div style="color:#38BDF8;font-weight:700;">{format_rupiah(r['Monetary'], short=False)}</div>
            </div>""",
            unsafe_allow_html=True,
        )

with t2:
    st.markdown(f'<div class="pill">{t("cs.frequent")}</div>', unsafe_allow_html=True)
    top_freq = clustered.nlargest(5, "Frequency")[["CustomerName", "Segment", "Frequency"]]
    for _, r in top_freq.iterrows():
        st.markdown(
            f"""<div class="glass-card" style="margin:8px 0;padding:12px 16px;">
            <b>{r['CustomerName']}</b><br>
            <span class="muted" style="font-size:0.8rem;">{r['Segment']}</span>
            <div style="color:#22C55E;font-weight:700;">{t("cs.orders", n=int(r['Frequency']))}</div>
            </div>""",
            unsafe_allow_html=True,
        )

with t3:
    st.markdown(f'<div class="pill">{t("cs.recent")}</div>', unsafe_allow_html=True)
    top_recent = clustered.nsmallest(5, "Recency")[["CustomerName", "Segment", "Recency"]]
    for _, r in top_recent.iterrows():
        st.markdown(
            f"""<div class="glass-card" style="margin:8px 0;padding:12px 16px;">
            <b>{r['CustomerName']}</b><br>
            <span class="muted" style="font-size:0.8rem;">{r['Segment']}</span>
            <div style="color:#F59E0B;font-weight:700;">{t("cs.days_ago", n=int(r['Recency']))}</div>
            </div>""",
            unsafe_allow_html=True,
        )

# --------------------------------------------------------------------------- #
# Segment composition: treemap + sunburst (the segment-share donut that used
# to sit here duplicated the one on the Dashboard page, so it has been
# retired in favour of these two more analytical, non-duplicated views).
# --------------------------------------------------------------------------- #
cards.section_header(t("cs.composition"), t("cs.composition_sub"))
charts.render(charts.segment_treemap(clustered), height=420)
cards.chart_caption(t("cs.cap_treemap"))

cards.section_header(t("cs.tier"), t("cs.tier_sub"))
charts.render(charts.segment_sunburst(clustered), height=430)
cards.chart_caption(t("cs.cap_sunburst"))

# --------------------------------------------------------------------------- #
# Marketing engagement (from the real engagement counters)
# --------------------------------------------------------------------------- #
cards.section_header(t("cs.engagement"), t("cs.engagement_sub"))
charts.render(charts.engagement_by_segment(clustered), height=360)
cards.chart_caption(t("cs.cap_engagement"))

# --------------------------------------------------------------------------- #
# Customer detail table with search + export
# --------------------------------------------------------------------------- #
cards.section_header(t("cs.detail"), t("cs.detail_sub"))

s1, s2 = st.columns([1, 1])
with s1:
    search = st.text_input(t("cs.search"), placeholder=t("cs.search_ph"))
with s2:
    seg_pick = st.multiselect(
        t("cs.filter_segment"),
        options=sorted(clustered["Segment"].unique().tolist()),
        default=sorted(clustered["Segment"].unique().tolist()),
    )

detail = clustered[clustered["Segment"].isin(seg_pick)] if seg_pick else clustered.iloc[0:0]
if search:
    q = search.lower()
    detail = detail[
        detail["CustomerName"].str.lower().str.contains(q)
        | detail["CustomerID"].str.lower().str.contains(q)
    ]

detail_view = detail[
    ["CustomerID", "Recency", "Frequency", "Monetary",
     "RFM_Score", "EngagementScore", "EmailOpenRate", "Segment"]
].copy()
detail_view["Monetary"] = detail_view["Monetary"].round(0)
detail_view["EmailOpenRate"] = detail_view["EmailOpenRate"].round(1)
detail_view = detail_view.rename(columns={"EngagementScore": "Engagement", "EmailOpenRate": "Email Open %"})

if detail_view.empty:
    cards.empty_state(t("cs.empty"), "🔍")
else:
    interactive_table(detail_view, height=440, page_size=12, key="segment_detail")
    download_button(detail_view, "customer_segments.csv")

cards.footer()
