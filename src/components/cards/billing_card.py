from __future__ import annotations

import streamlit as st

from src.shared.ui import status_badge_html
from src.utils.formatters import format_billing_status, format_currency, format_date


def render_billing_card(record: dict) -> None:
    badge_variant = "success" if record.get("status") == "paid" else "warning"
    st.markdown(
        f"""
        <div class="seg-record-card">
            <div class="seg-record-title">{record.get("descricao", "-")}</div>
            <div style="margin-bottom:0.5rem;">{status_badge_html(format_billing_status(record.get("status")), badge_variant)}</div>
            <div class="seg-record-meta">
                Valor: {format_currency(record.get("valor"))}<br>
                Geracao: {format_date(record.get("data_geracao"))}<br>
                Pagamento: {format_date(record.get("data_pagamento"))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
