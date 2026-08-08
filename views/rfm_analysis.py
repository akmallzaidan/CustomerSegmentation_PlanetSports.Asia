"""
views/rfm_analysis.py — RFM distributions, correlations and scoring.

Step 2 of the story: Dashboard → **RFM Analysis** → K-Means Clustering →
Customer Segments → Business Recommendations.

Distributions below are computed on the *regular* customer base (High Value
outliers removed first) — exactly like the notebook's "after separating the
High Value Segment" charts. Without this split, a handful of extreme
Frequency/Monetary outliers compress every other customer into a single
bar, making the whole distribution look sharply right-skewed even though
the regular customer base is fairly evenly spread.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from components import cards, charts, theme
from components.tables import download_button, interactive_table
from utils import loader
from utils import preprocessing as pp
from utils.i18n import t

rfm_all = loader.load_rfm()
rfm, rfm_hv = pp.split_high_value(rfm_all)

cards.page_hero(eyebrow=t("rfm.eyebrow"), title=t("rfm.title"), subtitle=t("rfm.subtitle"))
st.markdown(
    f'<span class="pill">💎 {t("rfm.hv_excluded", n=f"{len(rfm_hv):,}")}</span>',
    unsafe_allow_html=True,
)
st.write("")

# --------------------------------------------------------------------------- #
# Distributions
# --------------------------------------------------------------------------- #
cards.section_header(t("rfm.distributions"), t("rfm.distributions_sub"))
h1, h2, h3 = st.columns(3)
with h1:
    charts.render(charts.rfm_histogram(rfm, "Recency", theme.CATEGORICAL[3]), height=320)
    cards.chart_caption(t("rfm.cap_recency"))
with h2:
    charts.render(charts.rfm_histogram(rfm, "Frequency", theme.CATEGORICAL[2]), height=320)
    cards.chart_caption(t("rfm.cap_frequency"))
with h3:
    charts.render(charts.rfm_histogram(rfm, "Monetary", theme.CATEGORICAL[0]), height=320)
    cards.chart_caption(t("rfm.cap_monetary"))

# --------------------------------------------------------------------------- #
# Boxplot + correlation
# --------------------------------------------------------------------------- #
b1, b2 = st.columns(2)
with b1:
    cards.section_header(t("rfm.spread"), t("rfm.spread_sub"))
    charts.render(charts.rfm_boxplot(rfm), height=360)
    cards.chart_caption(t("rfm.cap_box"))
with b2:
    cards.section_header(t("rfm.correlation"), t("rfm.correlation_sub"))
    charts.render(charts.correlation_heatmap(rfm), height=360)
    cards.chart_caption(t("rfm.cap_corr"))

# --------------------------------------------------------------------------- #
# Combined RFM score distribution — the single-metric Monetary density curve
# that used to sit here was a near-duplicate of the Monetary histogram above,
# so it has been retired in favour of this distinct, higher-signal view.
# --------------------------------------------------------------------------- #
cards.section_header(t("rfm.score_dist"), t("rfm.score_dist_sub"))
charts.render(charts.rfm_score_distribution(rfm), height=360)
cards.chart_caption(t("rfm.cap_score"))

# --------------------------------------------------------------------------- #
# Summary table
# --------------------------------------------------------------------------- #
cards.section_header(t("rfm.table"), t("rfm.table_sub"))
table = rfm[
    ["CustomerID", "Recency", "Frequency", "Monetary",
     "R_Score", "F_Score", "M_Score", "RFM_Score", "RFM_Sum"]
].copy()
table["Monetary"] = table["Monetary"].round(0)
interactive_table(table, height=430, page_size=12, key="rfm_table")
download_button(table, "rfm_summary.csv")

with st.expander(t("rfm.describe")):
    st.dataframe(
        rfm[["Recency", "Frequency", "Monetary"]].describe().round(1),
        use_container_width=True,
    )

cards.footer()
