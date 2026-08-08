"""
utils/recommendation_engine.py
-------------------------------
Rule-Based Business Recommendation Engine for the Business Recommendations
page — turns each segment's real RFM + engagement averages into a structured
CRM decision-support package instead of static, hardcoded marketing copy.

Design principles
------------------
1. Nothing here is keyed on a segment NAME (no `if segment == "Champions"`).
   Every classification is computed by comparing a segment's mean metrics
   against a population baseline derived fresh from the live dataset, so the
   output adapts automatically if the underlying data changes.

2. The population baseline is the mean of each metric across *regular*
   (non-High-Value) customers. High Value is intentionally excluded from its
   own baseline — it was already pulled out of clustering for being an
   outlier group, so comparing it against the "normal" customer baseline is
   what actually shows how extreme it is, rather than diluting the baseline
   with its own outlier values.

3. Ratio-to-baseline classification (High / Medium / Low) is used instead of
   population quantiles. This dataset is extremely skewed (most customers
   have exactly one order), so raw quantile cut points collapse to
   degenerate values and stop discriminating between segments — a ratio to
   the regular-customer mean stays meaningful even under heavy skew.

4. `SpamMarked` and `ChatDelivered` exist in the raw schema but are 100%
   zero in this real data export (see preprocessing.py). Including them as
   rule inputs would be fake precision, so they are intentionally excluded
   from METRICS / the active rule set.

5. Multiple rules can and do fire simultaneously for one segment — the UI
   renders whichever combination the data actually produces, and the final
   "Recommended Marketing Strategy" list is the deduplicated union of every
   triggered rule's strategies, topped up with standing baseline CRM actions
   only if fewer than 5 unique strategies were actually triggered (clearly
   labeled as such — never disguised as a detected rule).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

# --------------------------------------------------------------------------- #
# Bilingual text helper — same {"en":.., "id":..} convention used everywhere
# else in this codebase (utils/i18n.py, utils/playbook.py).
# --------------------------------------------------------------------------- #
def L(pair: dict, lang: str) -> str:
    return pair.get(lang, pair.get("en", ""))


# --------------------------------------------------------------------------- #
# Metrics & classification
# --------------------------------------------------------------------------- #
METRICS = [
    "Recency", "Frequency", "Monetary", "SiteActivity", "ProductViewed",
    "EmailReceived", "EmailOpenRate", "EmailClickRate", "CouponReceived",
    "CampaignUnsubscribed",
]

HIGH_RATIO = 1.20   # segment mean >= 1.20x the regular-customer baseline
LOW_RATIO = 0.80    # segment mean <= 0.80x the regular-customer baseline


def population_baseline(clustered: pd.DataFrame) -> pd.Series:
    """Mean of every engine metric across *regular* customers only (Cluster
    >= 0) — the reference point every segment, including High Value, is
    compared against. Computed fresh from the live dataset every run."""
    regular = clustered[clustered["Cluster"] >= 0]
    return regular[METRICS].mean()


def segment_metric_means(clustered: pd.DataFrame) -> pd.DataFrame:
    """Per-segment mean of every engine metric, one row per Segment."""
    return (
        clustered.groupby(["Cluster", "Segment", "SegmentEmoji"])[METRICS]
        .mean()
        .reset_index()
    )


def classify(value: float, baseline: float) -> str:
    if baseline == 0:
        return "High" if value > 0 else "Medium"
    ratio = value / baseline
    if ratio >= HIGH_RATIO:
        return "High"
    if ratio <= LOW_RATIO:
        return "Low"
    return "Medium"


def segment_levels(row: pd.Series, baseline: pd.Series) -> dict[str, str]:
    """Classify one segment's mean metrics into Low/Medium/High labels
    relative to the regular-customer baseline."""
    return {m: classify(float(row[m]), float(baseline[m])) for m in METRICS}


# --------------------------------------------------------------------------- #
# Rule & Strategy data model
# --------------------------------------------------------------------------- #
@dataclass
class Strategy:
    id: str
    name: dict
    why: dict
    outcome: dict
    channel: str  # short label, e.g. "Email Marketing" — kept unlocalized


@dataclass
class Rule:
    id: str
    label: Callable[[dict], dict]           # levels -> {"en":.., "id":..}
    predicate: Callable[[dict], bool]
    problem: dict
    objective: dict
    why: Callable[[dict, dict | None], dict]  # (levels, context) -> explanation text
    strategies: list[Strategy]
    impact: list[dict]
    kpis: list[dict]
    weights: dict = field(default_factory=lambda: {
        "business_value": 0.4, "churn_risk": 0.3,
        "revenue_opportunity": 0.4, "engagement_opportunity": 0.4,
    })


def _static(pair: dict) -> Callable[[dict], dict]:
    return lambda _lv: pair


# --------------------------------------------------------------------------- #
# Rule catalogue
# --------------------------------------------------------------------------- #
RULES: list[Rule] = [
    Rule(
        id="reactivation",
        label=_static({"en": "High Recency + Low/Medium Frequency & Monetary",
                       "id": "Recency Tinggi + Frequency & Monetary Rendah/Sedang"}),
        predicate=lambda lv: lv["Recency"] == "High" and lv["Frequency"] != "High" and lv["Monetary"] != "High",
        problem={"en": "Inactive Customers / High Churn Risk", "id": "Pelanggan Tidak Aktif / Risiko Churn Tinggi"},
        objective={"en": "Reactivation", "id": "Reaktivasi"},
        why=lambda lv, ctx=None: {
            "en": f"Average days-since-last-purchase is well above the regular-customer baseline, while spend and order frequency are not elevated enough to offset the churn signal — a classic lapsing pattern.",
            "id": f"Rata-rata hari sejak pembelian terakhir jauh di atas baseline pelanggan reguler, sementara belanja dan frekuensi pembelian tidak cukup tinggi untuk mengimbangi sinyal churn ini — pola khas pelanggan yang mulai meninggalkan brand.",
        },
        strategies=[
            Strategy("winback", {"en": "Win-Back Campaign", "id": "Kampanye Win-Back"},
                     {"en": "Directly targets the recency gap with a reason to return now.", "id": "Langsung menyasar kesenjangan recency dengan alasan untuk kembali sekarang."},
                     {"en": "Recover a share of lapsing customers before they churn permanently.", "id": "Memulihkan sebagian pelanggan yang mulai churn sebelum benar-benar hilang."},
                     "Email Marketing"),
            Strategy("personalized_reco", {"en": "Personalized Product Recommendation", "id": "Rekomendasi Produk Personal"},
                     {"en": "Re-establishes relevance using their past purchase history.", "id": "Membangun kembali relevansi menggunakan riwayat pembelian mereka."},
                     {"en": "Higher click-through than generic reactivation blasts.", "id": "CTR lebih tinggi dibanding blast reaktivasi generik."},
                     "Website Personalization"),
            Strategy("dynamic_remarketing", {"en": "Dynamic Remarketing", "id": "Dynamic Remarketing"},
                     {"en": "Keeps the brand visible off-site while the customer is disengaged.", "id": "Menjaga brand tetap terlihat di luar situs saat pelanggan tidak aktif."},
                     {"en": "Increases return-visit rate ahead of a purchase decision.", "id": "Meningkatkan tingkat kunjungan ulang sebelum keputusan pembelian."},
                     "Dynamic Remarketing"),
            Strategy("limited_voucher", {"en": "Limited-Time Reactivation Voucher", "id": "Voucher Reaktivasi Terbatas Waktu"},
                     {"en": "A time constraint converts intent into an actual transaction.", "id": "Batas waktu mengubah niat menjadi transaksi nyata."},
                     {"en": "Short-term lift in reactivation rate.", "id": "Peningkatan jangka pendek pada tingkat reaktivasi."},
                     "Push Notification"),
        ],
        impact=[{"en": "Reduce Churn", "id": "Mengurangi Churn"}, {"en": "Increase Reactivation Rate", "id": "Meningkatkan Tingkat Reaktivasi"}],
        kpis=[{"en": "Reactivation Rate", "id": "Tingkat Reaktivasi"}, {"en": "Retention Rate", "id": "Tingkat Retensi"}],
        weights={"business_value": 0.5, "churn_risk": 0.9, "revenue_opportunity": 0.6, "engagement_opportunity": 0.3},
    ),
    Rule(
        id="basket_growth",
        label=_static({"en": "Recent Activity + Medium Frequency & Monetary",
                       "id": "Aktivitas Baru-baru Ini + Frequency & Monetary Sedang"}),
        predicate=lambda lv: lv["Recency"] != "High" and lv["Frequency"] == "Medium" and lv["Monetary"] in ("Low", "Medium"),
        problem={"en": "Low Basket Size / Upsell Opportunity", "id": "Nilai Keranjang Rendah / Peluang Upsell"},
        objective={"en": "Increase Average Order Value", "id": "Meningkatkan Rata-rata Nilai Pesanan"},
        why=lambda lv, ctx=None: {
            "en": "These customers are still buying at a reasonable cadence and are recently active, but their average spend hasn't scaled with their engagement — the relationship is healthy, the basket just isn't optimized yet.",
            "id": "Pelanggan ini masih membeli dengan ritme yang wajar dan aktif belakangan ini, namun rata-rata belanja mereka belum sebanding dengan keterlibatannya — hubungan sudah sehat, hanya keranjangnya belum optimal.",
        },
        strategies=[
            Strategy("cross_sell", {"en": "Cross-Selling", "id": "Cross-Selling"},
                     {"en": "Complementary items suit a customer who already trusts the brand.", "id": "Produk pelengkap cocok untuk pelanggan yang sudah percaya pada brand."},
                     {"en": "Higher items-per-order without discounting.", "id": "Jumlah item per pesanan lebih tinggi tanpa diskon."}, "Homepage Recommendation"),
            Strategy("upsell", {"en": "Upselling to Premium Tiers", "id": "Upselling ke Tingkat Premium"},
                     {"en": "Moderate spenders are the most persuadable toward a premium alternative.", "id": "Pembeli menengah paling mudah diarahkan ke alternatif premium."},
                     {"en": "Incremental AOV lift per transaction.", "id": "Kenaikan AOV per transaksi secara bertahap."}, "Website Personalization"),
            Strategy("bundle", {"en": "Bundle Recommendation", "id": "Rekomendasi Bundel"},
                     {"en": "Bundling raises perceived value while lifting basket size.", "id": "Bundling meningkatkan persepsi nilai sekaligus menaikkan nilai keranjang."},
                     {"en": "Higher conversion on multi-item carts.", "id": "Konversi lebih tinggi pada keranjang multi-item."}, "Website Personalization"),
            Strategy("fbt", {"en": "Frequently Bought Together", "id": "Sering Dibeli Bersama"},
                     {"en": "Social proof at checkout nudges an additional item into the cart.", "id": "Social proof saat checkout mendorong tambahan item ke keranjang."},
                     {"en": "Attach-rate improvement at checkout.", "id": "Peningkatan attach-rate saat checkout."}, "Website Personalization"),
        ],
        impact=[{"en": "Increase Basket Size", "id": "Meningkatkan Nilai Keranjang"}, {"en": "Increase Customer Lifetime Value", "id": "Meningkatkan CLV"}],
        kpis=[{"en": "Average Order Value", "id": "Rata-rata Nilai Pesanan"}, {"en": "Basket Size", "id": "Ukuran Keranjang"}],
        weights={"business_value": 0.5, "churn_risk": 0.2, "revenue_opportunity": 0.7, "engagement_opportunity": 0.4},
    ),
    Rule(
        id="retention_vip",
        label=_static({"en": "Recent Activity + High Frequency & Monetary",
                       "id": "Aktivitas Baru-baru Ini + Frequency & Monetary Tinggi"}),
        predicate=lambda lv: lv["Recency"] != "High" and lv["Frequency"] == "High" and lv["Monetary"] == "High",
        problem={"en": "High-Value Relationship to Protect", "id": "Hubungan Bernilai Tinggi yang Perlu Dijaga"},
        objective={"en": "Retention & Customer Lifetime Value", "id": "Retensi & Customer Lifetime Value"},
        why=lambda lv, ctx=None: {
            "en": (
                f"Both order frequency and spend are well above the regular-customer baseline while recency stays low — "
                f"this is the business's most valuable, most engaged behavior pattern"
                + (
                    f", concentrated enough that this segment alone drives {ctx['revenue_share']:.1f}% of total revenue "
                    f"from just {ctx['customer_share']:.1f}% of customers ({ctx['concentration']:.1f}x their proportional share)"
                    if ctx else ""
                )
                + ". Losing even a few of these customers has an outsized revenue impact."
            ),
            "id": (
                f"Frekuensi pembelian dan belanja sama-sama jauh di atas baseline pelanggan reguler, sementara recency tetap rendah — "
                f"ini adalah pola perilaku paling bernilai dan paling terlibat di bisnis ini"
                + (
                    f", terkonsentrasi hingga segmen ini sendiri menyumbang {ctx['revenue_share']:.1f}% dari total pendapatan "
                    f"hanya dari {ctx['customer_share']:.1f}% pelanggan ({ctx['concentration']:.1f}x porsi proporsionalnya)"
                    if ctx else ""
                )
                + ". Kehilangan meski hanya sedikit pelanggan di sini berdampak besar pada pendapatan."
            ),
        },
        strategies=[
            Strategy("vip_program", {"en": "VIP Program Enrollment", "id": "Pendaftaran Program VIP"},
                     {"en": "Formal recognition reinforces the relationship at its most valuable point.", "id": "Pengakuan formal memperkuat hubungan pada titik paling bernilai."},
                     {"en": "Improved multi-year retention.", "id": "Retensi multi-tahun yang lebih baik."}, "MAPCLUB Loyalty"),
            Strategy("early_access", {"en": "Early Access to New Collections", "id": "Akses Awal Koleksi Baru"},
                     {"en": "Rewards loyalty with something money can't buy: priority.", "id": "Menghargai loyalitas dengan sesuatu yang tak bisa dibeli: prioritas."},
                     {"en": "Reinforces exclusivity and reduces price sensitivity.", "id": "Memperkuat eksklusivitas dan mengurangi sensitivitas harga."}, "Email Marketing"),
            Strategy("double_points", {"en": "Double Loyalty Points Events", "id": "Event Poin Loyalitas Ganda"},
                     {"en": "Directly rewards the behavior (frequency + spend) driving their value.", "id": "Secara langsung menghargai perilaku (frekuensi + belanja) yang mendorong nilainya."},
                     {"en": "Sustains purchase cadence.", "id": "Menjaga ritme pembelian tetap terjaga."}, "MAPCLUB Loyalty"),
            Strategy("birthday_reward", {"en": "Birthday / Anniversary Reward", "id": "Reward Ulang Tahun / Anniversary"},
                     {"en": "A personal touch that's disproportionately memorable for high-engagement customers.", "id": "Sentuhan personal yang sangat berkesan bagi pelanggan dengan keterlibatan tinggi."},
                     {"en": "Strengthens emotional brand loyalty.", "id": "Memperkuat loyalitas emosional terhadap brand."}, "WhatsApp"),
        ],
        impact=[{"en": "Improve Customer Retention", "id": "Meningkatkan Retensi Pelanggan"}, {"en": "Increase Customer Lifetime Value", "id": "Meningkatkan CLV"}],
        kpis=[{"en": "Customer Lifetime Value", "id": "Customer Lifetime Value"}, {"en": "Retention Rate", "id": "Tingkat Retensi"}],
        weights={"business_value": 0.95, "churn_risk": 0.3, "revenue_opportunity": 0.8, "engagement_opportunity": 0.5},
    ),
    Rule(
        id="browsing_no_purchase",
        label=lambda lv: {
            "en": f"High {'Product Views' if lv['ProductViewed']=='High' else 'Site Activity'} + Non-High Frequency",
            "id": f"{'Produk Dilihat' if lv['ProductViewed']=='High' else 'Aktivitas Situs'} Tinggi + Frequency Non-Tinggi",
        },
        predicate=lambda lv: (lv["ProductViewed"] == "High" or lv["SiteActivity"] == "High") and lv["Frequency"] != "High",
        problem={"en": "Browsing Without Converting / Low Conversion", "id": "Sering Melihat Tanpa Membeli / Konversi Rendah"},
        objective={"en": "Increase Conversion", "id": "Meningkatkan Konversi"},
        why=lambda lv, ctx=None: {
            "en": "On-site browsing signals (product views and/or site activity) are elevated relative to the baseline, but that interest isn't translating into a proportionally high purchase frequency — the demand exists, the conversion path is the gap.",
            "id": "Sinyal browsing di situs (produk dilihat dan/atau aktivitas situs) berada di atas baseline, tetapi minat tersebut belum berubah menjadi frekuensi pembelian yang sepadan — permintaan sudah ada, yang kurang adalah jalur konversinya.",
        },
        strategies=[
            Strategy("remarketing", {"en": "Dynamic Remarketing", "id": "Dynamic Remarketing"},
                     {"en": "Follows up on specific viewed products with a direct nudge.", "id": "Menindaklanjuti produk yang dilihat dengan dorongan langsung."},
                     {"en": "Recovers a share of browse-only sessions into purchases.", "id": "Memulihkan sebagian sesi browsing menjadi pembelian."}, "Dynamic Remarketing"),
            Strategy("price_drop", {"en": "Price-Drop Notification", "id": "Notifikasi Penurunan Harga"},
                     {"en": "Price is a common hesitation point for high-viewed, low-bought items.", "id": "Harga sering jadi titik keraguan pada item yang banyak dilihat tapi jarang dibeli."},
                     {"en": "Converts price-sensitive browsers at the right moment.", "id": "Mengonversi browser yang sensitif harga di momen yang tepat."}, "Push Notification"),
            Strategy("back_in_stock", {"en": "Back-in-Stock Alert", "id": "Notifikasi Stok Tersedia Kembali"},
                     {"en": "Captures demand that was previously blocked by availability.", "id": "Menangkap permintaan yang sebelumnya terhambat ketersediaan stok."},
                     {"en": "Directly recovers otherwise-lost demand.", "id": "Memulihkan langsung permintaan yang sebelumnya hilang."}, "Push Notification"),
            Strategy("cart_recovery", {"en": "Cart Recovery Sequence", "id": "Rangkaian Pemulihan Keranjang"},
                     {"en": "Targets the highest-intent drop-off point in the funnel.", "id": "Menyasar titik drop-off dengan intensi tertinggi di funnel."},
                     {"en": "One of the highest-ROI automated CRM flows.", "id": "Salah satu alur CRM otomatis dengan ROI tertinggi."}, "Email Marketing"),
        ],
        impact=[{"en": "Improve Conversion", "id": "Meningkatkan Konversi"}, {"en": "Reduce Marketing Cost per Acquisition", "id": "Mengurangi Biaya Marketing per Akuisisi"}],
        kpis=[{"en": "Conversion Rate", "id": "Tingkat Konversi"}, {"en": "Cart Recovery Rate", "id": "Tingkat Pemulihan Keranjang"}],
        weights={"business_value": 0.4, "churn_risk": 0.3, "revenue_opportunity": 0.75, "engagement_opportunity": 0.6},
    ),
    Rule(
        id="low_email_engagement",
        label=_static({"en": "High Email Volume + Non-High Open Rate", "id": "Volume Email Tinggi + Open Rate Non-Tinggi"}),
        predicate=lambda lv: lv["EmailReceived"] == "High" and lv["EmailOpenRate"] != "High",
        problem={"en": "Poor Email Engagement", "id": "Keterlibatan Email Rendah"},
        objective={"en": "Improve Email Engagement", "id": "Meningkatkan Keterlibatan Email"},
        why=lambda lv, ctx=None: {
            "en": "This segment receives an above-baseline volume of email, yet open rates haven't kept pace — either fatigue from volume or a mismatch in relevance/timing is suppressing engagement.",
            "id": "Segmen ini menerima volume email di atas baseline, namun open rate tidak ikut naik — kemungkinan kelelahan akibat volume atau ketidaksesuaian relevansi/waktu pengiriman menekan keterlibatan.",
        },
        strategies=[
            Strategy("ab_subject", {"en": "A/B Subject Line Testing", "id": "A/B Testing Subject Line"},
                     {"en": "Open rate is a subject-line problem before it's a content problem.", "id": "Open rate adalah masalah subject line sebelum menjadi masalah konten."},
                     {"en": "Measurable lift in open rate within weeks.", "id": "Peningkatan open rate yang terukur dalam hitungan minggu."}, "Email Marketing"),
            Strategy("send_time", {"en": "Send-Time Optimization", "id": "Optimasi Waktu Pengiriman"},
                     {"en": "Volume is already high — timing, not frequency, is the likely lever.", "id": "Volume sudah tinggi — waktu, bukan frekuensi, kemungkinan menjadi tuas yang tepat."},
                     {"en": "Higher open rate without sending more email.", "id": "Open rate lebih tinggi tanpa menambah jumlah email."}, "Email Marketing"),
            Strategy("frequency_opt", {"en": "Campaign Frequency Optimization", "id": "Optimasi Frekuensi Kampanye"},
                     {"en": "Reduces the risk that high volume itself is causing disengagement.", "id": "Mengurangi risiko bahwa volume tinggi itu sendiri menyebabkan disengagement."},
                     {"en": "Improved engagement per email sent.", "id": "Keterlibatan per email terkirim yang lebih baik."}, "Email Marketing"),
        ],
        impact=[{"en": "Improve Email Open Rate", "id": "Meningkatkan Open Rate Email"}, {"en": "Reduce Marketing Cost", "id": "Mengurangi Biaya Marketing"}],
        kpis=[{"en": "Email Open Rate", "id": "Email Open Rate"}, {"en": "CTR", "id": "CTR"}],
        weights={"business_value": 0.3, "churn_risk": 0.35, "revenue_opportunity": 0.3, "engagement_opportunity": 0.8},
    ),
    Rule(
        id="checkout_friction",
        label=_static({"en": "High Email Open + High Click, Non-High Frequency", "id": "Open & Klik Email Tinggi, Frequency Non-Tinggi"}),
        predicate=lambda lv: lv["EmailOpenRate"] == "High" and lv["EmailClickRate"] == "High" and lv["Frequency"] != "High",
        problem={"en": "Checkout Friction / Conversion Leakage", "id": "Hambatan Checkout / Kebocoran Konversi"},
        objective={"en": "Increase Conversion", "id": "Meningkatkan Konversi"},
        why=lambda lv, ctx=None: {
            "en": "These customers open and click email at an above-baseline rate — interest clearly exists — but that doesn't show up as a correspondingly high purchase frequency, pointing to friction later in the funnel rather than a demand problem.",
            "id": "Pelanggan ini membuka dan mengklik email di atas baseline — minat jelas ada — namun tidak diikuti frekuensi pembelian yang sepadan, mengindikasikan hambatan di tahap selanjutnya dari funnel, bukan masalah permintaan.",
        },
        strategies=[
            Strategy("landing_opt", {"en": "Landing Page Optimization", "id": "Optimasi Landing Page"},
                     {"en": "High click-through with low purchase often traces to the landing experience.", "id": "CTR tinggi dengan pembelian rendah sering berakar pada pengalaman landing page."},
                     {"en": "Higher click-to-purchase conversion.", "id": "Konversi klik-ke-pembelian yang lebih tinggi."}, "Website Personalization"),
            Strategy("reviews", {"en": "Product Reviews & Social Proof", "id": "Ulasan Produk & Social Proof"},
                     {"en": "Addresses trust as a likely blocker for engaged-but-unconverted traffic.", "id": "Mengatasi kepercayaan sebagai kemungkinan penghambat trafik yang terlibat namun belum konversi."},
                     {"en": "Improved conversion at the product page.", "id": "Konversi yang lebih baik di halaman produk."}, "Website Personalization"),
            Strategy("faster_checkout", {"en": "Faster / Simplified Checkout", "id": "Checkout Lebih Cepat / Sederhana"},
                     {"en": "Removes friction at the final, most fragile step of the funnel.", "id": "Menghilangkan hambatan di tahap akhir funnel yang paling rentan."},
                     {"en": "Reduced checkout abandonment.", "id": "Mengurangi abandonment saat checkout."}, "Website Personalization"),
        ],
        impact=[{"en": "Improve Conversion", "id": "Meningkatkan Konversi"}, {"en": "Reduce Checkout Abandonment", "id": "Mengurangi Abandonment Checkout"}],
        kpis=[{"en": "Checkout Completion Rate", "id": "Tingkat Penyelesaian Checkout"}, {"en": "Conversion Rate", "id": "Tingkat Konversi"}],
        weights={"business_value": 0.4, "churn_risk": 0.3, "revenue_opportunity": 0.7, "engagement_opportunity": 0.5},
    ),
    Rule(
        id="coupon_ineffective",
        label=_static({"en": "High Coupon Volume + Non-High Frequency", "id": "Volume Kupon Tinggi + Frequency Non-Tinggi"}),
        predicate=lambda lv: lv["CouponReceived"] == "High" and lv["Frequency"] != "High",
        problem={"en": "Coupon Fatigue / Ineffective Couponing", "id": "Kelelahan Kupon / Kupon Tidak Efektif"},
        objective={"en": "Improve Marketing Efficiency", "id": "Meningkatkan Efisiensi Marketing"},
        why=lambda lv, ctx=None: {
            "en": "This segment already receives an above-baseline number of coupons, yet purchase frequency hasn't risen with it — broad couponing has diminishing returns here and is a marketing-cost inefficiency worth addressing.",
            "id": "Segmen ini sudah menerima jumlah kupon di atas baseline, namun frekuensi pembelian tidak ikut naik — kupon massal memiliki hasil yang semakin menurun di sini dan merupakan inefisiensi biaya marketing yang perlu diperbaiki.",
        },
        strategies=[
            Strategy("personalized_coupon", {"en": "Personalized (not Blanket) Coupons", "id": "Kupon Personal (Bukan Massal)"},
                     {"en": "Targeting replaces volume as the lever, since volume alone isn't working.", "id": "Penargetan menggantikan volume sebagai tuas, karena volume saja tidak berhasil."},
                     {"en": "Higher redemption rate per coupon issued.", "id": "Tingkat penukaran per kupon yang lebih tinggi."}, "Email Marketing"),
            Strategy("category_coupon", {"en": "Category-Specific Coupons", "id": "Kupon Spesifik Kategori"},
                     {"en": "Aligns the offer with demonstrated category interest instead of a generic discount.", "id": "Menyesuaikan penawaran dengan minat kategori yang terbukti, bukan diskon generik."},
                     {"en": "Better redemption-to-cost ratio.", "id": "Rasio penukaran terhadap biaya yang lebih baik."}, "Email Marketing"),
            Strategy("flash_coupon", {"en": "Flash / Time-Boxed Coupons", "id": "Kupon Flash / Berbatas Waktu"},
                     {"en": "Urgency can convert a segment that hasn't responded to standing offers.", "id": "Urgensi dapat mengonversi segmen yang belum merespons penawaran tetap."},
                     {"en": "Short-term redemption spike.", "id": "Lonjakan penukaran jangka pendek."}, "Push Notification"),
        ],
        impact=[{"en": "Reduce Marketing Cost", "id": "Mengurangi Biaya Marketing"}, {"en": "Improve Coupon Redemption Rate", "id": "Meningkatkan Tingkat Penukaran Kupon"}],
        kpis=[{"en": "Coupon Redemption Rate", "id": "Tingkat Penukaran Kupon"}, {"en": "Marketing ROI", "id": "ROI Marketing"}],
        weights={"business_value": 0.3, "churn_risk": 0.25, "revenue_opportunity": 0.4, "engagement_opportunity": 0.6},
    ),
    Rule(
        id="communication_fatigue",
        label=_static({"en": "High Campaign Unsubscribe Rate", "id": "Tingkat Unsubscribe Kampanye Tinggi"}),
        predicate=lambda lv: lv["CampaignUnsubscribed"] == "High",
        problem={"en": "Communication Fatigue / Deliverability Risk", "id": "Kelelahan Komunikasi / Risiko Deliverability"},
        objective={"en": "Improve Marketing Efficiency", "id": "Meningkatkan Efisiensi Marketing"},
        why=lambda lv, ctx=None: {
            "en": "Unsubscribe activity in this segment is above the regular-customer baseline — continuing an untargeted cadence here risks losing the channel entirely, not just this campaign's response rate.",
            "id": "Aktivitas unsubscribe di segmen ini berada di atas baseline pelanggan reguler — melanjutkan ritme komunikasi yang tidak tertarget berisiko kehilangan seluruh kanal ini, bukan hanya response rate kampanye tertentu.",
        },
        strategies=[
            Strategy("pref_center", {"en": "Preference Center", "id": "Preference Center"},
                     {"en": "Lets customers self-select frequency instead of unsubscribing entirely.", "id": "Memungkinkan pelanggan memilih sendiri frekuensi, alih-alih unsubscribe total."},
                     {"en": "Reduced full unsubscribes, retained partial reach.", "id": "Mengurangi unsubscribe total, tetap mempertahankan sebagian jangkauan."}, "Email Marketing"),
            Strategy("freq_control", {"en": "Frequency Capping", "id": "Pembatasan Frekuensi"},
                     {"en": "Directly addresses volume as a likely driver of the unsubscribe signal.", "id": "Secara langsung mengatasi volume sebagai kemungkinan pemicu sinyal unsubscribe."},
                     {"en": "Lower unsubscribe rate over time.", "id": "Tingkat unsubscribe yang menurun seiring waktu."}, "Email Marketing"),
            Strategy("personalized_cadence", {"en": "Personalized Communication Cadence", "id": "Ritme Komunikasi Personal"},
                     {"en": "Matches contact frequency to actual engagement level rather than a blanket schedule.", "id": "Menyesuaikan frekuensi kontak dengan tingkat keterlibatan aktual, bukan jadwal seragam."},
                     {"en": "Healthier long-term list quality.", "id": "Kualitas daftar kontak jangka panjang yang lebih sehat."}, "Email Marketing"),
        ],
        impact=[{"en": "Reduce Churn", "id": "Mengurangi Churn"}, {"en": "Protect Deliverability", "id": "Menjaga Deliverability"}],
        kpis=[{"en": "Unsubscribe Rate", "id": "Tingkat Unsubscribe"}, {"en": "Email Open Rate", "id": "Email Open Rate"}],
        weights={"business_value": 0.35, "churn_risk": 0.6, "revenue_opportunity": 0.2, "engagement_opportunity": 0.7},
    ),
    Rule(
        id="dormant",
        label=_static({"en": "High Recency + Low Site & Email Activity", "id": "Recency Tinggi + Aktivitas Situs & Email Rendah"}),
        predicate=lambda lv: (
            lv["Recency"] == "High" and lv["SiteActivity"] != "High"
            and lv["EmailOpenRate"] != "High" and lv["Frequency"] != "High"
        ),
        problem={"en": "Dormant Customer", "id": "Pelanggan Dorman"},
        objective={"en": "Low-Cost Reactivation", "id": "Reaktivasi Berbiaya Rendah"},
        why=lambda lv, ctx=None: {
            "en": "Recency is high while site activity, email engagement and purchase frequency are all at or below baseline — this is a fully disengaged customer where active CRM spend is unlikely to pay back.",
            "id": "Recency tinggi sementara aktivitas situs, keterlibatan email, dan frekuensi pembelian semuanya di bawah atau setara baseline — ini pelanggan yang sepenuhnya tidak aktif, di mana pengeluaran CRM aktif kemungkinan tidak akan kembali modal.",
        },
        strategies=[
            Strategy("seasonal_only", {"en": "Seasonal Campaigns Only", "id": "Hanya Kampanye Musiman"},
                     {"en": "Matches CRM spend to the low expected response rate of this group.", "id": "Menyesuaikan pengeluaran CRM dengan response rate rendah yang diharapkan dari grup ini."},
                     {"en": "Lower cost-per-contact with no material loss in response.", "id": "Biaya per kontak lebih rendah tanpa kehilangan respons yang berarti."}, "Email Marketing"),
            Strategy("low_priority_crm", {"en": "Low-Priority CRM Treatment", "id": "Perlakuan CRM Prioritas Rendah"},
                     {"en": "Frees up CRM budget to be redirected toward higher-response segments.", "id": "Membebaskan anggaran CRM untuk dialihkan ke segmen dengan respons lebih tinggi."},
                     {"en": "Improved overall marketing ROI.", "id": "ROI marketing keseluruhan yang lebih baik."}, "Email Marketing"),
            Strategy("annual_reactivation", {"en": "Annual Reactivation Push", "id": "Dorongan Reaktivasi Tahunan"},
                     {"en": "A single well-timed push captures the few who are still reachable.", "id": "Satu dorongan yang tepat waktu menjangkau sebagian kecil yang masih bisa diraih."},
                     {"en": "Occasional reactivation at minimal ongoing cost.", "id": "Reaktivasi sesekali dengan biaya berkelanjutan yang minimal."}, "Email Marketing"),
        ],
        impact=[{"en": "Reduce Marketing Cost", "id": "Mengurangi Biaya Marketing"}, {"en": "Improve Marketing ROI", "id": "Meningkatkan ROI Marketing"}],
        kpis=[{"en": "Marketing ROI", "id": "ROI Marketing"}, {"en": "Reactivation Rate", "id": "Tingkat Reaktivasi"}],
        weights={"business_value": 0.25, "churn_risk": 0.7, "revenue_opportunity": 0.3, "engagement_opportunity": 0.3},
    ),
    Rule(
        id="premium_buyer",
        label=_static({"en": "High Monetary + Non-High Frequency", "id": "Monetary Tinggi + Frequency Non-Tinggi"}),
        predicate=lambda lv: lv["Monetary"] == "High" and lv["Frequency"] != "High",
        problem={"en": "Premium / Occasional Big-Ticket Buyer", "id": "Pembeli Premium / Sesekali Bernilai Besar"},
        objective={"en": "Increase Repeat Purchase & CLV", "id": "Meningkatkan Repeat Purchase & CLV"},
        why=lambda lv, ctx=None: {
            "en": "Average spend is well above baseline despite a purchase frequency that isn't — this customer buys big, infrequently, likely around specific need-based moments rather than habitually.",
            "id": "Rata-rata belanja jauh di atas baseline meski frekuensi pembeliannya tidak — pelanggan ini membeli dalam jumlah besar namun jarang, kemungkinan pada momen kebutuhan tertentu, bukan secara rutin.",
        },
        strategies=[
            Strategy("premium_accessories", {"en": "Premium Accessory Cross-Sell", "id": "Cross-Sell Aksesori Premium"},
                     {"en": "Matches their demonstrated willingness to spend on quality.", "id": "Sesuai dengan kesediaan mereka untuk mengeluarkan biaya lebih untuk kualitas."},
                     {"en": "Incremental revenue per big-ticket purchase.", "id": "Pendapatan tambahan per pembelian bernilai besar."}, "Email Marketing"),
            Strategy("product_care", {"en": "Product Care / Maintenance Content", "id": "Konten Perawatan Produk"},
                     {"en": "Extends the relationship between infrequent purchase occasions.", "id": "Memperpanjang hubungan di antara momen pembelian yang jarang."},
                     {"en": "Keeps the brand top-of-mind until the next need arises.", "id": "Menjaga brand tetap diingat hingga kebutuhan berikutnya muncul."}, "Email Marketing"),
            Strategy("personal_followup", {"en": "Personalized Post-Purchase Follow-Up", "id": "Follow-Up Personal Pasca-Pembelian"},
                     {"en": "A high-value, low-frequency buyer merits a higher-touch relationship.", "id": "Pembeli bernilai tinggi namun jarang layak mendapat hubungan yang lebih personal."},
                     {"en": "Improved likelihood of a repeat big-ticket purchase.", "id": "Peluang lebih besar untuk pembelian besar berulang."}, "WhatsApp"),
        ],
        impact=[{"en": "Increase Repeat Purchase", "id": "Meningkatkan Repeat Purchase"}, {"en": "Increase Customer Lifetime Value", "id": "Meningkatkan CLV"}],
        kpis=[{"en": "Repeat Purchase Rate", "id": "Tingkat Pembelian Berulang"}, {"en": "Customer Lifetime Value", "id": "Customer Lifetime Value"}],
        weights={"business_value": 0.7, "churn_risk": 0.3, "revenue_opportunity": 0.65, "engagement_opportunity": 0.4},
    ),
    Rule(
        id="frequent_low_spender",
        label=_static({"en": "High Frequency + Non-High Monetary", "id": "Frequency Tinggi + Monetary Non-Tinggi"}),
        predicate=lambda lv: lv["Frequency"] == "High" and lv["Monetary"] != "High",
        problem={"en": "Frequent but Low-Value Purchases", "id": "Sering Membeli namun Nilai Rendah"},
        objective={"en": "Increase Average Order Value", "id": "Meningkatkan Rata-rata Nilai Pesanan"},
        why=lambda lv, ctx=None: {
            "en": "Purchase frequency is above baseline but average spend hasn't followed — a loyal shopping habit exists, but each visit is under-monetized relative to the engagement it represents.",
            "id": "Frekuensi pembelian di atas baseline namun rata-rata belanja tidak mengikuti — kebiasaan belanja yang loyal sudah ada, tetapi setiap kunjungan belum termonetisasi secara maksimal dibanding tingkat keterlibatannya.",
        },
        strategies=[
            Strategy("bundle_promo", {"en": "Bundle Promotion", "id": "Promosi Bundel"},
                     {"en": "Raises order value for a customer who is already visiting often.", "id": "Menaikkan nilai pesanan untuk pelanggan yang sudah sering berkunjung."},
                     {"en": "Higher revenue per visit without needing more visits.", "id": "Pendapatan per kunjungan lebih tinggi tanpa perlu menambah kunjungan."}, "Website Personalization"),
            Strategy("premium_upgrade", {"en": "Premium Product Upgrade Offer", "id": "Penawaran Upgrade Produk Premium"},
                     {"en": "Frequent shoppers are well-positioned to trade up given the right nudge.", "id": "Pembeli yang sering berbelanja berpotensi besar untuk naik kelas dengan dorongan yang tepat."},
                     {"en": "Higher average selling price per transaction.", "id": "Harga jual rata-rata per transaksi yang lebih tinggi."}, "Homepage Recommendation"),
            Strategy("free_shipping_threshold", {"en": "Free-Shipping Order Threshold", "id": "Ambang Gratis Ongkir"},
                     {"en": "A well-known, low-cost lever to nudge basket size upward at checkout.", "id": "Cara yang dikenal luas dan berbiaya rendah untuk menaikkan nilai keranjang saat checkout."},
                     {"en": "Immediate, measurable AOV lift.", "id": "Kenaikan AOV yang langsung terukur."}, "Website Personalization"),
        ],
        impact=[{"en": "Increase Average Order Value", "id": "Meningkatkan Rata-rata Nilai Pesanan"}, {"en": "Increase Customer Lifetime Value", "id": "Meningkatkan CLV"}],
        kpis=[{"en": "Average Order Value", "id": "Rata-rata Nilai Pesanan"}, {"en": "Basket Size", "id": "Ukuran Keranjang"}],
        weights={"business_value": 0.45, "churn_risk": 0.2, "revenue_opportunity": 0.6, "engagement_opportunity": 0.35},
    ),
]

# No baseline filler actions — only strategies from triggered rules are shown.
BASELINE_ACTIONS: list[Strategy] = []


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def evaluate(levels: dict[str, str]) -> list[Rule]:
    """Return every rule whose predicate is satisfied by these levels."""
    return [r for r in RULES if r.predicate(levels)]


def priority_score(triggered: list[Rule], revenue_share: float, customer_share: float) -> dict:
    """Smart Priority Engine: blends each triggered rule's own weights with
    how disproportionate this segment's revenue is relative to its size.
    Returns {"score": float 0-1, "stars": int 1-5, "label": {"en":..,"id":..}}.
    """
    if not triggered:
        max_w = {"business_value": 0.3, "churn_risk": 0.15, "revenue_opportunity": 0.3, "engagement_opportunity": 0.3}
    else:
        max_w = {
            k: max(r.weights[k] for r in triggered)
            for k in ("business_value", "churn_risk", "revenue_opportunity", "engagement_opportunity")
        }

    concentration = (revenue_share / customer_share) if customer_share > 0 else 1.0
    concentration_component = min(1.0, concentration / 3.0)
    blended_business_value = 0.5 * max_w["business_value"] + 0.5 * concentration_component

    overall = (
        0.40 * blended_business_value
        + 0.25 * max_w["churn_risk"]
        + 0.20 * max_w["revenue_opportunity"]
        + 0.15 * max_w["engagement_opportunity"]
    )
    overall = max(0.0, min(1.0, overall))

    if overall >= 0.68:
        stars, label = 5, {"en": "Critical", "id": "Kritis"}
    elif overall >= 0.55:
        stars, label = 4, {"en": "High", "id": "Tinggi"}
    elif overall >= 0.40:
        stars, label = 3, {"en": "Medium", "id": "Sedang"}
    elif overall >= 0.25:
        stars, label = 2, {"en": "Low", "id": "Rendah"}
    else:
        stars, label = 1, {"en": "Monitor", "id": "Pantau"}

    return {"score": round(overall, 3), "stars": stars, "label": label}


def rule_score(rule: Rule) -> float:
    """A single rule's own priority weight (used to tier its strategies)."""
    w = rule.weights
    return 0.35 * w["business_value"] + 0.30 * w["churn_risk"] + 0.20 * w["revenue_opportunity"] + 0.15 * w["engagement_opportunity"]


