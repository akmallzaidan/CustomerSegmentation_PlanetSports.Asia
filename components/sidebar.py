"""
components/sidebar.py
---------------------
Branded sidebar: clean logo mark, language switch and footer.

The dashboard is single-theme (dark navy) and always clusters at the
thesis-optimal k = 3, so no appearance or model controls live here anymore —
just brand identity, language and the auto-generated page navigation
(driven by `st.navigation()` in `app.py`).
"""

from __future__ import annotations

import os

import streamlit as st

from components import theme
from utils.i18n import LANGUAGES, t


def render_sidebar() -> None:
    """Render the brand mark + shared controls in the sidebar. Called once."""
    # st.logo places the brand mark ABOVE the page navigation.
    if os.path.exists(theme.LOGO_PATH):
        st.logo(theme.LOGO_PATH, size="large", link=None)

    with st.sidebar:
        # ---- Fallback brand (only if the logo file is missing) ---------- #
        if not os.path.exists(theme.LOGO_PATH):
            st.markdown(
                """
                <div class="sidebar-brand">
                    <div class="brand-mark">🏃</div>
                    <div class="brand-text">
                        <b>PlanetSports.Asia</b>
                        <span>Segmentation AI</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ---- Language ---------------------------------------------------- #
        st.markdown(f'<div class="nav-hint">{t("side.language")}</div>', unsafe_allow_html=True)
        codes = list(LANGUAGES.keys())
        current = st.session_state.get("lang", "en")
        chosen = st.radio(
            "language", options=codes, index=codes.index(current),
            format_func=lambda c: f"🇬🇧 {LANGUAGES[c]}" if c == "en" else f"🇮🇩 {LANGUAGES[c]}",
            horizontal=True, label_visibility="collapsed", key="lang_radio",
        )
        if chosen != current:
            st.session_state["lang"] = chosen
            st.rerun()

        st.markdown(
            f'<div class="sidebar-footer">{t("side.footer")}</div>',
            unsafe_allow_html=True,
        )
