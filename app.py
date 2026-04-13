# -*- coding: utf-8 -*-
"""
app.py — Avant | Visualizador de Shapefile + Dados Climáticos
Versão V2.1
- Header SaaS
- Logo estável
- Autenticação opcional
- Mapa modularizado
- Geometria original preservada para exibição sem simplificação
- Datas tratadas via services/date_service.py
- Tabs modularizadas
"""

import io
import os
import logging
from datetime import date
from typing import Optional, List

import pandas as pd
import geopandas as gpd
import requests
import streamlit as st

from core.styles import apply_styles
from core.stylesHEADER import apply_stylesHEADER
from config_urls import load_urls, get_url_by_year
from core.settings import (
    APP_TITLE,
    APP_ICON,
    LAYOUT,
    SIDEBAR_STATE,
    GEO_PATH,
    LOGO_PATH,
    AUTH_ENABLED,
    TIPOS_DADO,
)
from components.header import render_header

from services.date_service import parse_date_safe, enrich_date_columns

from tabs.tab_mapa import render_tab_mapa
from tabs.tab_shape import render_tab_shape
from tabs.tab_clima import render_tab_clima
from tabs.tab_analise import render_tab_analise

from tabs.tab_previsao import render_tab_previsao
from tabs.tab_tendencia_climatica import render_tab_tendencia_climatica

# =====================================================================
# LOGGING
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# =====================================================================
# CONFIG
# =====================================================================
SIMPLIFICATION_TOLERANCE = 0.001

MESES_DISPONIVEIS = {
    "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6,
    "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12
}
ANOS_DISPONIVEIS = list(range(2000, 2026))


# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE,
)

apply_styles()
apply_stylesHEADER()


# =====================================================================
# HELPERS
# =====================================================================
@st.cache_data(show_spinner=False)
def load_shapefile_full(file_path: str) -> Optional[gpd.GeoDataFrame]:
    logger.info("Carregando shapefile: %s", file_path)

    if not os.path.exists(file_path):
        logger.warning("Shapefile não encontrado: %s", file_path)
        return None

    try:
        gdf = gpd.read_file(file_path)

        if gdf.empty:
            logger.warning("Shapefile carregado, porém vazio.")
            return gdf

        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")

        if str(gdf.crs).upper() != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        # Guarda geometria original
        gdf["__geometry_original__"] = gdf.geometry.copy()

        try:
            gdf["geometry"] = gdf.geometry.simplify(
                SIMPLIFICATION_TOLERANCE,
                preserve_topology=True,
            )
        except Exception as e:
            logger.warning("Falha na simplificação do shapefile: %s", e)

        return gdf

    except Exception as e:
        logger.error("Erro ao carregar shapefile: %s", e)
        return None


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

    for c in out.columns:
        if out[c].dtype == "object":
            out[c] = out[c].astype(str).str.strip()

    return out


@st.cache_data(show_spinner=False)
def load_csv_from_url_robust(url: str, year: int) -> Optional[pd.DataFrame]:
    try:
        url = str(url).strip().replace("\\", "/")
        is_local_file = os.path.isfile(url)

        if is_local_file:
            with open(url, "rb") as f:
                content = f.read()
        else:
            if "1drv.ms" in url and "download=1" not in url:
                url = url + ("&download=1" if "?" in url else "?download=1")

            response = requests.get(url, timeout=180)
            response.raise_for_status()
            content = response.content

        for enc in ["utf-8", "utf-8-sig", "latin-1", "iso-8859-1", "cp1252"]:
            try:
                text = content.decode(enc)
            except Exception:
                continue

            for sep in [";", ",", "\t", "|"]:
                try:
                    df = pd.read_csv(
                        io.StringIO(text),
                        sep=sep,
                        engine="python",
                        on_bad_lines="skip",
                    )

                    if df is None or df.empty:
                        continue

                    df.columns = [str(c).strip() for c in df.columns]
                    if len(df.columns) <= 1:
                        continue

                    rename_map = {
                        "Data": "DATA",
                        "data": "DATA",
                        "Empresa": "EMPRESA",
                        "Fazenda": "FAZENDA",
                        "Município": "MUNICIPIO",
                        "Municipio": "MUNICIPIO",
                        "AREA_PORDUT": "AREA_PRODU",
                        "AREA_PRODUT": "AREA_PRODU",
                        "AREA_PRODUTIVA": "AREA_PRODU",
                    }
                    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

                    if "DATA" in df.columns:
                        df["DATA"] = parse_date_safe(df["DATA"])

                    logger.info("CSV %s carregado com %d linhas", year, len(df))
                    return df

                except Exception as e:
                    logger.error("Erro ao interpretar CSV do ano %s (enc=%s, sep=%r): %s", year, enc, sep, e)
                    continue

        logger.warning("Falha ao interpretar CSV do ano %s", year)
        return None

    except Exception as e:
        logger.error("Erro ao carregar CSV %s: %s", year, e)
        return None


