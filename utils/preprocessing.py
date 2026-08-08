"""
utils/preprocessing.py
----------------------
Core data-science logic for the PlanetSports.Asia customer-segmentation
dashboard.

Primary data source is the real, anonymised customer export
(`RAW Data_Planet Sports Asia.csv`) which is already aggregated to one row per
customer with RFM-ready fields:

    day_since_last_trx  -> Recency
    count_trx           -> Frequency
    net_sales (Rp…)     -> Monetary

plus a set of engagement counters (emails, site activity, content clicks…).

If that file is unavailable, a realistic synthetic generator is used as a
fallback so the app always runs.

Responsibilities:
    * Load & clean the real customer table (parse Rupiah, derive engagement).
    * Score customers on the classic 5-quantile RFM scale.
    * Run K-Means clustering (with scaling) and label segments.
    * Provide helper analytics: elbow / silhouette curves, PCA projection.

All functions are pure (no Streamlit imports) so they can be unit-tested and
cached from the loader layer.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MinMaxScaler

RANDOM_STATE = 42
RFM_FEATURES = ["Recency", "Frequency", "Monetary"]

ENGAGEMENT_COLS = [
    "SiteActivity", "EmailReceived", "EmailOpened", "ContentClicked",
    "ProductViewed", "CouponReceived", "EmailClicked", "CampaignUnsubscribed",
    "SpamMarked", "ChatDelivered",
]


# --------------------------------------------------------------------------- #
# 1. Real data loading & cleaning
# --------------------------------------------------------------------------- #
def parse_rupiah(series: pd.Series) -> pd.Series:
    """Convert values like 'Rp15,676' into floats."""
    cleaned = (
        series.astype(str)
        .str.replace("Rp", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def load_customers(path: str) -> pd.DataFrame:
    """Load and clean the real PlanetSports.Asia customer export."""
    raw = pd.read_csv(path)

    out = pd.DataFrame()
    out["HashID"] = raw["customer_id"].astype(str)
    out["CustomerID"] = [f"CUST-{i + 1:05d}" for i in range(len(raw))]
    # Data is anonymised (hashed IDs); use a stable display label.
    out["CustomerName"] = [f"Customer {i + 1:05d}" for i in range(len(raw))]
    out["Channel"] = raw.get("channel_code", "PlanetSports.Asia")

    out["Recency"] = pd.to_numeric(raw["day_since_last_trx"], errors="coerce")
    out["Frequency"] = pd.to_numeric(raw["count_trx"], errors="coerce")
    out["Monetary"] = parse_rupiah(raw["net_sales"]).round(2)

    # Engagement counters (default to 0 when a column is absent).
    def col(name: str) -> pd.Series:
        return pd.to_numeric(raw[name], errors="coerce").fillna(0) if name in raw else pd.Series(0, index=raw.index)

    out["SiteActivity"] = col("count_site_activity")
    out["EmailReceived"] = col("count_email_received")
    out["EmailOpened"] = col("count_email_opened")
    out["ContentClicked"] = col("count_content_clicked")
    out["ProductViewed"] = col("count_product_viewed")
    out["CouponReceived"] = col("count_coupon_received")
    # Clicks *within an opened email* (distinct from general on-site content
    # clicks above) — this is the true email CTR numerator.
    out["EmailClicked"] = col("count_email_opened_clicked")
    out["CampaignUnsubscribed"] = col("count_campaign_unsubscribed")
    out["SpamMarked"] = col("count_campaign_spam_marked")
    out["ChatDelivered"] = col("count_chat_delivered")

    # Derived engagement metrics.
    out["EmailOpenRate"] = (
        out["EmailOpened"] / out["EmailReceived"].replace(0, np.nan)
    ).fillna(0).clip(0, 1) * 100
    out["EmailClickRate"] = (
        out["EmailClicked"] / out["EmailOpened"].replace(0, np.nan)
    ).fillna(0).clip(0, 1) * 100
    out["EngagementScore"] = _engagement_score(out)

    out = out.dropna(subset=["Recency", "Frequency", "Monetary"])
    out = out[out["Monetary"] > 0].reset_index(drop=True)
    return out


def _engagement_score(df: pd.DataFrame) -> pd.Series:
    """0–100 composite of site + email + content engagement."""
    parts = ["SiteActivity", "EmailOpened", "ContentClicked", "ProductViewed"]
    score = np.zeros(len(df))
    for c in parts:
        score = score + _minmax(np.log1p(df[c]))
    return (score / len(parts) * 100).round(1)


# --------------------------------------------------------------------------- #
# 2. Synthetic fallback (used only when the real CSV is missing)
# --------------------------------------------------------------------------- #
_FIRST_NAMES = ["Aisha", "Budi", "Citra", "Dimas", "Eka", "Farah", "Gilang",
                "Hana", "Indra", "Joko", "Kirana", "Maya", "Naufal", "Putri"]
_LAST_NAMES = ["Santoso", "Wijaya", "Pratama", "Kusuma", "Hidayat", "Nugroho",
               "Utami", "Lestari", "Setiawan", "Maulana"]


def generate_synthetic_customers(n_customers: int = 3000, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """Fallback per-customer dataset mirroring the real schema."""
    rng = np.random.default_rng(seed)
    archetypes = [(20, 14, 1_800_000), (60, 8, 900_000), (120, 4, 450_000),
                  (300, 2, 250_000), (520, 1, 150_000)]
    weights = [0.16, 0.24, 0.28, 0.20, 0.12]

    rows = []
    for i in range(n_customers):
        rb, fl, sm = archetypes[rng.choice(len(archetypes), p=weights)]
        freq = max(1, int(rng.poisson(fl)))
        rec = min(365, max(1, int(rng.exponential(rb))))
        monetary = float(max(15_000, rng.normal(sm, sm / 3))) * freq
        received = int(rng.integers(0, 40))
        opened = int(rng.integers(0, received + 1))
        clicked = int(rng.integers(0, opened + 1))
        rows.append({
            "HashID": f"synthetic-{i:06d}",
            "CustomerID": f"CUST-{i + 1:05d}",
            "CustomerName": f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}",
            "Channel": "PlanetSports.Asia",
            "Recency": rec, "Frequency": freq, "Monetary": round(monetary, 2),
            "SiteActivity": int(rng.integers(0, 30)),
            "EmailReceived": received, "EmailOpened": opened, "EmailClicked": clicked,
            "ContentClicked": int(rng.integers(0, 10)),
            "ProductViewed": int(rng.integers(0, 25)),
            "CouponReceived": int(rng.integers(0, 3)),
            "CampaignUnsubscribed": int(rng.integers(0, 2)),
            "SpamMarked": int(rng.integers(0, 2)),
            "ChatDelivered": int(rng.integers(0, 3)),
        })
    df = pd.DataFrame(rows)
    df["EmailOpenRate"] = (df["EmailOpened"] / df["EmailReceived"].replace(0, np.nan)).fillna(0) * 100
    df["EmailClickRate"] = (df["EmailClicked"] / df["EmailOpened"].replace(0, np.nan)).fillna(0) * 100
    df["EngagementScore"] = _engagement_score(df)
    return df


# --------------------------------------------------------------------------- #
# 3. RFM scoring
# --------------------------------------------------------------------------- #
def score_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """Attach the classic 1–5 R/F/M scores to a customer table."""
    out = df.copy()
    out["R_Score"] = _score(out["Recency"], reverse=True)   # recent = high score
    out["F_Score"] = _score(out["Frequency"], reverse=False)
    out["M_Score"] = _score(out["Monetary"], reverse=False)
    out["RFM_Score"] = (
        out["R_Score"].astype(str) + out["F_Score"].astype(str) + out["M_Score"].astype(str)
    )
    out["RFM_Sum"] = out["R_Score"] + out["F_Score"] + out["M_Score"]
    return out


def _score(series: pd.Series, reverse: bool, bins: int = 5) -> pd.Series:
    """Quantile-based 1..5 score. `reverse=True` gives high score to low value."""
    try:
        ranks = pd.qcut(series.rank(method="first"), bins, labels=False) + 1
    except ValueError:
        ranks = pd.cut(series.rank(method="first"), bins, labels=False) + 1
    ranks = ranks.astype(int)
    if reverse:
        ranks = bins + 1 - ranks
    return ranks


# --------------------------------------------------------------------------- #
# 4. High Value Segment detection (mirrors the thesis notebook, §4.3.4)
# --------------------------------------------------------------------------- #
def detect_high_value(rfm: pd.DataFrame) -> pd.Series:
    """Outlier-based High Value Segment mask.

    Exactly mirrors the notebook: a customer is flagged as "High Value" when
    Monetary is an IQR outlier (> Q3 + 1.5·IQR) OR Frequency is above the
    99th percentile. These customers are separated out *before* clustering,
    so they never distort the K-Means result on the regular customer base.
    """
    q1, q3 = rfm["Monetary"].quantile([0.25, 0.75])
    iqr = q3 - q1
    upper_monetary = q3 + 1.5 * iqr
    outlier_monetary = rfm["Monetary"] > upper_monetary

    p99_freq = rfm["Frequency"].quantile(0.99)
    outlier_freq = rfm["Frequency"] > p99_freq

    return outlier_monetary | outlier_freq


def split_high_value(rfm: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (regular_customers, high_value_customers)."""
    mask = detect_high_value(rfm)
    return rfm[~mask].copy(), rfm[mask].copy()


