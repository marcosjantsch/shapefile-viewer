from pathlib import Path

import streamlit as st
from PIL import Image


def render_header(
    logo_path: str,
    app_name: str,
    version: str,
    user: str = None,
    role: str = None,
) -> None:
    """
    Header estável sem bloco HTML grande.
    Estrutura:
    [logo] Avant Clima   Análise de Dados Climáticos   V1.4     👤 usuário   🔐 perfil
    """

    # Espaçamento superior para não colar no topo
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    left, center, right = st.columns([3.2, 4.8, 2.0], vertical_alignment="center")

    with left:
        logo_col, text_col = st.columns([1, 6], vertical_alignment="center")

        with logo_col:
            logo_file = Path(logo_path)
            if logo_file.exists():
                try:
                    img = Image.open(logo_file)
                    st.image(img, width=52)
                except Exception:
                    pass

        with text_col:
            st.markdown(
                (
                    f"<div style='display:flex; align-items:center; gap:14px; white-space:nowrap;'>"
                    f"<span style='font-size:28px; font-weight:700;'>{app_name}</span>"
                    f"<span style='font-size:12px; opacity:0.65;'>{version}</span>"
                    f"</div>"
                ),
                unsafe_allow_html=True,
            )

    with center:
        st.markdown(
            (
                "<div style='display:flex; justify-content:center; align-items:center; height:100%;'>"
                "<span style='font-size:22px; font-weight:600; opacity:0.95;'>"
                "Análise de Dados Climáticos"
                "</span>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    with right:
        items = []
        if user:
            items.append(
                f"<span style='padding:4px 10px; border-radius:999px; font-size:11px; "
                f"border:1px solid rgba(255,255,255,0.12); background:rgba(255,255,255,0.06); "
                f"white-space:nowrap;'>👤 {user}</span>"
            )
        if role:
            items.append(
                f"<span style='padding:4px 10px; border-radius:999px; font-size:11px; "
                f"border:1px solid rgba(255,255,255,0.12); background:rgba(255,255,255,0.06); "
                f"white-space:nowrap;'>🔐 {role}</span>"
            )

        st.markdown(
            (
                "<div style='display:flex; justify-content:flex-end; align-items:center; gap:8px; "
                "white-space:nowrap;'>"
                + "".join(items) +
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='margin-top:8px; margin-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.10);'></div>",
        unsafe_allow_html=True,
    )