"""
utils/i18n.py
-------------
Lightweight bilingual (English / Bahasa Indonesia) text layer.

Usage:
    from utils.i18n import t
    st.write(t("home.title"))
    st.write(t("kpi.orders", n=42))     # supports .format() kwargs

Language is stored in st.session_state["lang"] ("en" | "id") and toggled from
the sidebar. Unknown keys fall back to English, then to the key itself.
"""

from __future__ import annotations

import streamlit as st

DEFAULT_LANG = "en"
LANGUAGES = {"en": "English", "id": "Indonesia"}


def get_lang() -> str:
    return st.session_state.get("lang", DEFAULT_LANG)


def t(key: str, **kwargs) -> str:
    entry = TR.get(key)
    if entry is None:
        return key
    text = entry.get(get_lang()) or entry.get("en") or key
    return text.format(**kwargs) if kwargs else text


# --------------------------------------------------------------------------- #
# Translations.  Each key -> {"en": ..., "id": ...}
# --------------------------------------------------------------------------- #
TR: dict[str, dict[str, str]] = {
    # ---- Sidebar ------------------------------------------------------------
    "side.language": {"en": "Language", "id": "Bahasa"},
    "side.footer": {
        "en": "CRISP-DM · Deployment<br>RFM + K-Means Clustering<br><span style='opacity:.6;'>Thesis Akmal Zaidan Yusuf</span>",
        "id": "CRISP-DM · Deployment<br>RFM + K-Means Clustering<br><span style='opacity:.6;'>Skripsi Akmal Zaidan Yusuf</span>",
    },

    # ---- Footer -------------------------------------------------------------
    "footer.html": {
        "en": ("<b>PlanetSports.Asia · Customer Segmentation Analytics</b><br>"
               "RFM Model &amp; K-Means Clustering · CRISP-DM Deployment Phase"
               "<span class='dot'>•</span> Built with Streamlit &amp; Plotly"
               "<span class='dot'>•</span> © 2026 Akmal Zaidan Yusuf Thesis Project"),
        "id": ("<b>PlanetSports.Asia · Analitik Segmentasi Pelanggan</b><br>"
               "Model RFM &amp; K-Means Clustering · Tahap Deployment CRISP-DM"
               "<span class='dot'>•</span> Dibuat dengan Streamlit &amp; Plotly"
               "<span class='dot'>•</span> © 2026 Proyek Skripsi Akmal Zaidan Yusuf"),
    },

    # ---- KPIs ---------------------------------------------------------------
    "kpi.total_customers": {"en": "Total Customers", "id": "Total Pelanggan"},
    "kpi.total_revenue": {"en": "Total Revenue", "id": "Total Pendapatan"},
    "kpi.avg_monetary": {"en": "Avg Monetary", "id": "Rata-rata Monetary"},
    "kpi.avg_frequency": {"en": "Avg Frequency", "id": "Rata-rata Frequency"},
    "kpi.avg_recency": {"en": "Avg Recency", "id": "Rata-rata Recency"},
    "kpi.segments": {"en": "Segments", "id": "Segmen"},
    "kpi.active_base": {"en": "active base", "id": "basis aktif"},
    "kpi.orders": {"en": "{n} orders", "id": "{n} transaksi"},
    "kpi.per_customer": {"en": "per customer", "id": "per pelanggan"},
    "kpi.orders_per_customer": {"en": "orders / customer", "id": "transaksi / pelanggan"},
    "kpi.since_last_buy": {"en": "since last buy", "id": "sejak beli terakhir"},
    "kpi.kmeans_clusters": {"en": "3 clusters + High Value", "id": "3 cluster + Bernilai Tinggi"},

    # ---- Common -------------------------------------------------------------
    "common.data_real": {"en": "Source: RAW Data PlanetSports.Asia · {n} customers",
                         "id": "Data asli PlanetSports.Asia · {n} pelanggan"},
    "common.data_synth": {"en": "Synthetic sample data · {n} customers",
                          "id": "Data sampel sintetis · {n} pelanggan"},
    "common.download_csv": {"en": "⬇️ Download CSV", "id": "⬇️ Unduh CSV"},
    "common.next_step": {"en": "Next in the story", "id": "Lanjutan cerita"},

    # ---- Home ---------------------------------------------------------------
    "home.eyebrow": {"en": "CRISP-DM · Deployment Phase", "id": "CRISP-DM · Tahap Deployment"},
    "home.title": {"en": "Customer Segmentation Intelligence", "id": "Inteligensi Segmentasi Pelanggan"},
    "home.subtitle": {
        "en": ("An interactive business-intelligence platform that segments "
               "PlanetSports.Asia customers using the RFM model and K-Means clustering, "
               "turning raw customer data into actionable growth strategies."),
        "id": ("Platform business intelligence interaktif yang menyegmentasikan pelanggan "
               "PlanetSports.Asia menggunakan model RFM dan K-Means clustering, "
               "mengubah data pelanggan mentah menjadi strategi pertumbuhan yang aplikatif."),
    },
    "home.revenue_recency": {"en": "Revenue by Recency", "id": "Pendapatan menurut Recency"},
    "home.revenue_recency_sub": {"en": "Where revenue concentrates by days since last purchase.",
                                 "id": "Konsentrasi pendapatan berdasarkan hari sejak pembelian terakhir."},
    "home.segment_share": {"en": "Segment Share", "id": "Porsi Segmen"},
    "home.segment_share_sub": {"en": "How customers distribute across discovered segments.",
                               "id": "Distribusi pelanggan pada segmen yang ditemukan."},
    "home.explore": {"en": "Explore the Dashboard", "id": "Jelajahi Dashboard"},
    "home.explore_sub": {"en": "Five analytical workspaces plus an AI analyst.",
                         "id": "Lima ruang analitik ditambah analis AI."},

    # Navigation guide cards
    "nav.dashboard": {"en": "Dashboard", "id": "Dashboard"},
    "nav.dashboard_desc": {"en": "KPI cockpit, live filters and the customer directory.",
                          "id": "Kokpit KPI, filter langsung, dan direktori pelanggan."},
    "nav.rfm": {"en": "RFM Analysis", "id": "Analisis RFM"},
    "nav.rfm_desc": {"en": "‎ ‎ Distributions, correlations and RFM scoring.",
                     "id": "‎ ‎ Distribusi, korelasi, dan skor RFM."},
    "nav.cluster": {"en": "K-Means Clustering", "id": "K-Means Clustering"},
    "nav.cluster_desc": {"en": "‎ ‎ Elbow, silhouette, PCA and 3-D cluster views.",
                         "id": "‎ ‎ Elbow, silhouette, PCA, dan tampilan cluster 3-D."},
    "nav.segments": {"en": "Customer Segments", "id": "Segmen Pelanggan"},
    "nav.segments_desc": {"en": "‎ ‎ Top customers, treemaps and detail tables.",
                          "id": "‎ ‎ Pelanggan teratas, treemap, dan tabel detail."},
    "nav.recommend": {"en": "Business Recommendations", "id": "Rekomendasi Bisnis"},
    "nav.recommend_desc": {"en": "‎ ‎ Rule-based CRM recommendations per segment.",
                           "id": "‎ ‎ Rekomendasi CRM berbasis aturan per segmen."},
    # ---- Overview -----------------------------------------------------------
    "ov.eyebrow": {"en": "Overview", "id": "Ikhtisar"},
    "ov.title": {"en": "Business Command Center", "id": "Pusat Kendali Bisnis"},
    "ov.subtitle": {"en": "Track the health of your customer base at a glance and slice it with live filters.",
                    "id": "Pantau kesehatan basis pelanggan sekilas dan iris dengan filter langsung."},
    "ov.filters": {"en": "Filters", "id": "Filter"},
    "ov.filters_sub": {"en": "Every visual below updates instantly with your selection.",
                       "id": "Setiap visual di bawah diperbarui seketika sesuai pilihan Anda."},
    "ov.recency": {"en": "📅 Recency (days since last purchase)", "id": "📅 Recency (hari sejak pembelian terakhir)"},
    "ov.segment": {"en": "🧩 Segment", "id": "🧩 Segmen"},
    "ov.search": {"en": "🔎 Customer search", "id": "🔎 Cari pelanggan"},
    "ov.search_ph": {"en": "ID or hash…", "id": "ID atau hash…"},
    "ov.empty": {"en": "No customers match the current filters. Try widening your selection.",
                 "id": "Tidak ada pelanggan yang cocok dengan filter saat ini. Perluas pilihan Anda."},
    "ov.key_metrics": {"en": "Key Metrics", "id": "Metrik Utama"},
    "ov.segment_mix": {"en": "Segment Mix", "id": "Komposisi Segmen"},
    "ov.segment_mix_sub": {"en": "Customer share across segments.", "id": "Porsi pelanggan antar segmen."},
    "ov.directory": {"en": "Customer Directory", "id": "Direktori Pelanggan"},
    "ov.directory_sub": {"en": "Most valuable customers in the current selection.",
                         "id": "Pelanggan paling bernilai pada pilihan saat ini."},
    "ov.preview": {"en": "📋 Dataset preview (cleaned RFM + engagement)",
                   "id": "📋 Pratinjau dataset (RFM bersih + engagement)"},
    "ov.summary": {"en": "📝 Summary", "id": "📝 Ringkasan"},
    "ov.sum_customers": {"en": "Customers in view", "id": "Pelanggan tampil"},
    "ov.sum_orders": {"en": "Orders in view (Σ frequency)", "id": "Transaksi tampil (Σ frequency)"},
    "ov.sum_revenue": {"en": "Revenue in view", "id": "Pendapatan tampil"},
    "ov.sum_aov": {"en": "Average order value", "id": "Rata-rata nilai transaksi"},
    "ov.sum_segments": {"en": "Segments present", "id": "Segmen yang ada"},

    # ---- RFM ----------------------------------------------------------------
    "rfm.eyebrow": {"en": "RFM Analysis", "id": "Analisis RFM"},
    "rfm.hv_excluded": {"en": "Distributions below exclude {n} High Value (outlier) customers, analyzed separately on Business Recommendations.",
                         "id": "Distribusi di bawah ini tidak menyertakan {n} pelanggan Bernilai Tinggi (outlier), yang dianalisis terpisah pada Rekomendasi Bisnis."},
    "rfm.title": {"en": "Recency · Frequency · Monetary", "id": "Recency · Frequency · Monetary"},
    "rfm.subtitle": {
        "en": ("The behavioural foundation of the segmentation. Recency measures how "
               "recently a customer purchased, Frequency how often, and Monetary how "
               "much — each scored 1–5."),
        "id": ("Fondasi perilaku dari segmentasi. Recency mengukur seberapa baru pelanggan "
               "membeli, Frequency seberapa sering, dan Monetary seberapa besar — "
               "masing-masing diberi skor 1–5."),
    },
    "rfm.distributions": {"en": "RFM Distributions", "id": "Distribusi RFM"},
    "rfm.distributions_sub": {"en": "Shape of each behavioural dimension across all customers.",
                              "id": "Bentuk setiap dimensi perilaku di seluruh pelanggan."},
    "rfm.cap_recency": {"en": "Most customers cluster at low recency — they purchased recently. A long right tail marks lapsing customers.",
                        "id": "Sebagian besar pelanggan berada di recency rendah — baru saja membeli. Ekor kanan yang panjang menandai pelanggan yang mulai pasif."},
    "rfm.cap_frequency": {"en": "Frequency is right-skewed: many one/two-time buyers and a few very loyal repeat purchasers.",
                          "id": "Frequency miring ke kanan: banyak pembeli satu/dua kali dan sedikit pembeli berulang yang sangat loyal."},
    "rfm.cap_monetary": {"en": "Monetary value follows a classic Pareto shape — a minority of customers drive most revenue.",
                         "id": "Nilai Monetary mengikuti pola Pareto klasik — sebagian kecil pelanggan menyumbang mayoritas pendapatan."},
    "rfm.spread": {"en": "Spread & Outliers", "id": "Sebaran & Pencilan"},
    "rfm.spread_sub": {"en": "Normalised so the three metrics share one axis.",
                       "id": "Dinormalisasi agar ketiga metrik berbagi satu sumbu."},
    "rfm.cap_box": {"en": "Boxplots reveal outliers (dots) and the interquartile range. Monetary shows the widest spread and the most high-value outliers.",
                    "id": "Boxplot menampilkan pencilan (titik) dan rentang antarkuartil. Monetary punya sebaran terlebar dan pencilan bernilai tinggi terbanyak."},
    "rfm.correlation": {"en": "Correlation", "id": "Korelasi"},
    "rfm.correlation_sub": {"en": "How the three metrics move together.", "id": "Bagaimana ketiga metrik bergerak bersama."},
    "rfm.cap_corr": {"en": "Frequency and Monetary are positively correlated — customers who buy more often also spend more. Recency is weakly/negatively related to both.",
                     "id": "Frequency dan Monetary berkorelasi positif — pelanggan yang lebih sering membeli juga lebih banyak berbelanja. Recency berhubungan lemah/negatif dengan keduanya."},
    "rfm.density": {"en": "Monetary Density", "id": "Kepadatan Monetary"},
    "rfm.density_sub": {"en": "Smoothed distribution of customer spend.", "id": "Distribusi pengeluaran pelanggan yang dihaluskan."},
    "rfm.cap_density": {"en": "The density curve highlights where the bulk of customers sit and how heavy the high-spend tail is.",
                        "id": "Kurva kepadatan menyoroti di mana mayoritas pelanggan berada dan seberapa berat ekor pengeluaran tinggi."},
    "rfm.score_dist": {"en": "RFM Score Distribution", "id": "Distribusi Skor RFM"},
    "rfm.score_dist_sub": {"en": "Combined R+F+M score (3–15).", "id": "Skor gabungan R+F+M (3–15)."},
    "rfm.cap_score": {"en": "Higher combined scores indicate more valuable customers. The distribution shows how the base splits between weak and strong customers.",
                      "id": "Skor gabungan lebih tinggi menandakan pelanggan lebih bernilai. Distribusi menunjukkan pembagian antara pelanggan lemah dan kuat."},
    "rfm.table": {"en": "RFM Summary Table", "id": "Tabel Ringkasan RFM"},
    "rfm.table_sub": {"en": "Per-customer RFM values and 1–5 scores.", "id": "Nilai RFM per pelanggan dan skor 1–5."},
    "rfm.describe": {"en": "📊 Descriptive statistics", "id": "📊 Statistik deskriptif"},

    # ---- Clustering ---------------------------------------------------------
    "cl.eyebrow": {"en": "K-Means Clustering", "id": "K-Means Clustering"},
    "cl.title": {"en": "Discovering Customer Segments", "id": "Menemukan Segmen Pelanggan"},
    "cl.subtitle": {
        "en": ("K-Means groups customers by their scaled RFM profile. The number of "
               "clusters (k = {k}) is validated below with the "
               "Elbow method and Silhouette score."),
        "id": ("K-Means mengelompokkan pelanggan berdasarkan profil RFM yang diskalakan. Jumlah "
               "cluster (k = {k}) diatur dari sidebar dan divalidasi di bawah dengan metode "
               "Elbow dan skor Silhouette."),
    },
    "cl.howmany": {"en": "How many clusters?", "id": "Berapa jumlah cluster?"},
    "cl.hv_excluded": {"en": "{n} High Value (outlier) customers are excluded from clustering — analyzed separately on Business Recommendations.",
                        "id": "{n} pelanggan Bernilai Tinggi (outlier) dikecualikan dari clustering — dianalisis terpisah pada Rekomendasi Bisnis."},
    "cl.howmany_sub": {"en": "Two complementary methods for choosing k.", "id": "Dua metode pelengkap untuk memilih k."},
    "cl.cap_elbow": {"en": "The Elbow curve shows a sharp decrease in inertia up to k = 3, followed by a much slower decline. This indicates that three clusters provide the best balance between segmentation quality and model complexity.",
                     "id": "Kurva Elbow menunjukkan penurunan inertia yang sangat tajam hingga k = 3, kemudian mulai melandai pada nilai k berikutnya. Pola tersebut menunjukkan bahwa tiga cluster memberikan keseimbangan terbaik antara kualitas segmentasi dan kompleksitas model."},
    "cl.cap_sil": {"en": "The highest Silhouette Score (0.4718) is achieved at k = {k}, indicating the best cluster separation among all tested values. Therefore, k = {k} is selected as the optimal number of clusters.",
                   "id": "Nilai Silhouette Score tertinggi sebesar 0,4718 diperoleh pada k = {k}. Hasil tersebut menunjukkan bahwa pemisahan antar cluster paling baik dibandingkan jumlah cluster lainnya, sehingga k = {k} dipilih sebagai jumlah cluster optimal."},
    "cl.sizes": {"en": "Cluster Sizes", "id": "Ukuran Cluster"},
    "cl.sizes_sub": {"en": "Customers assigned to each segment.", "id": "Pelanggan pada tiap segmen."},
    "cl.cap_sizes": {"en": "Balanced clusters are healthy; a single dominant cluster may signal that k is too low.",
                     "id": "Cluster yang seimbang itu sehat; satu cluster dominan bisa menandakan k terlalu kecil."},
    "cl.scatter": {"en": "Recency vs Monetary", "id": "Recency vs Monetary"},
    "cl.scatter_sub": {"en": "Bubble size encodes Frequency.", "id": "Ukuran gelembung mewakili Frequency."},
    "cl.cap_scatter": {"en": "Champions sit bottom-right (low recency, high monetary, large bubbles). Lost/hibernating customers drift to the upper-left.",
                       "id": "Champions berada di kanan-bawah (recency rendah, monetary tinggi, gelembung besar). Pelanggan hilang/hibernasi bergeser ke kiri-atas."},
    "cl.pca": {"en": "PCA Projection", "id": "Proyeksi PCA"},
    "cl.pca_sub": {"en": "RFM compressed to two principal components.", "id": "RFM dipadatkan menjadi dua komponen utama."},
    "cl.cap_pca": {"en": "PCA collapses the 3-D RFM space onto 2 axes while preserving variance. Clean separation here means the clusters are genuinely distinct.",
                   "id": "PCA memampatkan ruang RFM 3-D ke 2 sumbu sambil mempertahankan variansi. Pemisahan yang bersih berarti cluster benar-benar berbeda."},
    "cl.d3": {"en": "3-D Cluster View", "id": "Tampilan Cluster 3-D"},
    "cl.d3_sub": {"en": "Interactive — drag to rotate.", "id": "Interaktif — seret untuk memutar."},
    "cl.cap_d3": {"en": "Every point is a customer positioned by raw Recency, Frequency and Monetary. Rotate to inspect how the segments occupy the space.",
                  "id": "Setiap titik adalah pelanggan berdasarkan Recency, Frequency, dan Monetary asli. Putar untuk melihat bagaimana segmen mengisi ruang."},
    "cl.profiles": {"en": "Segment Profiles", "id": "Profil Segmen"},
    "cl.profiles_sub": {"en": "What defines each cluster.", "id": "Apa yang mendefinisikan tiap cluster."},
    "cl.cap_avg": {"en": "Average RFM per segment (normalised). Compare the bar heights to read each segment's personality at a glance.",
                   "id": "Rata-rata RFM per segmen (dinormalisasi). Bandingkan tinggi batang untuk membaca karakter tiap segmen sekilas."},
    "cl.cap_radar": {"en": "The radar plots freshness (inverted recency), frequency and monetary. A larger, outward shape means a more valuable segment.",
                     "id": "Radar memplot kesegaran (recency terbalik), frequency, dan monetary. Bentuk yang lebih luas berarti segmen lebih bernilai."},
    "cl.parallel": {"en": "Parallel Coordinates", "id": "Koordinat Paralel"},
    "cl.parallel_sub": {"en": "Trace how customers flow across the three metrics.", "id": "Telusuri aliran pelanggan pada ketiga metrik."},
    "cl.cap_parallel": {"en": "Each line is a customer, coloured by cluster. Tight, parallel bands indicate customers within a cluster behave consistently.",
                        "id": "Setiap garis adalah pelanggan, diwarnai per cluster. Pita yang rapat dan sejajar menandakan perilaku konsisten dalam satu cluster."},
    "cl.table": {"en": "Cluster Profile Table", "id": "Tabel Profil Cluster"},
    "cl.table_sub": {"en": "Numeric summary of every segment.", "id": "Ringkasan numerik setiap segmen."},
    "cl.cap_table_rev": {"en": "Revenue % is share of total company revenue — these three clusters won't sum to 100% here, since the High Value Segment's ~35% share (excluded from clustering) is shown on Business Recommendations.",
                          "id": "Persentase Pendapatan adalah porsi dari total pendapatan perusahaan — ketiga cluster ini tidak akan berjumlah 100% di sini, karena porsi ~35% Segmen Bernilai Tinggi (dikecualikan dari clustering) ditampilkan pada Rekomendasi Bisnis."},

    # ---- Customer Segments --------------------------------------------------
    "cs.eyebrow": {"en": "Customer Insight", "id": "Wawasan Pelanggan"},
    "cs.title": {"en": "Know Your Customers", "id": "Kenali Pelanggan Anda"},
    "cs.subtitle": {"en": "Spotlight your most valuable customers and understand how segments compose your revenue.",
                    "id": "Soroti pelanggan paling bernilai dan pahami bagaimana segmen menyusun pendapatan Anda."},
    "cs.top": {"en": "Top Customers", "id": "Pelanggan Teratas"},
    "cs.top_sub": {"en": "Leaders by spend, loyalty and recency.", "id": "Terdepan dalam pengeluaran, loyalitas, dan recency."},
    "cs.largest": {"en": "💰 Largest Monetary", "id": "💰 Monetary Terbesar"},
    "cs.frequent": {"en": "🔁 Most Frequent", "id": "🔁 Paling Sering"},
    "cs.recent": {"en": "⏱️ Recently Active", "id": "⏱️ Baru Aktif"},
    "cs.orders": {"en": "{n} orders", "id": "{n} transaksi"},
    "cs.days_ago": {"en": "{n} days ago", "id": "{n} hari lalu"},
    "cs.composition": {"en": "Segment Composition", "id": "Komposisi Segmen"},
    "cs.composition_sub": {"en": "Three lenses on how your base is structured.", "id": "Tiga sudut pandang struktur basis pelanggan Anda."},
    "cs.cap_treemap": {"en": "Treemap area = revenue contribution; colour = customer count. Large-area / small-count tiles are your high-value niches.",
                       "id": "Luas treemap = kontribusi pendapatan; warna = jumlah pelanggan. Ubin berluas besar/berjumlah kecil adalah ceruk bernilai tinggi."},
    "cs.cap_donut": {"en": "The donut shows headcount share, which often differs sharply from revenue share.",
                     "id": "Donat menampilkan porsi jumlah pelanggan, yang sering berbeda tajam dari porsi pendapatan."},
    "cs.tier": {"en": "Segmented by Spend Tier", "id": "Segmentasi Berdasarkan Tingkat Pengeluaran"},
    "cs.tier_sub": {"en": "Drill from segment into spend bands.", "id": "Telusuri dari segmen ke rentang pengeluaran."},
    "cs.cap_sunburst": {"en": "The sunburst nests spend tiers inside each segment — click a segment to zoom in on its internal spread.",
                        "id": "Sunburst menyusun tingkat pengeluaran di dalam tiap segmen — klik segmen untuk memperbesar sebaran internalnya."},
    "cs.engagement": {"en": "Marketing Engagement", "id": "Keterlibatan Pemasaran"},
    "cs.engagement_sub": {"en": "How responsive each segment is to marketing touchpoints.",
                          "id": "Seberapa responsif tiap segmen terhadap titik sentuh pemasaran."},
    "cs.cap_engagement": {"en": "Built from real email-open, site-activity and content-click counters. Highly engaged, high-value segments are prime targets for premium campaigns; low-engagement segments may need channel or creative changes.",
                          "id": "Dibangun dari data nyata pembukaan email, aktivitas situs, dan klik konten. Segmen dengan keterlibatan dan nilai tinggi adalah target utama kampanye premium; segmen keterlibatan rendah mungkin perlu perubahan kanal atau materi."},
    "cs.detail": {"en": "Customer Detail Table", "id": "Tabel Detail Pelanggan"},
    "cs.detail_sub": {"en": "Search, sort, filter and export the full customer list.",
                      "id": "Cari, urutkan, filter, dan ekspor daftar pelanggan lengkap."},
    "cs.search": {"en": "🔎 Search by name or ID", "id": "🔎 Cari berdasarkan nama atau ID"},
    "cs.search_ph": {"en": "e.g. Aisha or CUST-00042", "id": "mis. Aisha atau CUST-00042"},
    "cs.filter_segment": {"en": "Filter by segment", "id": "Filter berdasarkan segmen"},
    "cs.empty": {"en": "No customers match your search.", "id": "Tidak ada pelanggan yang cocok dengan pencarian Anda."},

    # ---- Business Recommendations -------------------------------------------
    "br.eyebrow": {"en": "Business Recommendation", "id": "Rekomendasi Bisnis"},
    "br.title": {"en": "From Segments to Strategy", "id": "Dari Segmen ke Strategi"},
    "br.subtitle": {
        "en": ("A rule-based CRM decision engine — priority-scored, data-driven recommendations "
               "for every discovered segment, the practical payoff of the CRISP-DM deployment phase."),
        "id": ("Mesin keputusan CRM berbasis aturan — rekomendasi berbasis data dengan skor prioritas "
               "untuk setiap segmen yang ditemukan — hasil nyata dari tahap deployment CRISP-DM."),
    },
    "br.characteristics": {"en": "Characteristics", "id": "Karakteristik"},
    "br.meaning": {"en": "Business Meaning", "id": "Makna Bisnis"},
    "br.hv_eyebrow": {"en": "High Value Segment", "id": "Segmen Bernilai Tinggi"},
    "br.hv_sub": {"en": "Drives {rs:.1f}% of total revenue from just {cs:.1f}% of the customer base — protect it first.",
                  "id": "Menyumbang {rs:.1f}% dari total pendapatan hanya dari {cs:.1f}% basis pelanggan — lindungi segmen ini terlebih dahulu."},
    "br.hv_customers": {"en": "customers", "id": "pelanggan"},
    "br.hv_avg": {"en": "avg. spend / customer", "id": "rata-rata belanja / pelanggan"},
    "br.hv_total": {"en": "total revenue", "id": "total pendapatan"},
    "br.marketing": {"en": "Marketing Strategy", "id": "Strategi Pemasaran"},
    "br.retention": {"en": "Retention Strategy", "id": "Strategi Retensi"},
    "br.promotion": {"en": "Promotion Recommendation", "id": "Rekomendasi Promosi"},
    "br.crm": {"en": "CRM Recommendation", "id": "Rekomendasi CRM"},
    "br.impact": {"en": "Expected Business Impact", "id": "Dampak Bisnis yang Diharapkan"},
    "br.summary": {"en": "Customer Summary", "id": "Ringkasan Pelanggan"},
    "br.strategy": {"en": "Recommended Marketing Strategy", "id": "Strategi Marketing yang Direkomendasikan"},
    "br.none": {"en": "No actions at this tier", "id": "Tidak ada aksi di tingkat ini"},
    "br.why": {"en": "Why", "id": "Alasan"},
    "br.outcome": {"en": "Expected Outcome", "id": "Hasil yang Diharapkan"},
    "br.insights_title": {"en": "Strategic Insights", "id": "Wawasan Strategis"},
    "br.insights_sub": {"en": "Executive summary generated from every segment on this page.",
                          "id": "Ringkasan eksekutif yang dihasilkan dari seluruh segmen di halaman ini."},
    "br.char_text": {"en": "Avg recency <b>{r:.0f} days</b>, avg frequency <b>{f:.1f} orders</b>, avg spend <b>{m}</b>.",
                     "id": "Rata-rata recency <b>{r:.0f} hari</b>, rata-rata frequency <b>{f:.1f} transaksi</b>, rata-rata belanja <b>{m}</b>."},
    "br.meta": {"en": "{n} customers · {cs:.1f}% of base · {rs:.1f}% of revenue",
                "id": "{n} pelanggan · {cs:.1f}% dari basis · {rs:.1f}% dari pendapatan"},

    # ---- Chart titles / axis labels ----------------------------------------
    "chart.dist": {"en": "{col} Distribution", "id": "Distribusi {col}"},
    "chart.density": {"en": "{col} Density", "id": "Kepadatan {col}"},
    "chart.customers": {"en": "Customers", "id": "Pelanggan"},
    "chart.density_y": {"en": "Density", "id": "Kepadatan"},
    "chart.histogram": {"en": "Histogram", "id": "Histogram"},
    "chart.rfm_spread": {"en": "RFM Spread (normalised 0–100)", "id": "Sebaran RFM (dinormalisasi 0–100)"},
    "chart.norm_value": {"en": "Normalised value", "id": "Nilai ternormalisasi"},
    "chart.corr": {"en": "RFM Correlation Heatmap", "id": "Heatmap Korelasi RFM"},
    "chart.combined_score": {"en": "RFM Combined Score Distribution", "id": "Distribusi Skor Gabungan RFM"},
    "chart.score_x": {"en": "R+F+M score (3–15)", "id": "Skor R+F+M (3–15)"},
    "chart.elbow": {"en": "Elbow Method", "id": "Metode Elbow"},
    "chart.k_axis": {"en": "Number of clusters (k)", "id": "Jumlah cluster (k)"},
    "chart.inertia": {"en": "Inertia (WSS)", "id": "Inertia (WSS)"},
    "chart.selected_k": {"en": "selected k = {k}", "id": "k terpilih = {k}"},
    "chart.sil_title": {"en": "Silhouette Score by k", "id": "Skor Silhouette per k"},
    "chart.silhouette": {"en": "Silhouette", "id": "Silhouette"},
    "chart.cust_per_seg": {"en": "Customers per Segment", "id": "Pelanggan per Segmen"},
    "chart.scatter_title": {"en": "Recency vs Monetary (bubble = Frequency, log scale)",
                            "id": "Recency vs Monetary (gelembung = Frequency, skala log)"},
    "chart.pca_title": {"en": "PCA Projection (2 components)", "id": "Proyeksi PCA (2 komponen)"},
    "chart.d3_title": {"en": "3D Cluster View", "id": "Tampilan Cluster 3D"},
    "chart.avg_rfm": {"en": "Average RFM per Segment (normalised)", "id": "Rata-rata RFM per Segmen (dinormalisasi)"},
    "chart.norm_0_100": {"en": "Normalised 0–100", "id": "Ternormalisasi 0–100"},
    "chart.radar": {"en": "Segment RFM Radar", "id": "Radar RFM Segmen"},
    "chart.radar_fresh": {"en": "Recency (fresh)", "id": "Recency (segar)"},
    "chart.parallel": {"en": "Parallel Coordinates — RFM by Cluster", "id": "Koordinat Paralel — RFM per Cluster"},
    "chart.treemap": {"en": "Revenue Contribution by Segment (Treemap)", "id": "Kontribusi Pendapatan per Segmen (Treemap)"},
    "chart.donut": {"en": "Customer Share by Segment", "id": "Porsi Pelanggan per Segmen"},
    "chart.sunburst": {"en": "Segment → Spend Tier (Sunburst)", "id": "Segmen → Tingkat Pengeluaran (Sunburst)"},
    "chart.low_spend": {"en": "Low Spend", "id": "Belanja Rendah"},
    "chart.mid_spend": {"en": "Mid Spend", "id": "Belanja Sedang"},
    "chart.high_spend": {"en": "High Spend", "id": "Belanja Tinggi"},
    "chart.rev_recency": {"en": "Revenue by Recency Band", "id": "Pendapatan per Rentang Recency"},
    "chart.days_since": {"en": "Days since last transaction", "id": "Hari sejak transaksi terakhir"},
    "chart.revenue_rp": {"en": "Revenue (Rp)", "id": "Pendapatan (Rp)"},
    "chart.cust_recency": {"en": "Customers by Recency Band", "id": "Pelanggan per Rentang Recency"},
    "chart.engagement": {"en": "Marketing Engagement by Segment", "id": "Keterlibatan Pemasaran per Segmen"},
    "chart.engagement_x": {"en": "Avg engagement score (0–100)", "id": "Rata-rata skor keterlibatan (0–100)"},
}