def get_years_in_range(start_date: date, end_date: date) -> List[int]:
    if start_date is None or end_date is None:
        return []
    if end_date < start_date:
        return []
    return list(range(start_date.year, end_date.year + 1))


def safe_unique(df: pd.DataFrame, col: str) -> List[str]:
    if col not in df.columns:
        return []
    return sorted([str(x) for x in df[col].dropna().unique()])


def filter_gdf(gdf: gpd.GeoDataFrame, filtro: dict) -> gpd.GeoDataFrame:
    gdf_filtered = gdf.copy()
    tipo = filtro["tipo_dado"]

    if tipo == "Dados por Estado" and filtro["selected_uf"] and "UF" in gdf_filtered.columns:
        gdf_filtered = gdf_filtered[gdf_filtered["UF"].astype(str) == str(filtro["selected_uf"])]

    elif tipo == "Dados por Empresa" and filtro["selected_empresa"] and "EMPRESA" in gdf_filtered.columns:
        gdf_filtered = gdf_filtered[gdf_filtered["EMPRESA"].astype(str) == str(filtro["selected_empresa"])]

    elif (
        tipo == "Dados Empresa/Fazenda"
        and filtro["selected_empresa"]
        and filtro["selected_fazenda"]
        and all(c in gdf_filtered.columns for c in ["EMPRESA", "FAZENDA"])
    ):
        gdf_filtered = gdf_filtered[
            (gdf_filtered["EMPRESA"].astype(str) == str(filtro["selected_empresa"])) &
            (gdf_filtered["FAZENDA"].astype(str) == str(filtro["selected_fazenda"]))
        ]

    elif (
        tipo == "Dados por Município"
        and filtro["selected_uf"]
        and filtro["selected_municipio"]
        and all(c in gdf_filtered.columns for c in ["UF", "MUNICIPIO"])
    ):
        gdf_filtered = gdf_filtered[
            (gdf_filtered["UF"].astype(str) == str(filtro["selected_uf"])) &
            (gdf_filtered["MUNICIPIO"].astype(str) == str(filtro["selected_municipio"]))
        ]

    return gdf_filtered


# =====================================================================
# AUTH
# =====================================================================
name = None
username = None
role = None
authentication_status = None
authenticator = None

auth_enabled = AUTH_ENABLED

if auth_enabled:
    try:
        from auth import setup_authentication, get_user_role

        authenticator, name, authentication_status, username = setup_authentication()

        if authentication_status is False:
            st.error("❌ Usuário/senha incorretos")
            st.stop()
        elif authentication_status is None:
            st.warning("⚠️ Informe suas credenciais")
            st.stop()

        try:
            role = get_user_role()
        except Exception:
            role = "Usuário"

    except Exception as e:
        logger.warning("Falha ao carregar autenticação: %s", e)
        auth_enabled = False
        name = "Usuário"
        role = "Sem autenticação"
else:
    name = "Usuário"
    role = "Acesso local"


# =====================================================================
# SESSION STATE
# =====================================================================
if "aplicar" not in st.session_state:
    st.session_state.aplicar = False

if "mostrar_tudo_shape" not in st.session_state:
    st.session_state["mostrar_tudo_shape"] = False

if "mostrar_tudo_clima" not in st.session_state:
    st.session_state["mostrar_tudo_clima"] = False


# =====================================================================
# HEADER
# =====================================================================
render_header(
    logo_path=LOGO_PATH,
    app_name="Avant - Clima",
    version="V2.1",
    user=name,
    role=role,
)


