"""
views/business_recommendations.py — CRM Decision Support System.

Step 5 (final) of the story: Dashboard → RFM Analysis → K-Means Clustering →
Customer Segments → **Business Recommendations**.

Nothing on this page is a static, hardcoded-per-segment playbook. Every
customer summary and marketing action is generated at runtime by
`utils/recommendation_engine.py`, which classifies each segment's real RFM +
engagement averages against a data-driven population baseline and evaluates
a rule catalogue against them. This view is intentionally "dumb" — it only
orchestrates engine calls and hands the results to `components/cards.py`
for rendering.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from components import cards
from utils import loader
from utils import preprocessing as pp
from utils import recommendation_engine as eng
from utils.i18n import get_lang, t

lang = get_lang()

clustered = loader.load_clustered()
profile = pp.cluster_profile(clustered)
baseline = eng.population_baseline(clustered)
metric_means = eng.segment_metric_means(clustered)

cards.page_hero(eyebrow=t("br.eyebrow"), title=t("br.title"), subtitle=t("br.subtitle"))
st.write("")

SECTION_LABELS = {
    "summary": t("br.summary"), "strategy": t("br.strategy"),
    "why": t("br.why"), "outcome": t("br.outcome"),
}

# --------------------------------------------------------------------------- #
# Run the engine once per segment. `priority` is still computed to decide
# display order (highest-impact segment first) even though the star badge
# itself is no longer shown on the card.
# --------------------------------------------------------------------------- #
engine_results: dict[str, dict] = {}
for _, mrow in metric_means.iterrows():
    segment = mrow["Segment"]
    levels = eng.segment_levels(mrow, baseline)
    triggered = eng.evaluate(levels)
    prow = profile[profile["Segment"] == segment].iloc[0]
    priority = eng.priority_score(triggered, prow["Revenue_Share"], prow["Customer_Share"])
    engine_results[segment] = {
        "levels": levels, "triggered": triggered, "priority": priority,
        "profile_row": prow,
    }

ordered_segments = sorted(
    engine_results.keys(), key=lambda s: engine_results[s]["priority"]["score"], reverse=True
)

for segment in ordered_segments:
    res = engine_results[segment]
    prow, levels, triggered = res["profile_row"], res["levels"], res["triggered"]

    actions = eng.build_action_plan(triggered)

    data = {
        "emoji": prow["SegmentEmoji"],
        "name": segment,
        "meta": t("br.meta", n=int(prow["Customers"]), cs=prow["Customer_Share"], rs=prow["Revenue_Share"]),
        "summary": eng.customer_summary(prow, levels, lang),
        "actions": [
            {
                "name": eng.L(a["strategy"].name, lang), "why": eng.L(a["strategy"].why, lang),
                "outcome": eng.L(a["strategy"].outcome, lang), "channel": a["strategy"].channel,
                "tier": a["tier"],
            }
            for a in actions
        ],
        "labels": SECTION_LABELS,
    }
    cards.business_recommendation_card(data)

# --------------------------------------------------------------------------- #
# Strategic Insights — generated from the actual computed engine results.
# --------------------------------------------------------------------------- #
insights = eng.strategic_insights(profile, engine_results, lang)
cards.strategic_insight_panel(t("br.insights_title"), insights)

cards.footer()