# --------------------------------------------------------------------------- #
# 5. K-Means clustering (regular customers only — notebook §4.3.6–4.5)
# --------------------------------------------------------------------------- #
def scale_features(rfm: pd.DataFrame) -> tuple[np.ndarray, MinMaxScaler]:
    """Min-max scale the raw RFM features (matches the notebook exactly —
    no log transform). Always called on the *regular*, non-outlier subset."""
    x = rfm[RFM_FEATURES].astype(float)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(x)
    return scaled, scaler


def run_kmeans(rfm: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    """Fit K-Means (min-max scaled) on the given RFM table and attach segment
    labels. Callers should pass the *regular* (non-outlier) subset —
    see `build_segments()` for the full pipeline including the separately
    identified High Value Segment."""
    scaled, _ = scale_features(rfm)
    model = KMeans(n_clusters=n_clusters, init="k-means++", n_init=10,
                    max_iter=300, random_state=RANDOM_STATE)
    labels = model.fit_predict(scaled)
    out = rfm.copy()
    out["Cluster"] = labels
    return _name_segments(out)


def _name_segments(clustered: pd.DataFrame) -> pd.DataFrame:
    """Assign human-friendly segment names by ranking cluster RFM profiles.

    For the thesis-standard k = 3, this reproduces the notebook's manual
    mapping exactly: highest Frequency/Monetary → Champions, lowest Recency
    with mid F/M → Potential Loyalist, highest Recency with low F/M → At Risk.
    """
    profile = clustered.groupby("Cluster")[RFM_FEATURES].mean()
    profile["value"] = (
        -_minmax(profile["Recency"])
        + _minmax(profile["Frequency"])
        + _minmax(profile["Monetary"])
    )
    ordered = profile["value"].sort_values(ascending=False).index.tolist()

    name_pool = [
        ("Champions", "🏆"), ("Potential Loyalist", "🌱"), ("At Risk", "⚠️"),
        ("Promising", "🔆"), ("Hibernating", "😴"), ("Lost Customers", "🕸️"),
        ("New Customers", "✨"), ("Loyal Customers", "💙"),
    ]
    mapping, emoji_map = {}, {}
    for rank, cid in enumerate(ordered):
        label, emoji = name_pool[rank % len(name_pool)]
        mapping[cid] = label
        emoji_map[cid] = emoji

    out = clustered.copy()
    out["Segment"] = out["Cluster"].map(mapping)
    out["SegmentEmoji"] = out["Cluster"].map(emoji_map)
    return out


def _minmax(series: pd.Series) -> pd.Series:
    rng = series.max() - series.min()
    if rng == 0:
        return series * 0
    return (series - series.min()) / rng


def build_segments(rfm: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    """Full segmentation pipeline — mirrors the thesis notebook end-to-end:

    1. Separate the High Value Segment (Monetary IQR outliers OR Frequency
       > p99) from the regular customer base (§4.3.4).
    2. Min-max scale the regular customers' RFM features and fit K-Means
       (k = 3 by default) → Champions / Potential Loyalist / At Risk (§4.4–4.5).
    3. Recombine with the High Value Segment (Cluster = -1) so every
       customer — high value or not — has exactly one Segment label, and
       revenue/customer shares across all segments sum to 100% (§4.5.3).
    """
    regular, high_value = split_high_value(rfm)
    regular_clustered = run_kmeans(regular, n_clusters=n_clusters)

    hv = high_value.copy()
    hv["Cluster"] = -1
    hv["Segment"] = "High Value Segment"
    hv["SegmentEmoji"] = "💎"

    combined = pd.concat([regular_clustered, hv], ignore_index=True)
    return combined


# --------------------------------------------------------------------------- #
# 6. Cluster-selection analytics (notebook §4.4.1 — regular customers only)
# --------------------------------------------------------------------------- #
def elbow_scores(rfm: pd.DataFrame, k_range: range = range(2, 11)) -> pd.DataFrame:
    """Inertia (WCSS) for each k, computed on the regular (non-outlier)
    customer subset — matches the notebook's elbow curve."""
    regular, _ = split_high_value(rfm)
    scaled, _ = scale_features(regular)
    records = []
    for k in k_range:
        model = KMeans(n_clusters=k, init="k-means++", n_init=10,
                        max_iter=300, random_state=RANDOM_STATE)
        model.fit(scaled)
        records.append({"k": k, "inertia": model.inertia_})
    return pd.DataFrame(records)


def silhouette_scores(
    rfm: pd.DataFrame, k_range: range = range(2, 11), sample_size: int = 8000
) -> pd.DataFrame:
    """Silhouette score for each k, computed on the regular (non-outlier)
    customer subset — matches the notebook's methodology. A fixed-size
    sample is used only to keep the interactive dashboard responsive on the
    full ~28k-row regular base; the curve shape closely tracks the
    notebook's un-sampled result."""
    regular, _ = split_high_value(rfm)
    scaled, _ = scale_features(regular)
    n = scaled.shape[0]
    ss = min(sample_size, n) if n > sample_size else None
    records = []
    for k in k_range:
        model = KMeans(n_clusters=k, init="k-means++", n_init=10,
                        max_iter=300, random_state=RANDOM_STATE)
        labels = model.fit_predict(scaled)
        score = silhouette_score(scaled, labels, sample_size=ss, random_state=RANDOM_STATE)
        records.append({"k": k, "silhouette": score})
    return pd.DataFrame(records)


# --------------------------------------------------------------------------- #
# 7. PCA projection (supplementary — not in the notebook, added for the
#    dashboard's interactive cluster-separation view; uses the same min-max
#    scaling as the K-Means model for consistency).
# --------------------------------------------------------------------------- #
def pca_projection(clustered: pd.DataFrame) -> pd.DataFrame:
    """Project scaled RFM features to 2 principal components for plotting."""
    scaled, _ = scale_features(clustered)
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords = pca.fit_transform(scaled)
    out = clustered.copy()
    out["PC1"] = coords[:, 0]
    out["PC2"] = coords[:, 1]
    return out


# --------------------------------------------------------------------------- #
# 8. Segment summary table (notebook §4.5.2–4.5.3 — works for all segments,
#    including the High Value Segment, since it groups generically).
# --------------------------------------------------------------------------- #
def cluster_profile(clustered: pd.DataFrame, total_revenue: float | None = None) -> pd.DataFrame:
    """Summary table: mean RFM + customer count + revenue share per segment.

    `total_revenue` lets callers express Revenue_Share as a percentage of the
    *whole* customer base (matching the notebook's "Kontribusi Omzet %")
    even when `clustered` is a subset — e.g. on the K-Means Clustering page,
    where only the regular (non-High-Value) clusters are shown but revenue
    share should still read as a share of total company revenue. Defaults to
    the subset's own total (percentages sum to 100% within the subset)."""
    grp = clustered.groupby(["Cluster", "Segment", "SegmentEmoji"])
    profile = grp.agg(
        Customers=("CustomerID", "count"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Frequency", "mean"),
        Avg_Monetary=("Monetary", "mean"),
        Total_Revenue=("Monetary", "sum"),
    ).reset_index()
    denom = total_revenue if total_revenue is not None else profile["Total_Revenue"].sum()
    profile["Revenue_Share"] = (profile["Total_Revenue"] / denom * 100).round(1)
    profile["Customer_Share"] = (
        profile["Customers"] / profile["Customers"].sum() * 100
    ).round(1)
    for col in ["Avg_Recency", "Avg_Frequency", "Avg_Monetary", "Total_Revenue"]:
        profile[col] = profile[col].round(0)
    return profile.sort_values("Total_Revenue", ascending=False).reset_index(drop=True)


def sample_for_plot(df: pd.DataFrame, n: int = 4000, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """Down-sample large frames so browser-side charts stay responsive."""
    if len(df) <= n:
        return df
    return df.sample(n=n, random_state=seed)
