"""
utils/loader.py
---------------
Data-access layer. Loads the real PlanetSports.Asia customer export, cleans it,
computes RFM scores and K-Means segments — all cached so heavy work runs once.

If the real CSV is missing it falls back to a synthetic generator, so
`streamlit run app.py` always works.

The cleaned artefacts are also written to `data/` (customer_data.csv, rfm.csv,
clustered_data.csv) to match the required project structure.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from utils import preprocessing as pp

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_BASE_DIR, "data")

# Real source export (anonymised customer-level data).
REAL_CSV_CANDIDATES = [
    os.path.join(_BASE_DIR, "RAW Data_Planet Sports Asia.csv"),
    os.path.join(DATA_DIR, "RAW Data_Planet Sports Asia.csv"),
]

CUSTOMER_CSV = os.path.join(DATA_DIR, "customer_data.csv")
RFM_CSV = os.path.join(DATA_DIR, "rfm.csv")
CLUSTERED_CSV = os.path.join(DATA_DIR, "clustered_data.csv")

DEFAULT_N_CLUSTERS = 3  # thesis-optimal k (Elbow + Silhouette peak at k=3)


def _real_csv_path() -> str | None:
    for path in REAL_CSV_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


@st.cache_data(show_spinner=False)
def load_customers() -> pd.DataFrame:
    """Cleaned per-customer table (RFM fields + engagement)."""
    real = _real_csv_path()
    customers = pp.load_customers(real) if real else pp.generate_synthetic_customers()

    # Persist the cleaned customer artefact (project-structure requirement).
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        customers.to_csv(CUSTOMER_CSV, index=False)
    except OSError:
        pass
    return customers


@st.cache_data(show_spinner=False)
def load_rfm() -> pd.DataFrame:
    """Per-customer RFM table with 1–5 scores."""
    rfm = pp.score_rfm(load_customers())
    try:
        rfm.to_csv(RFM_CSV, index=False)
    except OSError:
        pass
    return rfm


@st.cache_data(show_spinner=False)
def load_clustered(n_clusters: int = DEFAULT_N_CLUSTERS) -> pd.DataFrame:
    """RFM table enriched with the full segmentation result: the High Value
    Segment (outlier-based, separated first) plus the k-cluster K-Means
    result on the remaining regular customers. See `preprocessing.build_segments`."""
    clustered = pp.build_segments(load_rfm(), n_clusters=n_clusters)
    try:
        clustered.to_csv(CLUSTERED_CSV, index=False)
    except OSError:
        pass
    return clustered


@st.cache_data(show_spinner=False)
def recluster(n_clusters: int) -> pd.DataFrame:
    """Re-run the full segmentation pipeline for an arbitrary k."""
    if n_clusters == DEFAULT_N_CLUSTERS:
        return load_clustered(n_clusters)  # also writes the CSV artefact
    return pp.build_segments(load_rfm(), n_clusters=n_clusters)


@st.cache_data(show_spinner=False)
def load_all(n_clusters: int = DEFAULT_N_CLUSTERS) -> dict[str, pd.DataFrame]:
    """Convenience bundle used by the landing page."""
    return {
        "customers": load_customers(),
        "rfm": load_rfm(),
        "clustered": recluster(n_clusters),
    }


@st.cache_data(show_spinner=False)
def get_elbow(_rfm_hash: int) -> pd.DataFrame:
    """Cached elbow-method curve. `_rfm_hash` keys the cache."""
    return pp.elbow_scores(load_rfm())


@st.cache_data(show_spinner=False)
def get_silhouette(_rfm_hash: int) -> pd.DataFrame:
    """Cached silhouette curve."""
    return pp.silhouette_scores(load_rfm())


def is_real_data() -> bool:
    """True when the real customer export is being used."""
    return _real_csv_path() is not None