def build_action_plan(triggered: list[Rule], target_min: int = 5, target_max: int = 8) -> list[dict]:
    """Deduplicated, prioritized marketing action plan from triggered rules only.
    No baseline filler actions are added."""
    seen: set[str] = set()
    actions: list[dict] = []

    ranked_rules = sorted(triggered, key=rule_score, reverse=True)
    for rule in ranked_rules:
        score = rule_score(rule)
        tier = 1 if score >= 0.65 else 2 if score >= 0.5 else 3 if score >= 0.35 else 4
        for strat in rule.strategies:
            if strat.id in seen:
                continue
            seen.add(strat.id)
            actions.append({
                "strategy": strat, "tier": tier, "source_rule": rule.id,
                "source_objective": rule.objective,
            })

    actions.sort(key=lambda a: a["tier"])
    return actions[:target_max]


def build_roadmap(actions: list[dict]) -> dict[str, list[dict]]:
    """Bucket the action plan into an implementation roadmap."""
    return {
        "immediate": [a for a in actions if a["tier"] in (1, 2)],
        "medium": [a for a in actions if a["tier"] == 3],
        "long": [a for a in actions if a["tier"] == 4],
    }


def build_kpis(triggered: list[Rule], cap: int = 6) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for rule in sorted(triggered, key=rule_score, reverse=True):
        for kpi in rule.kpis:
            key = kpi["en"]
            if key in seen:
                continue
            seen.add(key)
            out.append(kpi)
    return out[:cap]


