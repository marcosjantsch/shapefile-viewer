from __future__ import annotations

import streamlit as st

from src.components.cards.billing_card import render_billing_card
from src.components.cards.common import render_metric_cards
from src.components.forms.billing_form import render_billing_form
from src.services.billing_service import list_billing_records, save_billing_record, simulate_payment
from src.services.company_service import list_companies
from src.shared.ui import render_feedback, render_page_intro


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Billing demo",
        "Area demonstrativa de cobranca, sem transacao financeira real nesta fase.",
        kicker="Modulo 11",
    )
    st.markdown(
        """
        <div class="seg-demo-banner">
            Este modulo e demonstrativo. Nenhuma cobranca real, gateway ou liquidacao financeira e executada nesta versao.
        </div>
        """,
        unsafe_allow_html=True,
    )

    companies = list_companies(current_user)
    company_id = str(current_user.get("company_id"))
    records = list_billing_records(current_user, company_id=company_id)
    pending_count = sum(1 for record in records if record.get("status") == "pending")
    render_metric_cards(
        [
            {"label": "Registros", "value": len(records), "help": "Historico demo da empresa."},
            {"label": "Pendentes", "value": pending_count, "help": "Simulacoes aguardando pagamento."},
            {"label": "Pagos", "value": len(records) - pending_count, "help": "Registros com baixa simulada."},
            {"label": "Integracao real", "value": "Futura", "help": "Arquitetura preparada para evoluir."},
        ]
    )

    left, right = st.columns([0.40, 0.60], gap="large")
    with left:
        submitted, payload = render_billing_form(
            initial_data=None,
            companies=companies,
            form_key="billing-form",
            fixed_company_id=company_id,
        )
        if submitted:
            saved, errors = save_billing_record(current_user, payload)
            if errors:
                render_feedback(errors)
            elif saved:
                st.success("Registro demo salvo com sucesso.")
                st.rerun()

    with right:
        for record in records:
            render_billing_card(record)
            if record.get("status") == "pending":
                if st.button("Simular pagamento", key=f"billing-pay-{record['id']}", use_container_width=True):
                    simulate_payment(current_user, record["id"])
                    st.success("Pagamento simulado com sucesso.")
                    st.rerun()
