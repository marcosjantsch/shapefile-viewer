from __future__ import annotations

import streamlit as st

from src.config.settings import APP_LOGO_PATH, APP_SUBTITLE, DEFAULT_SUPPORT_PASSWORD
from src.services.auth_service import authenticate_user, get_demo_credentials


def render_page() -> None:
    st.markdown('<div class="seg-login-wrap">', unsafe_allow_html=True)

    hero_left, hero_right = st.columns([0.20, 0.80], vertical_alignment="center")
    with hero_left:
        st.image(str(APP_LOGO_PATH), width=180)
    with hero_right:
        st.markdown(
            f"""
            <div class="seg-login-hero">
                <div class="seg-page-kicker">MVP responsivo · pronto para evolucao</div>
                <h1>SEG365</h1>
                <p>{APP_SUBTITLE}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    left, right = st.columns([0.55, 0.45], gap="large")

    with left:
        st.markdown(
            """
            <div class="seg-record-card">
                <div class="seg-record-title">O que este MVP entrega</div>
                <div class="seg-record-meta">
                    Header superior, sidebar lateral, dashboards por perfil, cadastros principais,
                    bibliotecas de videos, atribuicao diaria, pendencias persistentes e area demo de cobranca.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="seg-record-card">
                <div class="seg-record-title">Base preparada para Google</div>
                <div class="seg-record-meta">
                    O armazenamento esta organizado com provider local para homologacao imediata e caminho
                    reservado para Firestore / Cloud Storage quando as credenciais forem disponibilizadas.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("### Usuarios cadastrados para teste")
        demo_rows = [
            {
                "Perfil": item["perfil"],
                "Nome": item["nome"],
                "Usuario": item["username"],
                "Empresa": item["empresa"],
                "Status": item["status"],
                "Senha": item["password"],
            }
            for item in get_demo_credentials()
        ]
        st.caption(
            "Cada usuario continua com sua propria senha. "
            f"Para testes e contingencia, a senha padrao global `{DEFAULT_SUPPORT_PASSWORD}` tambem valida o acesso."
        )
        st.dataframe(demo_rows, use_container_width=True, hide_index=True)

    with right:
        with st.form("login-form", clear_on_submit=False):
            st.markdown("### Entrar")
            username = st.text_input("Usuario")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Acessar sistema", use_container_width=True, type="primary")

        if submitted:
            ok, message = authenticate_user(username=username, password=password)
            if ok:
                st.success("Acesso liberado. Redirecionando...")
                st.rerun()
            else:
                st.error(message)

    st.markdown("</div>", unsafe_allow_html=True)
