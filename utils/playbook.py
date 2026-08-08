"""
utils/playbook.py
-----------------
Per-segment strategy playbooks in English and Bahasa Indonesia.

The four segments mirror the thesis notebook exactly:
  * "High Value Segment" — Monetary IQR outliers OR Frequency > p99,
    separated BEFORE clustering (Section 4.3.4 of the notebook).
  * "Champions" / "Potential Loyalist" / "At Risk" — the k = 3 K-Means
    result trained on the remaining regular customers (Section 4.4–4.5).

Each segment maps to: meaning, marketing, retention, promotion, crm, impact.
Content for all four segments is adapted directly from the notebook's own
`rekomendasi_strategi` dictionary (Section 4.6), expanded into this card
format. Selected by the active language via `get_playbook()`.
"""

from __future__ import annotations

PLAYBOOK_EN: dict[str, dict[str, str]] = {
    "High Value Segment": {
        "meaning": "Customers flagged as Monetary outliers (IQR rule) or Frequency outliers (top 1%) and separated from clustering. The smallest group by headcount but the single largest contributor to revenue — protecting it is the top business priority.",
        "marketing": "Dedicated relationship management: a named account or priority-service line, early access to new product drops, and personal product consultations rather than mass-market campaigns.",
        "retention": "Treat retention as the #1 budget priority — losing even a few of these customers has an outsized revenue impact relative to their headcount.",
        "promotion": "Avoid blanket discounts, which erode margin unnecessarily; offer white-glove service and exclusivity instead of price cuts.",
        "crm": "Route to a dedicated account manager / VIP service queue; monitor individually rather than through automated lifecycle flows.",
        "impact": "This segment drives the largest share of total revenue from the fewest customers — retention here protects the business's revenue base more than any other single initiative.",
    },
    "Champions": {
        "meaning": "Within the regular customer base, the cluster with the highest Frequency and Monetary values — the best-performing group after the High Value outliers were separated out.",
        "marketing": "Exclusive VIP-tier loyalty programs, early access to new products, and cross-sell/up-sell toward premium items.",
        "retention": "Proactive account care and a premium loyalty program to lock in their habit before it fades.",
        "promotion": "Value-adds (free express shipping, bundles, limited editions) rather than deep discounts, to protect margin.",
        "crm": "Priority-service treatment and personalised touchpoints using full purchase history.",
        "impact": "Retaining and growing this cluster compounds revenue without the acquisition cost of chasing new customers.",
    },
    "Potential Loyalist": {
        "meaning": "The cluster with the lowest Recency (most recently active) but Frequency and Monetary still comparable to the At Risk cluster — customers who are engaged right now but haven't yet proven repeat value.",
        "marketing": "Nurturing programs to push toward a second purchase: targeted next-purchase coupons and recommendations built from browsing history.",
        "retention": "Second-purchase nudges and welcome-series content while their recent engagement is still warm.",
        "promotion": "Time-limited next-purchase offers and free-shipping thresholds to increase basket size.",
        "crm": "Track second- and third-purchase conversion closely; trigger nurture flows automatically.",
        "impact": "Converting this cluster into Champions expands the high-value base for the next period.",
    },
    "At Risk": {
        "meaning": "The cluster with the highest Recency (longest since last purchase) and the lowest Frequency/Monetary — and the largest customer count of the three clusters, making reactivation here high-leverage.",
        "marketing": "Win-back campaigns: high-value reactivation coupons and personalised notifications based on past purchases.",
        "retention": "A clear, compelling reason to return now — this is the largest cluster, so even a modest reactivation rate protects meaningful revenue.",
        "promotion": "Time-limited win-back discounts and reminders of previously browsed or abandoned items.",
        "crm": "Automated churn-risk triggers based on days-since-last-purchase thresholds.",
        "impact": "Because this is the largest cluster by headcount, reactivation efforts here have the biggest potential reach across the customer base.",
    },
}

DEFAULT_EN = {
    "meaning": "A distinct behavioural group identified by the segmentation model.",
    "marketing": "Tailor messaging to this segment's recency, frequency and spend profile.",
    "retention": "Design engagement flows that match how often this group buys.",
    "promotion": "Match promotion depth to the segment's price sensitivity and margin.",
    "crm": "Automate lifecycle touchpoints appropriate to this segment.",
    "impact": "Targeted treatment improves conversion and protects revenue.",
}

