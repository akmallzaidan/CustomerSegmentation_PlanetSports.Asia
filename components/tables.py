"""
components/tables.py
--------------------
Interactive table rendering. Uses streamlit-aggrid when available
(sorting, filtering, search, pagination) and gracefully falls back to a
styled `st.dataframe` when the package is not installed — so the app always
runs.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

try:  # Optional dependency — graceful fallback if missing.
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    from st_aggrid.shared import JsCode

    _HAS_AGGRID = True
except Exception:  # pragma: no cover - import guard
    _HAS_AGGRID = False


def interactive_table(
    df: pd.DataFrame,
    height: int = 420,
    page_size: int = 12,
    key: str | None = None,
) -> None:
    """Render an interactive, sortable, filterable, paginated table."""
    if _HAS_AGGRID:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(
            resizable=True, sortable=True, filter=True,
            floatingFilter=True, editable=False,
        )
        gb.configure_pagination(
            paginationAutoPageSize=False, paginationPageSize=page_size
        )
        gb.configure_grid_options(domLayout="normal")
        grid_options = gb.build()
        AgGrid(
            df,
            gridOptions=grid_options,
            height=height,
            theme="alpine-dark",
            fit_columns_on_grid_load=True,
            update_mode=GridUpdateMode.NO_UPDATE,
            allow_unsafe_jscode=True,
            key=key,
        )
    else:
        st.info(
            "💡 Install `streamlit-aggrid` for full sorting/filtering. "
            "Showing the standard interactive table.",
            icon="ℹ️",
        )
        st.dataframe(df, use_container_width=True, height=height, hide_index=True)


def download_button(df: pd.DataFrame, filename: str, label: str | None = None) -> None:
    from utils.i18n import t
    label = label or t("common.download_csv")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label, data=csv, file_name=filename, mime="text/csv",
        use_container_width=False,
    )