# =====================================================================
# DADOS BASE
# =====================================================================
gdf_full = load_shapefile_full(GEO_PATH)
if gdf_full is None:
    st.error(f"Não foi possível carregar o shapefile em: {GEO_PATH}")
    st.stop()


# =====================================================================
# SIDEBAR
# =====================================================================
tipo_dado = st.sidebar.selectbox("Tipo de Dado", TIPOS_DADO)

selected_uf = None
selected_empresa = None
selected_fazenda = None
selected_municipio = None

if tipo_dado == "Dados por Estado":
    ufs = safe_unique(gdf_full, "UF")
    selected_uf = st.sidebar.selectbox("Selecione UF", ufs) if ufs else None

elif tipo_dado == "Dados por Empresa":
    empresas = safe_unique(gdf_full, "EMPRESA")
    selected_empresa = st.sidebar.selectbox("Selecione Empresa", empresas) if empresas else None

elif tipo_dado == "Dados Empresa/Fazenda":
    empresas = safe_unique(gdf_full, "EMPRESA")
    selected_empresa = st.sidebar.selectbox("Selecione Empresa", empresas) if empresas else None

    if selected_empresa and "FAZENDA" in gdf_full.columns and "EMPRESA" in gdf_full.columns:
        fazendas = safe_unique(
            gdf_full[gdf_full["EMPRESA"].astype(str) == str(selected_empresa)],
            "FAZENDA",
        )
        selected_fazenda = st.sidebar.selectbox("Selecione Fazenda", fazendas) if fazendas else None

elif tipo_dado == "Dados por Município":
    ufs = safe_unique(gdf_full, "UF")
    selected_uf = st.sidebar.selectbox("Selecione UF", ufs) if ufs else None

    if selected_uf and "MUNICIPIO" in gdf_full.columns and "UF" in gdf_full.columns:
        municipios = safe_unique(
            gdf_full[gdf_full["UF"].astype(str) == str(selected_uf)],
            "MUNICIPIO",
        )
        selected_municipio = st.sidebar.selectbox("Selecione Município", municipios) if municipios else None

st.sidebar.markdown("---")
st.sidebar.subheader("Período mensal")

col1, col2 = st.sidebar.columns(2)
with col1:
    start_mes_nome = st.selectbox("Mês inicial", list(MESES_DISPONIVEIS.keys()), index=0)
with col2:
    start_ano = st.selectbox("Ano inicial", ANOS_DISPONIVEIS, index=ANOS_DISPONIVEIS.index(2025))

col3, col4 = st.sidebar.columns(2)
with col3:
    end_mes_nome = st.selectbox("Mês final", list(MESES_DISPONIVEIS.keys()), index=11)
with col4:
    end_ano = st.selectbox("Ano final", ANOS_DISPONIVEIS, index=ANOS_DISPONIVEIS.index(2025))

start_date = date(start_ano, MESES_DISPONIVEIS[start_mes_nome], 1)
end_date = date(end_ano, MESES_DISPONIVEIS[end_mes_nome], 1)

apply = st.sidebar.button("✅ Aplicar Filtros")
log_container = st.sidebar.container() if apply else st.sidebar.empty()

if apply:
    st.session_state.aplicar = True
    st.session_state["mostrar_tudo_shape"] = False
    st.session_state["mostrar_tudo_clima"] = False


# =====================================================================
# FILTRO SHAPE
# =====================================================================
filtro = {
    "tipo_dado": tipo_dado,
    "selected_uf": selected_uf,
    "selected_empresa": selected_empresa,
    "selected_fazenda": selected_fazenda,
    "selected_municipio": selected_municipio,
}

gdf_filtered = gdf_full.copy()
if st.session_state.aplicar:
    gdf_filtered = filter_gdf(gdf_full, filtro)


# =====================================================================
# LOAD CSV
# =====================================================================
df_csv = pd.DataFrame()

