from __future__ import annotations

import streamlit as st

from src.shared.ui import status_badge_html


def render_metric_cards(items: list[dict]) -> None:
    if not items:
        return
    columns = st.columns(len(items), gap="medium")
    for column, item in zip(columns, items):
        with column:
            st.markdown(
                f"""
                <div class="seg-metric-card">
                    <small>{item.get("label", "")}</small>
                    <strong>{item.get("value", "-")}</strong>
                    <span>{item.get("help", "")}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_record_summary(
    title: str,
    meta_lines: list[str],
    badges: list[dict] | None = None,
    footer: str = "",
) -> None:
    badge_html = "".join(
        status_badge_html(item.get("label", ""), item.get("variant", "muted")) for item in (badges or [])
    )
    meta_html = "<br>".join(meta_lines)
    footer_html = f"<div class='seg-record-meta' style='margin-top:0.55rem;'>{footer}</div>" if footer else ""
    st.markdown(
        f"""
        <div class="seg-record-card">
            <div class="seg-record-title">{title}</div>
            <div style="display:flex;gap:0.45rem;flex-wrap:wrap;margin-bottom:0.5rem;">{badge_html}</div>
            <div class="seg-record-meta">{meta_html}</div>
            {footer_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
