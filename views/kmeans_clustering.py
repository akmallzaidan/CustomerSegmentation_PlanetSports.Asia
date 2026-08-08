"""
views/kmeans_clustering.py — Cluster diagnostics & multi-view cluster analysis.

Step 3 of the story: Dashboard → RFM Analysis → **K-Means Clustering** →
Customer Segments → Business Recommendations.

Mirrors the thesis notebook exactly: the High Value Segment (Monetary IQR
outliers OR Frequency > p99) is separated out *before* clustering, so K-Means
is trained and diagnosed on the regular customer base only. The model always
uses the thesis-optimal k = 3 — there is no cluster-count selector.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from components import cards, charts
from components.tables import download_button, interactive_table
from utils import loader
from utils import preprocessing as pp
from utils.i18n import t

K = loader.DEFAULT_N_CLUSTERS  # thesis-optimal k = 3 (Elbow + Silhouette peak)

rfm = loader.load_rfm()
clustered_full = loader.load_clustered()
# K-Means was trained on regular customers only — the High Value Segment
# (Cluster = -1) is analyzed separately, on Business Recommendations.
clustered = clustered_full[clustered_full["Cluster"] >= 0].copy()
n_high_value = int((clustered_full["Cluster"] == -1).sum())

cards.page_hero(eyebrow=t("cl.eyebrow"), title=t("cl.title"), subtitle=t("cl.subtitle", k=K))
st.markdown(
    f'<span class="pill">💎 {t("cl.hv_excluded", n=f"{n_high_value:,}")}</span>',
    unsafe_allow_html=True,
)
st.write("")

# --------------------------------------------------------------------------- #
# Cluster selection diagnostics — why k = 3 (computed on regular customers)
# --------------------------------------------------------------------------- #
cards.section_header(t("cl.howmany"), t("cl.howmany_sub"))
e1, e2 = st.columns(2)
with e1:
    elbow = loader.get_elbow(len(rfm))
    charts.render(charts.elbow_chart(elbow, K), height=340)
    cards.chart_caption(t("cl.cap_elbow"))
with e2:
    sil = loader.get_silhouette(len(rfm))
    best_k = int(sil.loc[sil["silhouette"].idxmax(), "k"])
    charts.render(charts.silhouette_chart(sil, K), height=340)
    cards.chart_caption(t("cl.cap_sil", k=best_k))

# --------------------------------------------------------------------------- #
# Cluster sizes + separation (PCA and 3D — the raw Recency-vs-Monetary bubble
# scatter that used to sit here was a lower-fidelity duplicate of the PCA
# projection below, so it has been retired).
# --------------------------------------------------------------------------- #
cards.section_header(t("cl.sizes"), t("cl.sizes_sub"))
charts.render(charts.cluster_distribution(clustered), height=380)
cards.chart_caption(t("cl.cap_sizes"))

p1, p2 = st.columns(2)
with p1:
    cards.section_header(t("cl.pca"), t("cl.pca_sub"))
    pca_df = pp.pca_projection(clustered)
    charts.render(charts.pca_scatter(pca_df), height=400)
    cards.chart_caption(t("cl.cap_pca"))
with p2:
    cards.section_header(t("cl.d3"), t("cl.d3_sub"))
    charts.render(charts.scatter_3d(clustered), height=400)
    cards.chart_caption(t("cl.cap_d3"))

# --------------------------------------------------------------------------- #
# Cluster profile table
# --------------------------------------------------------------------------- #
profile = pp.cluster_profile(clustered, total_revenue=clustered_full["Monetary"].sum())

cards.section_header(t("cl.table"), t("cl.table_sub"))
cards.chart_caption(t("cl.cap_table_rev"))
show = profile.rename(columns={
    "SegmentEmoji": "",
    "Avg_Recency": "Avg Recency (d)",
    "Avg_Frequency": "Avg Frequency",
    "Avg_Monetary": "Avg Monetary (Rp)",
    "Total_Revenue": "Total Revenue (Rp)",
    "Revenue_Share": "Revenue %",
    "Customer_Share": "Customer %",
})
interactive_table(show, height=320, page_size=8, key="cluster_profile")
download_button(profile, "cluster_profile.csv")

cards.footer()