if st.session_state.get("aplicar", False):
    try:
        urls = load_urls()
        years = get_years_in_range(start_date, end_date)

        if years:
            with st.spinner(f"Carregando dados climáticos ({', '.join(map(str, years))})..."):
                frames = []

                for y in years:
                    try:
                        url = get_url_by_year(urls, y)

                        if not url:
                            log_container.warning(f"⚠️ Sem URL para o ano {y}")
                            continue

                        df_y = load_csv_from_url_robust(url, y)

                        if df_y is None or df_y.empty:
                            log_container.warning(f"⚠️ Ano {y} sem dados válidos")
                            continue

                        frames.append(df_y)
                        log_container.success(f"✅ {y}: carregado")

                    except Exception as e:
                        logger.error("Erro ao ler CSV ano %s: %s", y, e)
                        log_container.error(f"❌ Erro ao ler CSV do ano {y}: {e}")

                if frames:
                    df_csv = pd.concat(frames, ignore_index=True)

        if df_csv is not None and not df_csv.empty:
            df_csv = _normalize_columns(df_csv)

            if "DATA" in df_csv.columns:
                df_csv = enrich_date_columns(df_csv, "DATA")

                start_period = pd.Period(start_date, freq="M")
                end_period = pd.Period(end_date, freq="M")

                df_csv["MES_ANO_PERIODO"] = df_csv["DATA"].dt.to_period("M")
                df_csv = df_csv[
                    (df_csv["MES_ANO_PERIODO"] >= start_period) &
                    (df_csv["MES_ANO_PERIODO"] <= end_period)
                ].copy()
                df_csv.drop(columns=["MES_ANO_PERIODO"], inplace=True, errors="ignore")

            if tipo_dado == "Dados por Estado" and selected_uf and "UF" in df_csv.columns:
                df_csv = df_csv[df_csv["UF"].astype(str) == str(selected_uf)]

            elif tipo_dado == "Dados por Empresa" and selected_empresa and "EMPRESA" in df_csv.columns:
                df_csv = df_csv[df_csv["EMPRESA"].astype(str) == str(selected_empresa)]

            elif (
                tipo_dado == "Dados Empresa/Fazenda"
                and selected_empresa and selected_fazenda
                and all(c in df_csv.columns for c in ["EMPRESA", "FAZENDA"])
            ):
                df_csv = df_csv[
                    (df_csv["EMPRESA"].astype(str) == str(selected_empresa)) &
                    (df_csv["FAZENDA"].astype(str) == str(selected_fazenda))
                ]

            elif (
                tipo_dado == "Dados por Município"
                and selected_uf and selected_municipio
                and all(c in df_csv.columns for c in ["UF", "MUNICIPIO"])
            ):
                df_csv = df_csv[
                    (df_csv["UF"].astype(str) == str(selected_uf)) &
                    (df_csv["MUNICIPIO"].astype(str) == str(selected_municipio))
                ]

            log_container.info(f"📦 Total final: {len(df_csv)} registros")
        else:
            log_container.warning("⚠️ Nenhum registro carregado.")

    except Exception as e:
        logger.error("Erro no carregamento dos CSVs: %s", e)
        log_container.error(f"❌ Erro geral no carregamento: {e}")


# =====================================================================
# TABS
# =====================================================================
tab1, tab2, tab3, tab4, tab5,tab6  = st.tabs(
    ["🗺️ Mapa Principal", "📋 Dados Shape", "📈 Dados de Clima", "📉 Análise Avançada", "Previsão do Tempo", "Tendência Climática"]
)

with tab1:
    render_tab_mapa(gdf_full, gdf_filtered, filtro)

with tab2:
    render_tab_shape(gdf_filtered)

with tab3:
    # MArcos st.write(df_csv[["EMPRESA", "FAZENDA", "DATA", "AREA_T", "AREA_PRODU"]].head(20))
    render_tab_clima(df_csv)

with tab4:
    render_tab_analise(
        df_csv,
        tipo_dado=tipo_dado,
        selected_uf=selected_uf,
        selected_municipio=selected_municipio,
        selected_empresa=selected_empresa,
        selected_fazenda=selected_fazenda,
        start_date=start_date,
        end_date=end_date,
    )

with tab5:
    render_tab_previsao(
        gdf_filtered=gdf_filtered,
        selected_empresa=selected_empresa,
        selected_fazenda=selected_fazenda,
        selected_municipio=selected_municipio,
        selected_uf=selected_uf,
        logo_path=LOGO_PATH,
    )    

with tab6:
    render_tab_tendencia_climatica(
        gdf_filtered=gdf_filtered,
        selected_empresa=selected_empresa,
        selected_fazenda=selected_fazenda,
        selected_municipio=selected_municipio,
        selected_uf=selected_uf,
        logo_path=LOGO_PATH,
    )