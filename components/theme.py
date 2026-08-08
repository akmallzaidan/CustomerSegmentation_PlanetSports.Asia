"""
components/theme.py
-------------------
Central design-system: colour palette, Plotly templates and the routine that
injects the global CSS. `configure_app()` is called once from `app.py`.
"""

from __future__ import annotations

import os

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(_BASE_DIR, "assets")
CSS_PATH = os.path.join(ASSETS_DIR, "style.css")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")

# --------------------------------------------------------------------------- #
# Brand palette
# --------------------------------------------------------------------------- #
PRIMARY = "#0B1F3A"      # Navy blue
SECONDARY = "#173F73"
ACCENT = "#2E6EF7"       # Electric blue
ACCENT_2 = "#38BDF8"     # Cyan
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
DANGER = "#EF4444"

# A qualitative palette used across every categorical chart.
CATEGORICAL = [
    "#2E6EF7", "#38BDF8", "#22C55E", "#F59E0B",
    "#A855F7", "#EF4444", "#14B8A6", "#EC4899",
]
# Sequential (navy -> cyan) for heatmaps / continuous encodings.
SEQUENTIAL = [
    [0.0, "#112D4E"],
    [0.35, "#1D4E89"],
    [0.70, "#3B82F6"],
    [1.0, "#67E8F9"],
]


def _register_plotly_templates() -> None:
    """Register rounded, dark & light Plotly templates once."""
    common = dict(
        font=dict(family="Poppins, sans-serif", size=13),
        colorway=CATEGORICAL,
        margin=dict(l=60, r=30, t=60, b=50),
        hoverlabel=dict(
            font=dict(family="Poppins, sans-serif", size=12),
            bordercolor="rgba(0,0,0,0)",
        ),
    )

    dark = go.layout.Template()
    dark.layout = go.Layout(
        **common,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E2E8F0",
        title_font=dict(family="Poppins, sans-serif", size=18, color="#F8FAFC"),
        xaxis=dict(gridcolor="rgba(148,163,184,0.15)", zerolinecolor="rgba(148,163,184,0.2)"),
        yaxis=dict(gridcolor="rgba(148,163,184,0.15)", zerolinecolor="rgba(148,163,184,0.2)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    dark.layout.hoverlabel.bgcolor = "#173F73"

    light = go.layout.Template()
    light.layout = go.Layout(
        **common,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#334155",
        title_font=dict(family="Poppins, sans-serif", size=18, color="#0B1F3A"),
        xaxis=dict(gridcolor="rgba(15,23,42,0.08)", zerolinecolor="rgba(15,23,42,0.12)"),
        yaxis=dict(gridcolor="rgba(15,23,42,0.08)", zerolinecolor="rgba(15,23,42,0.12)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    light.layout.hoverlabel.bgcolor = "#2E6EF7"

    pio.templates["ps_dark"] = dark
    pio.templates["ps_light"] = light


_register_plotly_templates()


def plotly_template() -> str:
    """Return the Plotly template name. The dashboard is dark-navy only."""
    return "ps_dark"


def init_session_state() -> None:
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("lang", "en")


def load_css() -> None:
    """Inject the global stylesheet."""
    if os.path.exists(CSS_PATH):
        with open(CSS_PATH, "r", encoding="utf-8") as fh:
            st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)


def configure_app(title: str = "PlanetSports Analytics", icon: str = "🏃", layout: str = "wide") -> None:
    """One-call app bootstrap: set page config, session state and CSS.

    Called exactly once, from the top-level `app.py`, before `st.navigation()`
    takes over routing between the views in `views/`.
    """
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state="expanded",
    )
    init_session_state()
    load_css()


def apply_chart_theme(fig: go.Figure, height: int = 380) -> go.Figure:
    """Apply the active template + consistent sizing / config to a figure."""
    fig.update_layout(
        template=plotly_template(),
        height=height,
        # Title lives at the top; legend at the bottom-centre so the two never
        # overlap (previously the top-right legend collided with the title).
        margin=dict(l=55, r=25, t=58, b=72),
        title=dict(y=0.97, yanchor="top", x=0.02, xanchor="left"),
        legend=dict(
            orientation="h", yanchor="top", y=-0.18,
            xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


# Consistent Plotly modebar / interactivity config for every chart.
CHART_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}