def customer_summary(row: pd.Series, levels: dict[str, str], lang: str) -> str:
    """Natural-language paragraph describing this segment's behavior,
    built entirely from real computed numbers — never a static template."""
    r, f, m = row["Avg_Recency"], row["Avg_Frequency"], row["Avg_Monetary"]
    from components.metrics import format_rupiah

    recency_desc = {
        "en": {"High": "have not purchased in a long time", "Medium": "purchase at a typical pace", "Low": "have purchased very recently"},
        "id": {"High": "sudah lama tidak bertransaksi", "Medium": "bertransaksi dengan ritme yang umum", "Low": "baru saja bertransaksi"},
    }[lang][levels["Recency"]]
    freq_desc = {
        "en": {"High": "buy noticeably more often than most customers", "Medium": "buy at a moderate, average frequency", "Low": "buy infrequently"},
        "id": {"High": "membeli jauh lebih sering dari kebanyakan pelanggan", "Medium": "membeli dengan frekuensi sedang, sesuai rata-rata", "Low": "jarang membeli"},
    }[lang][levels["Frequency"]]
    money_desc = {
        "en": {"High": "spend well above the typical customer", "Medium": "spend a moderate, average amount", "Low": "spend relatively little per order"},
        "id": {"High": "berbelanja jauh di atas pelanggan pada umumnya", "Medium": "berbelanja dalam jumlah sedang, sesuai rata-rata", "Low": "berbelanja relatif sedikit per pesanan"},
    }[lang][levels["Monetary"]]

    if lang == "id":
        return (
            f"Rata-rata pelanggan di segmen ini {recency_desc}, {freq_desc}, dan {money_desc}. "
            f"Secara konkret: recency rata-rata {r:.0f} hari, frequency rata-rata {f:.1f} transaksi, "
            f"dan monetary rata-rata {format_rupiah(m)} per pelanggan."
        )
    return (
        f"On average, customers in this segment {recency_desc}, {freq_desc}, and {money_desc}. "
        f"Concretely: average recency is {r:.0f} days, average frequency is {f:.1f} orders, "
        f"and average monetary value is {format_rupiah(m)} per customer."
    )


