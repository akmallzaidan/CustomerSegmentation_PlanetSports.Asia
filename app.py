"""
app.py — PlanetSports.Asia Customer Segmentation Dashboard
==========================================================
Entry point / router.

Thesis: "Customer Segmentation Analysis Using RFM Model and K-Means Clustering
on PlanetSports.Asia Website Using Streamlit" (CRISP-DM · Deployment phase).

Uses `st.navigation()` so the sidebar shows exactly five labelled pages in a
fixed story order — Dashboard, RFM Analysis, K-Means Clustering, Customer
Segments, Business Recommendations — with no separate "Overview" entry and
no reliance on raw filenames for the nav labels.

Run:  streamlit run app.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from components import sidebar, theme

theme.configure_app(title="PlanetSports.Asia Analytics", icon="assets/LOGO_PSA.png")

pages = [
    st.Page("views/dashboard.py", title="Dashboard", default=True),
    st.Page("views/rfm_analysis.py", title="RFM Analysis", ),
    st.Page("views/kmeans_clustering.py", title="K-Means Clustering"),
    st.Page("views/customer_segments.py", title="Customer Segments"),
    st.Page("views/business_recommendations.py", title="Business Recommendations"),
]
nav = st.navigation(pages)

sidebar.render_sidebar()

nav.run()
