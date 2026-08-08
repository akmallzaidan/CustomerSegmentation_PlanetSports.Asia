"""
components/cards.py
-------------------
HTML/CSS card builders: animated KPI cards, section headers, page hero,
recommendation cards and empty states.
"""

from __future__ import annotations

import streamlit as st


def page_hero(eyebrow: str, title: str, subtitle: str) -> None:
    """Large gradient page header."""
    st.markdown(
        f"""
        <div class="page-hero fade-in">
            <div class="eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    sub = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="section-title">{title}</div>{sub}',
        unsafe_allow_html=True,
    )


def kpi_card(
    label: str,
    value: str,
    icon: str = "insights",
    delta: str | None = None,
    direction: str = "flat",
) -> None:
    """A single animated KPI card. `icon` is a Material Icons Round ligature."""
    delta_html = ""
    if delta:
        arrow = {"up": "▲", "down": "▼", "flat": "—"}.get(direction, "—")
        delta_html = f'<div class="kpi-delta {direction}">{arrow} {delta}</div>'
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-icon"><span class="material-icons-round">{icon}</span></div>
            </div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(cards: list[dict]) -> None:
    """Render a responsive row of KPI cards from a list of dicts."""
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            kpi_card(
                label=card["label"],
                value=card["value"],
                icon=card.get("icon", "insights"),
                delta=card.get("delta"),
                direction=card.get("direction", "flat"),
            )


def glass_open(title: str = "", note: str = "") -> None:
    """Open a glass container (remember to call `glass_close`)."""
    head = f'<div class="chart-title">{title}</div>' if title else ""
    sub = f'<div class="chart-note">{note}</div>' if note else ""
    st.markdown(f'<div class="glass-card fade-in">{head}{sub}', unsafe_allow_html=True)


def glass_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def chart_caption(text: str) -> None:
    """Interpretation text shown under a chart."""
    st.markdown(f'<div class="chart-note">💬 {text}</div>', unsafe_allow_html=True)


def recommendation_card(segment: str, emoji: str, meta: str, items: list[tuple[str, str, str]]) -> None:
    """Modern recommendation card.

    `items` is a list of (icon, label, body) tuples rendered in a 2-col grid.
    """
    grid = "".join(
        f"""
        <div class="rec-item">
            <div class="rec-label"><span class="material-icons-round" style="font-size:15px;">{icon}</span>{label}</div>
            <div class="rec-body">{body}</div>
        </div>
        """
        for icon, label, body in items
    )
    st.markdown(
        f"""
        <div class="rec-card fade-in">
            <div class="rec-head">
                <div class="rec-emoji">{emoji}</div>
                <div>
                    <h3>{segment}</h3>
                    <div class="rec-meta">{meta}</div>
                </div>
            </div>
            <div class="rec-grid">{grid}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nav_link_card(page: str, icon: str, title: str, desc: str, key: str) -> None:
    """A clickable glass card that navigates to another page via st.page_link.

    `page` is the file path (relative to app.py) of the target view, e.g.
    'views/rfm_analysis.py'. `key` must be unique per card on the page.
    """
    with st.container(key=key):
        if icon:
            st.page_link(page, label=title, icon=icon)
        else:
            st.page_link(page, label=title)
        st.markdown(f'<div class="nav-card-desc muted">{desc}</div>', unsafe_allow_html=True)


def story_next(page: str, icon: str, label: str, caption: str) -> None:
    """A single 'continue the story' link pointing to the next analytical page."""
    st.write("")
    with st.container(key="story_next"):
        st.markdown(f'<div class="story-next-eyebrow">{caption}</div>', unsafe_allow_html=True)
        st.page_link(page, label=label, icon=icon)


def _flat(html: str) -> str:
    """Strip leading whitespace from every line before handing HTML to
    st.markdown(). Markdown treats any line indented 4+ spaces as a
    preformatted code block — deeply nested f-string HTML (like the cards
    below) hits that rule easily, so this keeps newlines (harmless) while
    removing the indentation (not harmless)."""
    return "\n".join(line.lstrip() for line in html.split("\n"))


def priority_stars_html(stars: int, label: str) -> str:
    """★★★★★-style priority badge (1-5 filled stars + text label)."""
    filled = "★" * stars
    empty = "☆" * (5 - stars)
    tier_class = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "monitor"}.get(stars, "medium")
    return (
        f'<div class="priority-badge priority-{tier_class}">'
        f'<span class="priority-stars">{filled}<span class="priority-stars-empty">{empty}</span></span>'
        f'<span class="priority-label">{label}</span></div>'
    )


def business_recommendation_card(data: dict) -> None:
    """Render one CRM decision-support card for a segment.

    `data` is a plain dict assembled by the view from the recommendation
    engine's output — this function only renders, it makes no business
    decisions. Expected keys: emoji, name, meta, summary,
    actions[{name,why,outcome,channel,tier}], labels{...section headings...}.
    """
    L = data["labels"]

    tier_dot = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢"}
    actions_html = "".join(
        _flat(f'''<div class="action-card action-tier-{a["tier"]}">
            <div class="action-head">{tier_dot.get(a["tier"], "🟢")} <span class="action-name">{a["name"]}</span>
                <span class="action-channel">{a["channel"]}</span></div>
            <div class="action-why"><b>{L["why"]}:</b> {a["why"]}</div>
            <div class="action-outcome"><b>{L["outcome"]}:</b> {a["outcome"]}</div>
        </div>''')
        for a in data["actions"]
    )

    st.markdown(
        _flat(f"""
        <div class="reco-card fade-in">
            <div class="reco-header">
                <div class="reco-emoji">{data['emoji']}</div>
                <div class="reco-heading">
                    <div class="reco-title">{data['name']}</div>
                    <div class="reco-meta">{data['meta']}</div>
                </div>
            </div>

            <div class="reco-block reco-summary">
                <div class="section-label">📊 {L['summary']}</div>
                <div class="reco-summary-text">{data['summary']}</div>
            </div>

            <div class="reco-block">
                <div class="section-label">⭐ {L['strategy']}</div>
                <div class="action-grid">{actions_html}</div>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )



def strategic_insight_panel(title: str, insights: list[str]) -> None:
    """Executive insight panel at the bottom of Business Recommendations."""
    items = "".join(f"<li>{i}</li>" for i in insights)
    st.markdown(
        _flat(f"""
        <div class="insight-panel fade-in">
            <div class="section-label">💼 {title}</div>
            <ul class="insight-list">{items}</ul>
        </div>
        """),
        unsafe_allow_html=True,
    )


def empty_state(message: str, icon: str = "🔍") -> None:
    st.markdown(
        f"""
        <div class="glass-card empty-state">
            <div class="es-icon">{icon}</div>
            <div>{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer() -> None:
    from utils.i18n import t
    st.markdown(f'<div class="ps-footer">{t("footer.html")}</div>', unsafe_allow_html=True)