PLAYBOOK_ID: dict[str, dict[str, str]] = {
    "High Value Segment": {
        "meaning": "Pelanggan yang teridentifikasi sebagai outlier Monetary (metode IQR) atau outlier Frequency (1% teratas), dan dipisahkan sebelum proses clustering. Kelompok dengan jumlah pelanggan paling sedikit, namun penyumbang omzet terbesar — retensinya menjadi prioritas bisnis utama.",
        "marketing": "Program relationship management khusus: dedicated account atau layanan prioritas, akses awal (early access) terhadap produk baru, serta konsultasi produk personal — bukan kampanye massal.",
        "retention": "Jadikan retensi segmen ini prioritas anggaran utama — kehilangan meskipun sedikit pelanggan di sini berdampak besar terhadap pendapatan dibanding jumlah pelanggannya.",
        "promotion": "Hindari diskon massal yang menggerus margin secara tidak perlu; tawarkan layanan premium dan eksklusivitas alih-alih potongan harga.",
        "crm": "Arahkan ke dedicated account manager / antrean layanan VIP; pantau secara individual, bukan lewat alur otomatis massal.",
        "impact": "Segmen ini menyumbang porsi omzet terbesar dari jumlah pelanggan paling sedikit — mempertahankannya melindungi basis pendapatan bisnis lebih dari inisiatif lainnya.",
    },
    "Champions": {
        "meaning": "Di antara pelanggan reguler, cluster dengan nilai Frequency dan Monetary tertinggi — kelompok berkinerja terbaik setelah segmen bernilai tinggi dipisahkan.",
        "marketing": "Program loyalitas VIP eksklusif, akses awal terhadap produk baru, serta cross-sell dan up-sell produk premium.",
        "retention": "Perawatan akun yang proaktif dan program loyalitas premium untuk mengunci kebiasaan belanja mereka sebelum memudar.",
        "promotion": "Nilai tambah (gratis ongkir ekspres, bundel, edisi terbatas) alih-alih diskon besar, guna menjaga margin.",
        "crm": "Perlakuan layanan prioritas dan personalisasi setiap titik sentuh menggunakan riwayat pembelian lengkap.",
        "impact": "Mempertahankan dan menumbuhkan cluster ini melipatgandakan pendapatan tanpa biaya akuisisi pelanggan baru.",
    },
    "Potential Loyalist": {
        "meaning": "Cluster dengan Recency terendah (paling baru aktif bertransaksi) namun Frequency dan Monetary masih setara dengan cluster At Risk — pelanggan yang aktif saat ini tetapi belum membuktikan nilai pembelian berulang.",
        "marketing": "Program nurturing untuk mendorong transaksi kedua: kupon khusus pembelian berikutnya dan rekomendasi berdasarkan riwayat penelusuran.",
        "retention": "Dorongan pembelian kedua dan konten seri sambutan selagi keterlibatan mereka masih hangat.",
        "promotion": "Penawaran pembelian berikutnya berbatas waktu dan ambang gratis ongkir untuk menaikkan nilai keranjang.",
        "crm": "Pantau konversi pembelian kedua dan ketiga secara cermat; picu alur nurturing secara otomatis.",
        "impact": "Mengonversi cluster ini menjadi Champions memperluas basis pelanggan bernilai tinggi pada periode berikutnya.",
    },
    "At Risk": {
        "meaning": "Cluster dengan Recency tertinggi (paling lama sejak transaksi terakhir) serta Frequency/Monetary terendah — dan jumlah pelanggan terbesar di antara ketiga cluster, sehingga reaktivasi di sini berdaya ungkit tinggi.",
        "marketing": "Kampanye win-back: kupon reaktivasi bernilai tinggi dan notifikasi personal berdasarkan produk yang pernah dibeli.",
        "retention": "Berikan alasan yang jelas dan menarik untuk kembali sekarang — ini cluster terbesar, sehingga tingkat reaktivasi sedang saja tetap melindungi pendapatan yang berarti.",
        "promotion": "Diskon win-back berbatas waktu dan pengingat barang yang pernah dilihat/ditinggalkan.",
        "crm": "Pemicu risiko churn otomatis berdasarkan ambang hari sejak pembelian terakhir.",
        "impact": "Karena ini cluster terbesar dari sisi jumlah pelanggan, upaya reaktivasi di sini berpotensi menjangkau bagian terbesar dari basis pelanggan.",
    },
}

DEFAULT_ID = {
    "meaning": "Kelompok perilaku berbeda yang diidentifikasi oleh model segmentasi.",
    "marketing": "Sesuaikan pesan dengan profil recency, frequency, dan belanja segmen ini.",
    "retention": "Rancang alur keterlibatan yang sesuai dengan seberapa sering kelompok ini membeli.",
    "promotion": "Sesuaikan kedalaman promosi dengan sensitivitas harga dan margin segmen.",
    "crm": "Otomasikan titik sentuh siklus hidup yang sesuai untuk segmen ini.",
    "impact": "Perlakuan yang tertarget meningkatkan konversi dan melindungi pendapatan.",
}


def get_playbook(lang: str) -> tuple[dict, dict]:
    """Return (playbook, default) for the requested language."""
    if lang == "id":
        return PLAYBOOK_ID, DEFAULT_ID
    return PLAYBOOK_EN, DEFAULT_EN