def strategic_insights(profile: pd.DataFrame, engine_results: dict[str, dict], lang: str) -> list[str]:
    """3-5 executive insights generated from the actual computed segment
    data (revenue shares, dominant rules, etc.) — not static copy."""
    from components.metrics import format_rupiah

    insights: list[str] = []
    total_customers = int(profile["Customers"].sum())

    hv_row = profile[profile["Segment"] == "High Value Segment"]
    if not hv_row.empty:
        hv = hv_row.iloc[0]
        if lang == "id":
            insights.append(
                f"Segmen Bernilai Tinggi menyumbang {hv['Revenue_Share']:.1f}% dari total pendapatan "
                f"hanya dari {hv['Customer_Share']:.1f}% basis pelanggan ({int(hv['Customers']):,} orang) — "
                f"perlakuan CRM premium untuk segmen ini bukan pilihan, melainkan keharusan bisnis."
            )
        else:
            insights.append(
                f"The High Value Segment drives {hv['Revenue_Share']:.1f}% of total revenue from just "
                f"{hv['Customer_Share']:.1f}% of the customer base ({int(hv['Customers']):,} people) — "
                f"premium CRM treatment for this segment is a business necessity, not a nice-to-have."
            )

    at_risk_row = profile[profile["Segment"] == "At Risk"]
    if not at_risk_row.empty:
        ar = at_risk_row.iloc[0]
        if ar["Customer_Share"] >= 30:
            if lang == "id":
                insights.append(
                    f"Segmen At Risk adalah {ar['Customer_Share']:.1f}% dari seluruh basis pelanggan "
                    f"({int(ar['Customers']):,} orang) — pada skala ini, retensi harus menjadi prioritas "
                    f"marketing yang lebih besar dibanding akuisisi pelanggan baru."
                )
            else:
                insights.append(
                    f"The At Risk segment makes up {ar['Customer_Share']:.1f}% of the entire customer base "
                    f"({int(ar['Customers']):,} people) — at this scale, retention needs to outweigh new "
                    f"customer acquisition as the primary marketing investment."
                )

    conversion_segments = [
        seg for seg, res in engine_results.items()
        if any(r.id in ("browsing_no_purchase", "checkout_friction") for r in res["triggered"])
    ]
    if conversion_segments:
        if lang == "id":
            insights.append(
                f"Segmen {', '.join(conversion_segments)} menunjukkan keterlibatan tinggi "
                f"(browsing/klik email) tanpa frekuensi pembelian yang sepadan — ini adalah peluang "
                f"konversi terbesar di seluruh basis pelanggan saat ini."
            )
        else:
            insights.append(
                f"The {', '.join(conversion_segments)} segment(s) show high engagement (browsing or "
                f"email clicks) without a matching purchase frequency — this is currently the largest "
                f"conversion opportunity across the customer base."
            )

    one_time_share = None
    reg = profile[profile["Segment"] != "High Value Segment"]
    if not reg.empty:
        low_freq_share = reg.loc[reg["Avg_Frequency"] <= 1.3, "Customer_Share"].sum()
        if low_freq_share >= 40:
            if lang == "id":
                insights.append(
                    f"Sekitar {low_freq_share:.0f}% pelanggan reguler rata-rata hanya bertransaksi "
                    f"1 kali — retensi dan repeat purchase harus menjadi fokus marketing utama "
                    f"dibanding akuisisi."
                )
            else:
                insights.append(
                    f"Roughly {low_freq_share:.0f}% of regular customers average close to a single "
                    f"transaction — retention and repeat-purchase programs should be the primary "
                    f"marketing focus ahead of acquisition."
                )

    n_segments = len(profile)
    if lang == "id":
        insights.append(
            f"Dengan {n_segments} segmen berkarakteristik berbeda mencakup {total_customers:,} pelanggan, "
            f"satu jenis perjalanan CRM untuk semua tidak lagi memadai — setiap segmen di halaman ini "
            f"memerlukan kombinasi kanal dan penawaran yang berbeda."
        )
    else:
        insights.append(
            f"Across {n_segments} behaviorally distinct segments covering {total_customers:,} customers, "
            f"a one-size-fits-all CRM journey is no longer sufficient — each segment on this page needs "
            f"its own channel and offer mix."
        )

    return insights[:5]
