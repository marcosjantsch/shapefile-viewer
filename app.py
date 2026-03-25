

# -*- coding: utf-8 -*-
"""
app.py — Avant | Visualizador de Shapefile + Dados Climáticos
VERSÃO CORRIGIDA COM DIAGNÓSTICO DE DADOS
"""

import os
import io
import logging
from datetime import date
from typing import Optional, List, Dict

import io
import glob

import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import requests
import streamlit as st
import plotly.express as px





# =====================================================================
# LOGGING
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)

# =====================================================================
# STREAMLIT CONFIG
# =====================================================================
st.set_page_config(
    page_title="Visualizador de Shapefile e Dados Climáticos",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# CSS COMPLETO
# =====================================================================
st.markdown("""
<style>

/* AJUSTE GLOBAL DA PÁGINA */
.block-container {
    padding-top: 0.05rem !important;
    padding-bottom: 1rem !important;
}

header[data-testid="stHeader"] {
    height: 0rem !important;
}

section.main > div {
    padding-top: 0rem !important;
}

/* TÍTULO PRINCIPAL */
.main-title {
    font-size: 24px !important;
    font-weight: 600;
    margin-top: -12px !important;
    margin-bottom: 8px !important;
}

/* TÍTULOS DE SEÇÃO */
.section-title {
    font-size: 14px !important;
    font-weight: 600;
    margin-top: 2px !important;
    margin-bottom: 6px !important;
    opacity: 0.95;
}

/* USERBAR (Topo Direito) */
.userbar {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    margin-top: -8px;
    margin-bottom: 4px;
    white-space: nowrap;
}

.userbar .pill {
    padding: 2px 8px;
    border: 1px solid rgba(49,51,63,0.25);
    border-radius: 999px;
    background-color: rgba(240,240,240,0.6);
}

/* BOTÕES */
div[data-testid="stButton"] > button {
    padding: 0.2rem 0.5rem !important;
    font-size: 11px !important;
    height: 28px !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    padding-top: 0.3rem !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 0.3rem !important;
    padding-bottom: 0.3rem !important;
}

section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {
    margin-bottom: 0.18rem !important;
}

section[data-testid="stSidebar"] label {
    margin-bottom: 1px !important;
    font-size: 12px !important;
}

section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stDateInput,
section[data-testid="stSidebar"] .stTextInput,
section[data-testid="stSidebar"] .stNumberInput,
section[data-testid="stSidebar"] .stMultiselect {
    margin-bottom: 0.15rem !important;
}

section[data-testid="stSidebar"] h1 {
    font-size: 18px !important;
    margin-bottom: 0.3rem !important;
}

section[data-testid="stSidebar"] hr {
    margin: 0.4rem 0 !important;
}

/* TABS */
button[role="tab"] {
    font-size: 13px !important;
    padding: 6px 10px !important;
}

/* METRICS */
div[data-testid="stMetric"] {
    padding: 6px !important;
}

</style>
""", unsafe_allow_html=True)

# =====================================================================
# IMPORTS DO PROJETO
# =====================================================================
from config_urls import load_urls, get_url_by_year  # noqa: E402

# Autenticação opcional
AUTH_ENABLED = os.path.exists("config.yaml")
if AUTH_ENABLED:
    try:
        from auth import setup_authentication, get_user_role  # noqa: E402
    except Exception as e:
        AUTH_ENABLED = False
        logger.warning("Falha ao importar auth.py, desativando autenticação: %s", e)

# =====================================================================
# CONSTANTES
# =====================================================================
GEO_PATH =  "Geo.shp"
SIMPLIFICATION_TOLERANCE = 0.001
MAX_FEATURES_FULL_MAP = 5000

# =====================================================================
# HELPERS
# =====================================================================
@st.cache_data(show_spinner=False)
def load_shapefile_full(file_path: str) -> Optional[gpd.GeoDataFrame]:
    """Carrega shapefile com reprojeção e simplificação."""
    logger.info("Carregando shapefile: %s", file_path)
    if not os.path.exists(file_path):
        return None

    try:
        gdf = gpd.read_file(file_path)
        if gdf.empty:
            return gdf

        if gdf.crs is None:
            logger.warning("Shapefile sem CRS. Assumindo EPSG:4326.")
            gdf = gdf.set_crs("EPSG:4326")

        if str(gdf.crs).upper() != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        try:
            gdf["geometry"] = gdf.geometry.simplify(SIMPLIFICATION_TOLERANCE, preserve_topology=True)
        except Exception as e:
            logger.warning("Falha na simplificação: %s", e)

        logger.info("Shapefile carregado com sucesso: %d feições", len(gdf))
        return gdf
    except Exception as e:
        logger.error("Erro ao carregar shapefile: %s", e)
        return None


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nomes de colunas e remove espaços."""
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    for c in out.columns:
        if out[c].dtype == "object":
            out[c] = out[c].astype(str).str.strip()
    return out


@st.cache_data(show_spinner=False)
def load_csv_from_url_robust(url: str, year: int) -> Optional[pd.DataFrame]:
    try:
        logger.info("DEBUG >>> ENTROU NA FUNÇÃO load_csv_from_url_robust")
        logger.info(f"DEBUG caminho recebido: {url}")

        url = str(url).strip().replace("\\", "/")
        is_local_file = os.path.isfile(url)

        logger.info(f"DEBUG isfile: {is_local_file}")

        if is_local_file:
            logger.info("DEBUG >>> LENDO COMO ARQUIVO LOCAL")
            with open(url, "rb") as f:
                content = f.read()
        else:
            logger.info("DEBUG >>> LENDO COMO URL WEB")

            if "1drv.ms" in url and "download=1" not in url:
                url = url + ("&download=1" if "?" in url else "?download=1")

            response = requests.get(url, timeout=180)
            response.raise_for_status()
            content = response.content

        logger.info(f"DEBUG tamanho do arquivo (bytes): {len(content)}")

        for enc in ["utf-8", "utf-8-sig", "latin-1", "iso-8859-1", "cp1252"]:
            try:
                text = content.decode(enc)
                logger.info(f"DEBUG encoding OK: {enc}")
            except Exception:
                logger.info(f"DEBUG encoding falhou: {enc}")
                continue

            logger.info(f"DEBUG primeiras 300 chars:\n{text[:300]}")

            for sep in [";", ",", "\t", "|"]:
                try:
                    df = pd.read_csv(
                        io.StringIO(text),
                        sep=sep,
                        engine="python",
                        on_bad_lines="skip"
                    )

                    logger.info(
                        f"DEBUG tentativa sep='{sep}' -> linhas={len(df)} cols={len(df.columns)} colunas={list(df.columns)[:10]}"
                    )
                    logger.info(f"DEBUG head sep='{sep}':\n{df.head(3).to_string()}")

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
                    }

                    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

                    if "DATA" in df.columns:
                        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce", dayfirst=True)

                    logger.info(f"✅ CSV {year} carregado: {len(df)} linhas e {len(df.columns)} colunas")
                    return df

                except Exception as e:
                    logger.info(f"DEBUG sep='{sep}' falhou: {e}")
                    continue

        logger.warning(f"⚠️ Falha ao interpretar CSV do ano {year}")
        return None

    except Exception as e:
        logger.error(f"❌ Erro ao carregar CSV {year}: {e}")
        return None





def generate_fictitious_csv_data(year):
    """Gera dados CSV fictícios para um ano específico com todas as colunas necessárias."""
    num_entries = 100
    
    ufs = ['SP', 'MG', 'PR', 'BA', 'GO']
    empresas = ['AgroTech', 'Fazenda Verde', 'Colheita Feliz']
    fazendas = ['Fazenda A', 'Fazenda B', 'Fazenda C', 'Fazenda D']
    municipios = ['Cidade X', 'Cidade Y', 'Cidade Z', 'Cidade W']

    data = {
        'UF': np.random.choice(ufs, num_entries),
        'EMPRESA': np.random.choice(empresas, num_entries),
        'FAZENDA': np.random.choice(fazendas, num_entries),
        'MUNICIPIO': np.random.choice(municipios, num_entries),
        'DATA': [date(year, np.random.randint(1, 13), np.random.randint(1, 29)) for _ in range(num_entries)],
        'PRECIP_CHIRPS_MM': np.random.uniform(0, 200, num_entries),
        'AREA_PRODU': np.random.uniform(100, 1000, num_entries),
        'AREA_T': np.random.uniform(150, 1200, num_entries),
        'TEMP_MEDIA_C': np.random.uniform(18, 30, num_entries),
        'TEMP_MIN_C': np.random.uniform(10, 25, num_entries),
        'TEMP_MAX_C': np.random.uniform(25, 40, num_entries),
        'AMPLITUDE_TERMICA_C': np.random.uniform(5, 15, num_entries),
        'UMID_MEDIA_PCT': np.random.uniform(50, 90, num_entries),
        'UMID_MIN_PCT': np.random.uniform(30, 70, num_entries),
        'INDICE_RISCO_INCENDIO': np.random.uniform(0, 100, num_entries),
        'DEFICIT_HIDRICO_MM': np.random.uniform(0, 50, num_entries),
        'INDICE_SECA': np.random.uniform(0, 5, num_entries),
        'RISCO_ESTRESSE_HIDRICO': np.random.uniform(0, 1, num_entries),
        'NOITES_FRIAS_Eucalipto_<15C': np.random.randint(0, 10, num_entries),
        'NOITES_FRIAS_Pinus_<5C': np.random.randint(0, 5, num_entries),
        'ONDAS_CALOR_Eucalipto_>35C': np.random.randint(0, 7, num_entries),
        'DIAS_SEM_CHUVA': np.random.randint(0, 30, num_entries),
    }
    df = pd.DataFrame(data)
    df['DATA'] = pd.to_datetime(df['DATA'])
    
    # Garante que cada fazenda tenha a mesma AREA_PRODU e AREA_T
    for fazenda in df['FAZENDA'].unique():
        area_produ_value = df[df['FAZENDA'] == fazenda]['AREA_PRODU'].iloc[0]
        area_t_value = df[df['FAZENDA'] == fazenda]['AREA_T'].iloc[0]
        df.loc[df['FAZENDA'] == fazenda, 'AREA_PRODU'] = area_produ_value
        df.loc[df['FAZENDA'] == fazenda, 'AREA_T'] = area_t_value
    
    logger.info(f"Dados fictícios gerados para {year}: {len(df)} registros, {len(df.columns)} colunas")
    return df


def get_years_in_range(start_date: date, end_date: date) -> List[int]:
    """Retorna lista de anos entre duas datas."""
    if start_date is None or end_date is None:
        return []
    if end_date < start_date:
        return []
    return list(range(start_date.year, end_date.year + 1))


def to_numeric_safe(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Converte colunas para numérico com segurança."""
    d = df.copy()
    for c in cols:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Calcula média ponderada."""
    v = pd.to_numeric(values, errors="coerce")
    w = pd.to_numeric(weights, errors="coerce")
    m = v.notna() & w.notna() & (w > 0)
    if m.sum() == 0:
        return float("nan")
    return float((v[m] * w[m]).sum() / w[m].sum())


def generate_map_full_optimized(gdf_to_display: gpd.GeoDataFrame, tipo_exibicao: str) -> folium.Map:
    """Gera mapa Folium otimizado."""
    if gdf_to_display is None or gdf_to_display.empty:
        return folium.Map(location=[-15.0, -55.0], zoom_start=4)

    if len(gdf_to_display) > MAX_FEATURES_FULL_MAP:
        st.warning(f"⚠️ Muitas feições ({len(gdf_to_display)}). Renderizando apenas {MAX_FEATURES_FULL_MAP}.")
        gdf_to_display = gdf_to_display.head(MAX_FEATURES_FULL_MAP)

    m = folium.Map()
    bounds = gdf_to_display.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    color_map = {
        "Todos os Dados": "#FF4500",
        "Dados por Estado": "#FF1493",
        "Dados por Empresa": "#4B0082",
        "Dados Empresa/Fazenda": "#8B008B",
        "Dados por Município": "#FF8C00",
    }
    color = color_map.get(tipo_exibicao, "blue")

    fields = [c for c in ["UF", "MUNICIPIO", "EMPRESA", "FAZENDA"] if c in gdf_to_display.columns]
    aliases_map = {"UF": "UF", "MUNICIPIO": "Município", "EMPRESA": "Empresa", "FAZENDA": "Fazenda"}
    aliases = [aliases_map.get(c, c) for c in fields]

    try:
        folium.GeoJson(
            gdf_to_display.to_json(),
            style_function=lambda x: {"fillColor": color, "color": color, "weight": 1, "fillOpacity": 0.55},
            tooltip=folium.features.GeoJsonTooltip(fields=fields, aliases=aliases, sticky=False),
        ).add_to(m)
    except Exception as e:
        logger.warning("Erro ao renderizar GeoJson: %s. Usando fallback.", e)
        for _, row in gdf_to_display.iterrows():
            popup_text = (
                f"<b>UF:</b> {row.get('UF', 'N/A')}<br>"
                f"<b>Município:</b> {row.get('MUNICIPIO', 'N/A')}<br>"
                f"<b>Empresa:</b> {row.get('EMPRESA', 'N/A')}<br>"
                f"<b>Fazenda:</b> {row.get('FAZENDA', 'N/A')}"
            )
            folium.GeoJson(
                row.geometry,
                style_function=lambda x: {"fillColor": color, "color": color, "weight": 1, "fillOpacity": 0.55},
                popup=folium.Popup(popup_text, max_width=320),
                tooltip=f"{row.get('UF', 'N/A')} - {row.get('FAZENDA', 'N/A')}",
            ).add_to(m)

    return m


def resumo_por_fazenda(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Gera resumo por fazenda com TODAS as colunas solicitadas."""
    logger.info(f"[resumo_por_fazenda] Entrada: {len(df)} linhas, colunas: {list(df.columns)}")
    
    if df is None or df.empty:
        logger.warning("[resumo_por_fazenda] DataFrame vazio!")
        return None
    
    if "FAZENDA" not in df.columns:
        logger.warning("[resumo_por_fazenda] Coluna FAZENDA não encontrada!")
        return None

    df2 = df.copy()
    
    # Converter para numérico
    numeric_cols = [
        "AREA_PRODU", "AREA_T", "PRECIP_CHIRPS_MM", "TEMP_MEDIA_C", "TEMP_MIN_C", "TEMP_MAX_C",
        "AMPLITUDE_TERMICA_C", "UMID_MIN_PCT", "DIAS_SEM_CHUVA", "DEFICIT_HIDRICO_MM", "INDICE_SECA",
        "RISCO_ESTRESSE_HIDRICO", "NOITES_FRIAS_Eucalipto_<15C", "NOITES_FRIAS_Pinus_<5C",
        "ONDAS_CALOR_Eucalipto_>35C", "UMID_MEDIA_PCT", "INDICE_RISCO_INCENDIO"
    ]
    
    for col in numeric_cols:
        if col in df2.columns:
            df2[col] = pd.to_numeric(df2[col], errors="coerce")
    
    logger.info(f"[resumo_por_fazenda] Após conversão numérica: {len(df2)} linhas")
    
    # Construir agregações dinamicamente
    agg_dict = {}
    
    if "AREA_PRODU" in df2.columns:
        agg_dict["AREA_PRODU"] = "first"
    if "AREA_T" in df2.columns:
        agg_dict["AREA_T"] = "first"
    if "PRECIP_CHIRPS_MM" in df2.columns:
        agg_dict["PRECIP_CHIRPS_MM"] = "sum"
    if "TEMP_MEDIA_C" in df2.columns:
        agg_dict["TEMP_MEDIA_C"] = "mean"
    if "TEMP_MIN_C" in df2.columns:
        agg_dict["TEMP_MIN_C"] = "min"
    if "TEMP_MAX_C" in df2.columns:
        agg_dict["TEMP_MAX_C"] = "max"
    if "AMPLITUDE_TERMICA_C" in df2.columns:
        agg_dict["AMPLITUDE_TERMICA_C"] = "mean"
    if "UMID_MIN_PCT" in df2.columns:
        agg_dict["UMID_MIN_PCT"] = "mean"
    if "DIAS_SEM_CHUVA" in df2.columns:
        agg_dict["DIAS_SEM_CHUVA"] = "max"
    if "DEFICIT_HIDRICO_MM" in df2.columns:
        agg_dict["DEFICIT_HIDRICO_MM"] = "sum"
    if "INDICE_SECA" in df2.columns:
        agg_dict["INDICE_SECA"] = "sum"
    if "RISCO_ESTRESSE_HIDRICO" in df2.columns:
        agg_dict["RISCO_ESTRESSE_HIDRICO"] = "mean"
    if "NOITES_FRIAS_Eucalipto_<15C" in df2.columns:
        agg_dict["NOITES_FRIAS_Eucalipto_<15C"] = "sum"
    if "NOITES_FRIAS_Pinus_<5C" in df2.columns:
        agg_dict["NOITES_FRIAS_Pinus_<5C"] = "sum"
    if "ONDAS_CALOR_Eucalipto_>35C" in df2.columns:
        agg_dict["ONDAS_CALOR_Eucalipto_>35C"] = "sum"
    if "UMID_MEDIA_PCT" in df2.columns:
        agg_dict["UMID_MEDIA_PCT"] = "mean"
    if "INDICE_RISCO_INCENDIO" in df2.columns:
        agg_dict["INDICE_RISCO_INCENDIO"] = "max"
    
    logger.info(f"[resumo_por_fazenda] Agregações: {list(agg_dict.keys())}")
    
    if not agg_dict:
        logger.warning("[resumo_por_fazenda] Nenhuma coluna para agregar!")
        return None

    try:
        res = df2.groupby("FAZENDA", dropna=False).agg(agg_dict).round(2)
        logger.info(f"[resumo_por_fazenda] Após agrupamento: {len(res)} fazendas")
        
        # Renomear colunas
        rename_map = {
            "PRECIP_CHIRPS_MM": "Soma Precipitação (mm)",
            "TEMP_MEDIA_C": "Média Temp (°C)",
            "TEMP_MIN_C": "Menor Temp Min (°C)",
            "TEMP_MAX_C": "Maior Temp Max (°C)",
            "AMPLITUDE_TERMICA_C": "Média Amplitude Térmica (°C)",
            "UMID_MIN_PCT": "Média Umidade Min (%)",
            "DIAS_SEM_CHUVA": "Máximo Dias Sem Chuva",
            "DEFICIT_HIDRICO_MM": "Soma Déficit Hídrico (mm)",
            "INDICE_SECA": "Soma Índice Seca",
            "RISCO_ESTRESSE_HIDRICO": "Média Risco Estresse Hídrico",
            "NOITES_FRIAS_Eucalipto_<15C": "Soma Noites Frias Eucalipto (<15C)",
            "NOITES_FRIAS_Pinus_<5C": "Soma Noites Frias Pinus (<5C)",
            "ONDAS_CALOR_Eucalipto_>35C": "Soma Ondas de Calor (>35C)",
            "UMID_MEDIA_PCT": "Média Umidade (%)",
            "INDICE_RISCO_INCENDIO": "Máximo Risco Incêndio",
        }
        
        res = res.rename(columns=rename_map)
        
        # Ordenar colunas
        order = [
            c for c in [
                "AREA_PRODU", "AREA_T", "Soma Precipitação (mm)", "Média Temp (°C)",
                "Menor Temp Min (°C)", "Maior Temp Max (°C)", "Média Amplitude Térmica (°C)",
                "Média Umidade Min (%)", "Máximo Dias Sem Chuva", "Soma Déficit Hídrico (mm)",
                "Soma Índice Seca", "Média Risco Estresse Hídrico",
                "Soma Noites Frias Eucalipto (<15C)", "Soma Noites Frias Pinus (<5C)",
                "Soma Ondas de Calor (>35C)", "Média Umidade (%)", "Máximo Risco Incêndio"
            ]
            if c in res.columns
        ]
        
        res_final = res[order]
        logger.info(f"[resumo_por_fazenda] Resultado final: {len(res_final)} fazendas, {len(res_final.columns)} colunas")
        return res_final
        
    except Exception as e:
        logger.error(f"[resumo_por_fazenda] Erro ao agrupar: {e}")
        return None


def metricas_agregadas_casoB(df: pd.DataFrame) -> Dict:
    """Calcula métricas agregadas (Caso B) com TODAS as colunas solicitadas."""
    logger.info(f"[metricas_agregadas_casoB] Entrada: {len(df)} linhas")
    
    out = {
        "precip_wp": np.nan,
        "temp_mean": np.nan,
        "umid_mean": np.nan,
        "indice_risco_incendio_max": np.nan,
        "deficit_hidrico_soma": np.nan,
        "indice_seca_soma": np.nan,
        "risco_estresse_hidrico_media": np.nan,
        "noites_frias_eucalipto_soma": np.nan,
        "noites_frias_pinus_soma": np.nan,
        "serie_dias_sem_chuva_wp": pd.DataFrame(),
        "serie_indice_risco_incendio": pd.DataFrame(),
        "serie_risco_estresse_hidrico": pd.DataFrame(),
    }
    df2 = df.copy()

    if "DATA" in df2.columns:
        df2["DATA"] = pd.to_datetime(df2["DATA"], errors="coerce")

    df2 = to_numeric_safe(df2, [
        "AREA_PRODU", "PRECIP_CHIRPS_MM", "TEMP_MEDIA_C", "UMID_MEDIA_PCT", "DIAS_SEM_CHUVA",
        "INDICE_RISCO_INCENDIO", "DEFICIT_HIDRICO_MM", "INDICE_SECA", "RISCO_ESTRESSE_HIDRICO",
        "NOITES_FRIAS_Eucalipto_<15C", "NOITES_FRIAS_Pinus_<5C"
    ])

    # Métricas simples
    if "TEMP_MEDIA_C" in df2.columns:
        out["temp_mean"] = float(df2["TEMP_MEDIA_C"].mean(skipna=True))
    if "UMID_MEDIA_PCT" in df2.columns:
        out["umid_mean"] = float(df2["UMID_MEDIA_PCT"].mean(skipna=True))
    if "INDICE_RISCO_INCENDIO" in df2.columns:
        out["indice_risco_incendio_max"] = float(df2["INDICE_RISCO_INCENDIO"].max(skipna=True))
    if "DEFICIT_HIDRICO_MM" in df2.columns:
        out["deficit_hidrico_soma"] = float(df2["DEFICIT_HIDRICO_MM"].sum(skipna=True))
    if "INDICE_SECA" in df2.columns:
        out["indice_seca_soma"] = float(df2["INDICE_SECA"].sum(skipna=True))
    if "RISCO_ESTRESSE_HIDRICO" in df2.columns:
        out["risco_estresse_hidrico_media"] = float(df2["RISCO_ESTRESSE_HIDRICO"].mean(skipna=True))
    if "NOITES_FRIAS_Eucalipto_<15C" in df2.columns:
        out["noites_frias_eucalipto_soma"] = float(df2["NOITES_FRIAS_Eucalipto_<15C"].sum(skipna=True))
    if "NOITES_FRIAS_Pinus_<5C" in df2.columns:
        out["noites_frias_pinus_soma"] = float(df2["NOITES_FRIAS_Pinus_<5C"].sum(skipna=True))

    # Precip ponderada por área
    if all(c in df2.columns for c in ["FAZENDA", "AREA_PRODU", "PRECIP_CHIRPS_MM"]):
        areas = df2.groupby("FAZENDA")["AREA_PRODU"].first()
        p_sum = df2.groupby("FAZENDA")["PRECIP_CHIRPS_MM"].sum(min_count=1)
        tmp = pd.concat([areas.rename("A"), p_sum.rename("P")], axis=1).dropna()
        tmp = tmp[tmp["A"] > 0]
        if not tmp.empty:
            out["precip_wp"] = float((tmp["P"] * tmp["A"]).sum() / tmp["A"].sum())

    # Série dias sem chuva ponderada
    if all(c in df2.columns for c in ["DATA", "DIAS_SEM_CHUVA", "FAZENDA", "AREA_PRODU"]):
        d3 = df2.dropna(subset=["DATA", "FAZENDA"]).copy()
        area_map = d3.groupby("FAZENDA")["AREA_PRODU"].first()
        d3["PESO_AREA"] = d3["FAZENDA"].map(area_map)
        d3 = d3.dropna(subset=["PESO_AREA"])
        d3 = d3[d3["PESO_AREA"] > 0]
        if not d3.empty:
            s = (
                d3.groupby(d3["DATA"].dt.date)
                .apply(lambda g: weighted_mean(g["DIAS_SEM_CHUVA"], g["PESO_AREA"]))
                .reset_index(name="DIAS_SEM_CHUVA_MEDIA_PONDERADA")
            )
            s["DATA"] = pd.to_datetime(s["DATA"])
            out["serie_dias_sem_chuva_wp"] = s.sort_values("DATA")

    # Série Índice de Risco de Incêndio
    if all(c in df2.columns for c in ["DATA", "INDICE_RISCO_INCENDIO"]):
        d4 = df2.dropna(subset=["DATA", "INDICE_RISCO_INCENDIO"]).copy()
        d4["DATA"] = pd.to_datetime(d4["DATA"])
        s2 = d4.groupby(d4["DATA"].dt.date)["INDICE_RISCO_INCENDIO"].mean().reset_index(name="INDICE_RISCO_INCENDIO_MEDIA")
        s2["DATA"] = pd.to_datetime(s2["DATA"])
        out["serie_indice_risco_incendio"] = s2.sort_values("DATA")

    # Série Risco de Estresse Hídrico
    if all(c in df2.columns for c in ["DATA", "RISCO_ESTRESSE_HIDRICO"]):
        d5 = df2.dropna(subset=["DATA", "RISCO_ESTRESSE_HIDRICO"]).copy()
        d5["DATA"] = pd.to_datetime(d5["DATA"])
        s3 = d5.groupby(d5["DATA"].dt.date)["RISCO_ESTRESSE_HIDRICO"].mean().reset_index(name="RISCO_ESTRESSE_HIDRICO_MEDIA")
        s3["DATA"] = pd.to_datetime(s3["DATA"])
        out["serie_risco_estresse_hidrico"] = s3.sort_values("DATA")

    logger.info(f"[metricas_agregadas_casoB] Métricas calculadas")
    return out


def add_logo_sidebar():
    """Exibe logo na sidebar."""
    logo_path = "Logo.tif"
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=100)
    else:
        st.sidebar.caption("Logo.tif não encontrado (opcional).")


def render_logout_in_main(authenticator) -> None:
    """Compatibilidade entre versões do streamlit-authenticator."""
    try:
        authenticator.logout(location="main")
    except TypeError:
        authenticator.logout("Logout", "main")


# =====================================================================
# AUTENTICAÇÃO (OPCIONAL)
# =====================================================================
name = None
username = None
authentication_status = None
authenticator = None

if AUTH_ENABLED:
    authenticator, name, authentication_status, username = setup_authentication()

    if authentication_status is False:
        st.error("❌ Usuário/senha incorretos")
        st.stop()
    elif authentication_status is None:
        st.warning("⚠️ Informe suas credenciais")
        st.stop()
else:
    st.sidebar.info("Autenticação desativada (crie config.yaml para ativar).")

# =====================================================================
# SIDEBAR
# =====================================================================
add_logo_sidebar()
st.sidebar.title("Avant - Clima")
st.sidebar.title("V1.3")
st.sidebar.markdown("---")

gdf_full = load_shapefile_full(GEO_PATH)
if gdf_full is None:
    st.error(f"Não foi possível carregar o shapefile em: {GEO_PATH}")
    st.info("Coloque Geo.shp + .shx/.dbf/.prj dentro de Shape/.")
    st.stop()

tipo_dado = st.sidebar.selectbox(
    "Tipo de Dado",
    ["Todos os Dados", "Dados por Estado", "Dados por Empresa", "Dados Empresa/Fazenda", "Dados por Município"],
)

selected_uf = selected_empresa = selected_fazenda = selected_municipio = None


def safe_unique(gdf: gpd.GeoDataFrame, col: str) -> List[str]:
    """Retorna valores únicos de uma coluna com segurança."""
    if col not in gdf.columns:
        return []
    return sorted([str(x) for x in gdf[col].dropna().unique()])


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
        fazendas = safe_unique(gdf_full[gdf_full["EMPRESA"].astype(str) == str(selected_empresa)], "FAZENDA")
        selected_fazenda = st.sidebar.selectbox("Selecione Fazenda", fazendas) if fazendas else None

elif tipo_dado == "Dados por Município":
    ufs = safe_unique(gdf_full, "UF")
    selected_uf = st.sidebar.selectbox("Selecione UF", ufs) if ufs else None
    if selected_uf and "MUNICIPIO" in gdf_full.columns and "UF" in gdf_full.columns:
        municipios = safe_unique(gdf_full[gdf_full["UF"].astype(str) == str(selected_uf)], "MUNICIPIO")
        selected_municipio = st.sidebar.selectbox("Selecione Município", municipios) if municipios else None

st.sidebar.markdown("---")
st.sidebar.subheader("Período mensal")

anos_disponiveis = list(range(2000, 2026))
meses_disponiveis = {
    "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6,
    "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12
}

col1, col2 = st.sidebar.columns(2)
with col1:
    start_mes_nome = st.selectbox("Mês inicial", list(meses_disponiveis.keys()), index=0)
with col2:
    start_ano = st.selectbox("Ano inicial", anos_disponiveis, index=anos_disponiveis.index(2025))

col3, col4 = st.sidebar.columns(2)
with col3:
    end_mes_nome = st.selectbox("Mês final", list(meses_disponiveis.keys()), index=11)
with col4:
    end_ano = st.selectbox("Ano final", anos_disponiveis, index=anos_disponiveis.index(2025))

start_date = date(start_ano, meses_disponiveis[start_mes_nome], 1)
end_date = date(end_ano, meses_disponiveis[end_mes_nome], 1)






apply = st.sidebar.button("✅ Aplicar Filtros")

# Container fixo para logs logo abaixo do botão
if apply:
    log_container = st.sidebar.container()
else:
    log_container = st.sidebar.empty()



if "aplicar" not in st.session_state:
    st.session_state.aplicar = False
if apply:
    st.session_state.aplicar = True

# =====================================================================
# BARRA TOPO-DIREITA (1 LINHA): USUÁRIO | PERMISSÃO | LOGOUT
# =====================================================================
topL, topR = st.columns([7, 3], vertical_alignment="center")
with topR:
    if AUTH_ENABLED and authentication_status:
        c_user, c_role, c_btn = st.columns([2.2, 1.6, 1.2], vertical_alignment="center")

        with c_user:
            st.markdown(
                f'<div class="userbar"><span class="pill">👤 {name}</span></div>',
                unsafe_allow_html=True,
            )

        with c_role:
            st.markdown(
                f'<div class="userbar"><span class="pill">🔐 {get_user_role()}</span></div>',
                unsafe_allow_html=True,
            )

        with c_btn:
            render_logout_in_main(authenticator)

# =====================================================================
# TÍTULO PRINCIPAL
# =====================================================================
st.markdown('<h1 class="main-title">Análise de Dados Climáticos</h1>', unsafe_allow_html=True)

# =====================================================================
# FILTRO DO SHAPEFILE
# =====================================================================
gdf_filtered = gdf_full.copy()

if st.session_state.aplicar:
    if tipo_dado == "Dados por Estado" and selected_uf and "UF" in gdf_filtered.columns:
        gdf_filtered = gdf_filtered[gdf_filtered["UF"].astype(str) == str(selected_uf)]

    elif tipo_dado == "Dados por Empresa" and selected_empresa and "EMPRESA" in gdf_filtered.columns:
        gdf_filtered = gdf_filtered[gdf_filtered["EMPRESA"].astype(str) == str(selected_empresa)]

    elif (
        tipo_dado == "Dados Empresa/Fazenda"
        and selected_empresa
        and selected_fazenda
        and all(c in gdf_filtered.columns for c in ["EMPRESA", "FAZENDA"])
    ):
        gdf_filtered = gdf_filtered[
            (gdf_filtered["EMPRESA"].astype(str) == str(selected_empresa))
            & (gdf_filtered["FAZENDA"].astype(str) == str(selected_fazenda))
        ]

    elif (
        tipo_dado == "Dados por Município"
        and selected_uf
        and selected_municipio
        and all(c in gdf_filtered.columns for c in ["UF", "MUNICIPIO"])
    ):
        gdf_filtered = gdf_filtered[
            (gdf_filtered["UF"].astype(str) == str(selected_uf))
            & (gdf_filtered["MUNICIPIO"].astype(str) == str(selected_municipio))
        ]

# =====================================================================
# =====================================================================
# CARREGAR CSVs — URL / UPLOAD / PASTA LOCAL
# =====================================================================

# =====================================================================
# CARREGAR CSVs — APENAS POR URL
# =====================================================================
df_csv = pd.DataFrame()

if st.session_state.get("aplicar", False):
    try:
        urls = load_urls()
        years = get_years_in_range(start_date, end_date)

        if years:
            with st.spinner(f"Carregando dados climáticos (anos: {', '.join(map(str, years))})..."):
                frames = []

                for y in years:
                    url = get_url_by_year(urls, y)

                    if not url:
                        log_container.warning(f"⚠️ Sem URL para o ano {y}")
                        continue

                    try:
                        df_y = load_csv_from_url_robust(url, y)

                        if df_y is None or df_y.empty:
                            log_container.warning(f"⚠️ Ano {y} sem dados válidos")
                            continue

                        frames.append(df_y)
                        log_container.success(f"✅ {y}: carregado")

                    except Exception as e:
                        log_container.error(f"❌ {y}: erro {e}")

                if frames:
                    df_csv = pd.concat(frames, ignore_index=True)

        # aplica os filtros do app original
        if df_csv is not None and not df_csv.empty:
            df_csv = _normalize_columns(df_csv)

            if "DATA" in df_csv.columns:
                df_csv["DATA"] = pd.to_datetime(df_csv["DATA"], errors="coerce", dayfirst=True)
                df_csv = df_csv.dropna(subset=["DATA"]).copy()
            
                start_period = pd.Period(start_date, freq="M")
                end_period = pd.Period(end_date, freq="M")
            
                df_csv["MES_ANO"] = df_csv["DATA"].dt.to_period("M")
                df_csv = df_csv[
                    (df_csv["MES_ANO"] >= start_period) &
                    (df_csv["MES_ANO"] <= end_period)
                ].copy()
            
                df_csv["MES_ANO"] = df_csv["MES_ANO"].astype(str)

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
            df_csv = pd.DataFrame()
            log_container.warning("⚠️ Nenhum registro carregado.")

    except Exception as e:
        logger.error(f"Erro no carregamento dos CSVs: {e}")
        log_container.error(f"❌ Erro geral no carregamento: {e}")





# =====================================================================
# ABAS
# =====================================================================
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa Principal", "📋 Dados Shape", "📈 Dados de Clima", "📉 Análise Avançada"])

# ===== ABA 1: MAPA =====


# ===== ABA 1: MAPA PRINCIPAL (REESCRITA COM MELHORIAS) =====
with tab1:
    st.markdown('<div class="section-title">Mapa Principal</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # 1) Contexto e resumo rápido
    # ----------------------------------------------------
    if st.session_state.get("aplicar", False):
        gdf_map = gdf_filtered
        tipo_exib = tipo_dado
    else:
        gdf_map = gdf_full
        tipo_exib = "Todos os Dados"

    if gdf_map is None or gdf_map.empty:
        st.info("Nenhuma geometria disponível para exibição no mapa.")
        st.stop()

    area_total_mapa = np.nan
    area_produ_mapa = np.nan
    n_empresas = 0
    n_fazendas = 0
    n_municipios = 0
    n_feicoes = len(gdf_map)

    try:
        if "AREA_T" in gdf_map.columns:
            area_total_mapa = float(pd.to_numeric(gdf_map["AREA_T"], errors="coerce").sum(skipna=True))

        if "AREA_PRODU" in gdf_map.columns:
            area_produ_mapa = float(pd.to_numeric(gdf_map["AREA_PRODU"], errors="coerce").sum(skipna=True))

        if "EMPRESA" in gdf_map.columns:
            n_empresas = int(gdf_map["EMPRESA"].dropna().astype(str).nunique())

        if "FAZENDA" in gdf_map.columns:
            n_fazendas = int(gdf_map["FAZENDA"].dropna().astype(str).nunique())

        if "MUNICIPIO" in gdf_map.columns:
            n_municipios = int(gdf_map["MUNICIPIO"].dropna().astype(str).nunique())
    except Exception:
        pass

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Fazendas", str(n_fazendas))
    with c2:
        st.metric("Área total (ha)", f"{area_total_mapa:.1f}" if pd.notna(area_total_mapa) else "N/A")
    with c3:
        st.metric("Área produtiva (ha)", f"{area_produ_mapa:.1f}" if pd.notna(area_produ_mapa) else "N/A")
    with c4:
        st.metric("Municípios", str(n_municipios))
    with c5:
        st.metric("Feições", f"{n_feicoes:,}".replace(",", "."))

    def descricao_filtro_mapa():
        if tipo_dado == "Dados por Estado":
            return f"Estado: {selected_uf}" if selected_uf else "Estado"
        elif tipo_dado == "Dados por Empresa":
            return f"Empresa: {selected_empresa}" if selected_empresa else "Empresa"
        elif tipo_dado == "Dados Empresa/Fazenda":
            if selected_empresa and selected_fazenda:
                return f"Empresa/Fazenda: {selected_empresa} / {selected_fazenda}"
            elif selected_empresa:
                return f"Empresa: {selected_empresa}"
            return "Empresa/Fazenda"
        elif tipo_dado == "Dados por Município":
            if selected_uf and selected_municipio:
                return f"Município: {selected_municipio} / {selected_uf}"
            elif selected_municipio:
                return f"Município: {selected_municipio}"
            return "Município"
        return "Todos os Dados"

    st.caption(
        f"Camada exibida: {tipo_exib} | Filtro: {descricao_filtro_mapa()} | "
        f"Empresas: {n_empresas} | Fazendas: {n_fazendas}"
    )

    # ----------------------------------------------------
    # 2) Preparação dos campos para exibição
    # ----------------------------------------------------
    gdf_map_display = gdf_map.copy()

    for col in ["AREA_T", "AREA_PRODU"]:
        if col in gdf_map_display.columns:
            gdf_map_display[col] = pd.to_numeric(gdf_map_display[col], errors="coerce").round(1)

    if "AREA_T" in gdf_map_display.columns:
        gdf_map_display["AREA_T_TXT"] = gdf_map_display["AREA_T"].apply(
            lambda x: f"{x:.1f} ha" if pd.notna(x) else "N/A"
        )

    if "AREA_PRODU" in gdf_map_display.columns:
        gdf_map_display["AREA_PRODU_TXT"] = gdf_map_display["AREA_PRODU"].apply(
            lambda x: f"{x:.1f} ha" if pd.notna(x) else "N/A"
        )

    # ----------------------------------------------------
    # 3) Criar mapa base
    # ----------------------------------------------------
    m = folium.Map(tiles=None, control_scale=True)

    bounds = gdf_map_display.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # ----------------------------------------------------
    # 4) Camadas base
    # ----------------------------------------------------
    folium.TileLayer(
        "OpenStreetMap",
        name="OpenStreetMap",
        show=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri World Imagery",
        show=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satélite",
        subdomains=["mt0", "mt1", "mt2", "mt3"],
        show=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Híbrido",
        subdomains=["mt0", "mt1", "mt2", "mt3"],
        show=False,
    ).add_to(m)

    # ----------------------------------------------------
    # 5) Estilo da camada
    # ----------------------------------------------------
    color_map = {
        "Todos os Dados": "#DFF500",
        "Dados por Estado": "#F500B4",
        "Dados por Empresa": "#00C4F5",
        "Dados Empresa/Fazenda": "#FF3B30",
        "Dados por Município": "#F5C400",
    }
    color = color_map.get(tipo_exib, "#3388ff")

    # ----------------------------------------------------
    # 6) Tooltip e popup profissionais
    # ----------------------------------------------------
    tooltip_fields = [
        c for c in [
            "UF",
            "MUNICIPIO",
            "EMPRESA",
            "FAZENDA",
            "AREA_T_TXT",
            "AREA_PRODU_TXT",
        ]
        if c in gdf_map_display.columns
    ]

    tooltip_aliases_map = {
        "UF": "UF",
        "MUNICIPIO": "Município",
        "EMPRESA": "Empresa",
        "FAZENDA": "Fazenda",
        "AREA_T_TXT": "Área Total",
        "AREA_PRODU_TXT": "Área Produtiva",
    }
    tooltip_aliases = [tooltip_aliases_map.get(c, c) for c in tooltip_fields]

    popup_fields = tooltip_fields
    popup_aliases = tooltip_aliases

    # ----------------------------------------------------
    # 7) GeoJson principal com destaque ao passar o mouse
    # ----------------------------------------------------
    folium.GeoJson(
        gdf_map_display.to_json(),
        name="Áreas (Shape)",
        style_function=lambda x: {
            "fillColor": color,
            "color": color,
            "weight": 1.2,
            "fillOpacity": 0.40,
        },
        highlight_function=lambda x: {
            "fillColor": color,
            "color": "#000000",
            "weight": 2.4,
            "fillOpacity": 0.65,
        },
        tooltip=folium.features.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            sticky=True,
            labels=True,
            localize=True,
            style=(
                "background-color: white; "
                "color: #222; "
                "font-family: Arial; "
                "font-size: 12px; "
                "padding: 8px; "
                "border: 1px solid #999; "
                "border-radius: 4px; "
                "box-shadow: 2px 2px 6px rgba(0,0,0,0.15);"
            ),
        ),
        popup=folium.features.GeoJsonPopup(
            fields=popup_fields,
            aliases=popup_aliases,
            localize=True,
            labels=True,
            style="background-color: white;",
        ),
    ).add_to(m)

    # ----------------------------------------------------
    # 8) Legenda visual simples
    # ----------------------------------------------------
    legenda_html = f"""
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        z-index: 9999;
        background-color: white;
        border: 1px solid rgba(0,0,0,0.25);
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 12px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.15);
    ">
        <div style="font-weight: 700; margin-bottom: 6px;">Legenda</div>
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="
                display:inline-block;
                width:16px;
                height:16px;
                background:{color};
                border:1px solid #444;
            "></span>
            <span>{tipo_exib}</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legenda_html))

    # ----------------------------------------------------
    # 9) Controle de camadas
    # ----------------------------------------------------
    folium.LayerControl(collapsed=False).add_to(m)

    # ----------------------------------------------------
    # 10) Exibição
    # ----------------------------------------------------
    st_folium(
        m,
        width=1400,
        height=620,
        key="mapa_principal",
        returned_objects=[],
    )





# ===== ABA 2: DADOS SHAPE (ORDENADA + REMOÇÃO LOCAL_PROJ + EXCEL) =====
# ===== ABA 2: DADOS SHAPE (5 PRIMEIRAS LINHAS + BOTÃO EXIBIR TUDO) =====
with tab2:
    st.markdown('<div class="section-title">Dados Shape</div>', unsafe_allow_html=True)

    if not st.session_state.get("aplicar", False):
        st.info("Clique em 'Aplicar Filtros' na sidebar para ver os dados do shapefile.")
        st.stop()

    if gdf_filtered is None or gdf_filtered.empty:
        st.info("Nenhum dado filtrado para exibir.")
        st.stop()

    # ----------------------------------------------------
    # 1) Preparação
    # ----------------------------------------------------
    df_shape = gdf_filtered.copy()
    df_shape = df_shape.drop(columns=["geometry"], errors="ignore")
    df_shape.columns = [str(c).strip() for c in df_shape.columns]

    aliases = {
        "AREA_PORDUT": "AREA_PRODU",
        "AREA_PRODUT": "AREA_PRODU",
        "AREA_PRODUTIVA": "AREA_PRODU",
    }
    df_shape = df_shape.rename(columns={k: v for k, v in aliases.items() if k in df_shape.columns})

    # ----------------------------------------------------
    # 2) Remover LOCAL_PROJ
    # ----------------------------------------------------
    df_shape = df_shape.drop(columns=["LOCAL_PROJ"], errors="ignore")

    # ----------------------------------------------------
    # 3) Ajustar casas decimais
    # ----------------------------------------------------
    for col_area in ["AREA_T", "AREA_PRODU"]:
        if col_area in df_shape.columns:
            df_shape[col_area] = pd.to_numeric(df_shape[col_area], errors="coerce").round(1)

    # ----------------------------------------------------
    # 4) Reordenar colunas
    # ----------------------------------------------------
    ordem_prioritaria = [
        "UF",
        "EMPRESA",
        "FAZENDA",
        "MUNICIPIO",
        "AREA_T",
        "AREA_PRODU",
        "CENTROIDE_",
        "CENTROID_1",
    ]

    colunas_existentes = [c for c in ordem_prioritaria if c in df_shape.columns]
    outras_colunas = [c for c in df_shape.columns if c not in colunas_existentes]
    df_shape = df_shape[colunas_existentes + outras_colunas]

    # ----------------------------------------------------
    # 5) Exportação Excel
    # ----------------------------------------------------
    import io

    def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Dados_Shape") -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        return output.getvalue()

    excel_bytes = df_to_excel_bytes(df_shape, sheet_name="Dados_Shape")

    st.download_button(
        label="⬇️ Exportar para Excel (.xlsx)",
        data=excel_bytes,
        file_name="dados_shape.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ----------------------------------------------------
    # 6) Exibição parcial / completa
    # ----------------------------------------------------
    if "mostrar_tudo_shape" not in st.session_state:
        st.session_state["mostrar_tudo_shape"] = False

    st.info("Foram exibidas somente as 5 primeiras linhas da tabela.")

    if st.button("Exibir tudo", key="btn_exibir_tudo_shape"):
        st.session_state["mostrar_tudo_shape"] = True

    if st.session_state["mostrar_tudo_shape"]:
        st.dataframe(df_shape, use_container_width=True, height=520)
        st.caption(f"Total de registros: {len(df_shape)}")
    else:
        st.dataframe(df_shape.head(5), use_container_width=True, height=220)
        st.caption(f"Mostrando 5 de {len(df_shape)} registros.")






# ===== ABA 3: DADOS DE CLIMA (ORDEM ESPECÍFICA + EXCEL) =====
# ===== ABA 3: DADOS DE CLIMA (5 PRIMEIRAS LINHAS + BOTÃO EXIBIR TUDO) =====
with tab3:
    st.markdown('<div class="section-title">Dados de Clima</div>', unsafe_allow_html=True)

    if not st.session_state.get("aplicar", False):
        st.info("Clique em 'Aplicar Filtros' na sidebar para carregar os dados de clima.")
        st.stop()

    if df_csv is None or df_csv.empty:
        st.warning("Nenhum dado de clima filtrado.")
        st.stop()

    dfc = df_csv.copy()
    dfc.columns = [str(c).strip() for c in dfc.columns]

    aliases = {
        "Data": "DATA",
        "data": "DATA",
        "AREA_PORDUT": "AREA_PRODU",
        "AREA_PRODUT": "AREA_PRODU",
        "AREA_PRODUTIVA": "AREA_PRODU",
    }
    dfc = dfc.rename(columns={k: v for k, v in aliases.items() if k in dfc.columns})

    if "DATA" not in dfc.columns:
        st.error("❌ Coluna DATA não encontrada.")
        st.stop()

    dfc["DATA"] = pd.to_datetime(dfc["DATA"], errors="coerce", dayfirst=True)
    dfc = dfc.dropna(subset=["DATA"]).copy()

    # ----------------------------------------------------
    # ANO e MÊS
    # ----------------------------------------------------
    meses_pt = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }

    dfc["ANO"] = dfc["DATA"].dt.strftime("%Y")
    dfc["MES"] = dfc["DATA"].dt.month.map(meses_pt)

    # DATA no formato DD-MM-AAAA
    dfc["DATA"] = dfc["DATA"].dt.strftime("%d-%m-%Y")

    # ----------------------------------------------------
    # Ajuste de áreas
    # ----------------------------------------------------
    for col_area in ["AREA_T", "AREA_PRODU"]:
        if col_area in dfc.columns:
            dfc[col_area] = pd.to_numeric(dfc[col_area], errors="coerce").round(1)

    # ----------------------------------------------------
    # Ordem das colunas
    # ----------------------------------------------------
    ordem_especifica = [
        "DATA", "ANO", "MES",
        "EMPRESA", "FAZENDA", "UF", "MUNICIPIO",
        "AREA_T", "AREA_PRODU",
        "PRECIP_CHIRPS_MM",
        "TEMP_MEDIA_C", "TEMP_MIN_C", "TEMP_MAX_C", "AMPLITUDE_TERMICA_C",
        "NOITES_FRIAS_Eucalipto_<15C", "NOITES_FRIAS_Pinus_<5C",
        "ONDAS_CALOR_Eucalipto_>35C", "ONDAS_CALOR_Pinus_>32C",
        "UMID_MEDIA_PCT", "UMID_MIN_PCT", "UMID_MAX_PCT",
        "UMID_NOITE_MEDIA_PCT", "UMID_BAIXA_FLAG",
        "VPD_KPA",
        "VENTO_MEDIO_MS", "VENTO_MAX_MS", "DIRECAO_VENTO_GRAUS",
        "RADIACAO_SOLAR_MJ_M2", "RADIACAO_LIQUIDA_MJ_M2",
        "HORAS_SOL",
        "ET0_MM_DIA", "ET_REAL_MM_DIA",
        "DEFICIT_HIDRICO_MM",
        "DIAS_SEM_CHUVA",
        "INDICE_SECA",
        "INDICE_RISCO_INCENDIO",
        "RISCO_ESTRESSE_HIDRICO",
        "ERA5_IMG_COUNT_DIA",
        "CHIRPS_IMG_COUNT_DIA",
        "CENTROIDE_LAT", "CENTROIDE_LON",
    ]

    colunas_existentes = [c for c in ordem_especifica if c in dfc.columns]
    outras_colunas = [c for c in dfc.columns if c not in colunas_existentes]
    dfc = dfc[colunas_existentes + outras_colunas]

    # ----------------------------------------------------
    # Exportar para Excel
    # ----------------------------------------------------
    import io

    def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Dados_Clima") -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        return output.getvalue()

    excel_bytes = df_to_excel_bytes(dfc, sheet_name="Dados_Clima")

    st.download_button(
        label="⬇️ Exportar para Excel (.xlsx)",
        data=excel_bytes,
        file_name="dados_clima.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ----------------------------------------------------
    # Exibição parcial / completa
    # ----------------------------------------------------
    if "mostrar_tudo_clima" not in st.session_state:
        st.session_state["mostrar_tudo_clima"] = False

    st.info("Foram exibidas somente as 5 primeiras linhas da tabela.")

    if st.button("Exibir tudo", key="btn_exibir_tudo_clima"):
        st.session_state["mostrar_tudo_clima"] = True

    if st.session_state["mostrar_tudo_clima"]:
        st.dataframe(dfc, use_container_width=True, height=520)
        st.caption(f"Total de registros: {len(dfc)}")
        st.caption(f"Colunas: {list(dfc.columns)}")
    else:
        st.dataframe(dfc.head(5), use_container_width=True, height=220)
        st.caption(f"Mostrando 5 de {len(dfc)} registros.")
        st.caption(f"Colunas: {list(dfc.columns)}")





# ===== ABA 4: ANÁLISE AVANÇADA (COMPLETA:# ===== ABA 4: ANÁLISE AVANÇADA (REESCRITA) =====

# ===== ABA 4: ANÁLISE AVANÇADA (ORDEM AJUSTADA) =====
with tab4:
    st.markdown('<div class="section-title">Análise Avançada</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # 1) Validações iniciais
    # ----------------------------------------------------
    if not st.session_state.get("aplicar", False):
        st.info("Clique em **'✅ Aplicar Filtros'** na sidebar para ver a análise.")
        st.stop()

    if df_csv is None or df_csv.empty:
        st.error("❌ Sem dados filtrados para análise.")
        st.info("Verifique se os dados foram carregados corretamente na aba **'Dados de Clima'**.")
        st.stop()

    st.success(f"✅ Analisando {len(df_csv)} registros no período selecionado.")

    # ----------------------------------------------------
    # 2) Preparação e normalização
    # ----------------------------------------------------
    df_work = df_csv.copy()
    df_work.columns = [str(c).strip() for c in df_work.columns]

    aliases = {
        "Data": "DATA",
        "data": "DATA",
        "Empresa": "EMPRESA",
        "Fazenda": "FAZENDA",
        "Município": "MUNICIPIO",
        "Municipio": "MUNICIPIO",
        "PRECIP": "PRECIP_CHIRPS_MM",
        "PRECIP_MM": "PRECIP_CHIRPS_MM",
        "TEMP_MEDIA": "TEMP_MEDIA_C",
        "UMID_MEDIA": "UMID_MEDIA_PCT",
        "AREA_PORDUT": "AREA_PRODU",
        "AREA_PRODUT": "AREA_PRODU",
        "AREA_PRODUTIVA": "AREA_PRODU",
    }
    df_work = df_work.rename(columns={k: v for k, v in aliases.items() if k in df_work.columns})

    def coerce_numeric_br(s: pd.Series) -> pd.Series:
        x = s.astype(str).str.strip()
        x = x.replace({"None": "", "nan": "", "NaN": "", "N/A": "", "-": "", "": np.nan})
        x = x.str.replace(r"[^0-9,\.\-]+", "", regex=True)

        has_dot = x.str.contains(r"\.", na=False)
        has_comma = x.str.contains(r",", na=False)
        both = has_dot & has_comma

        x.loc[both] = x.loc[both].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)

        only_comma = has_comma & ~has_dot
        x.loc[only_comma] = x.loc[only_comma].str.replace(",", ".", regex=False)

        return pd.to_numeric(x, errors="coerce")

    if "DATA" not in df_work.columns:
        st.error("❌ Coluna DATA não encontrada no CSV.")
        st.stop()

    df_work["DATA"] = pd.to_datetime(
        df_work["DATA"].astype(str).str.strip(),
        errors="coerce",
        dayfirst=True
    )
    df_work = df_work.dropna(subset=["DATA"]).copy()

    numeric_candidates = [
        "AREA_PRODU",
        "PRECIP_CHIRPS_MM",
        "TEMP_MEDIA_C",
        "TEMP_MIN_C",
        "TEMP_MAX_C",
        "AMPLITUDE_TERMICA_C",
        "UMID_MEDIA_PCT",
        "DIAS_SEM_CHUVA",
    ]
    for c in numeric_candidates:
        if c in df_work.columns:
            df_work[c] = coerce_numeric_br(df_work[c])

    meses_pt = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }

    df_work["ANO"] = df_work["DATA"].dt.year
    df_work["MES_NUM"] = df_work["DATA"].dt.month
    df_work["MES"] = df_work["MES_NUM"].map(meses_pt)
    df_work["MES_ANO"] = df_work["DATA"].dt.strftime("%Y-%m")

    import io

    def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Resumo") -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        return output.getvalue()

    def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
        v = pd.to_numeric(values, errors="coerce")
        w = pd.to_numeric(weights, errors="coerce")
        m = v.notna() & w.notna() & (w > 0)
        if m.sum() == 0:
            return float("nan")
        return float((v[m] * w[m]).sum() / w[m].sum())

    def area_por_fazenda(g: pd.DataFrame) -> pd.Series:
        if not all(c in g.columns for c in ["FAZENDA", "AREA_PRODU"]):
            return pd.Series(dtype=float)
        tmp = g[["FAZENDA", "AREA_PRODU"]].copy()
        tmp["AREA_PRODU"] = pd.to_numeric(tmp["AREA_PRODU"], errors="coerce")
        return tmp.groupby("FAZENDA", dropna=False)["AREA_PRODU"].first()

    def descricao_filtro():
        if tipo_dado == "Dados por Estado":
            return f"Estado: {selected_uf}" if selected_uf else "Estado"
        elif tipo_dado == "Dados por Empresa":
            return f"Empresa: {selected_empresa}" if selected_empresa else "Empresa"
        elif tipo_dado == "Dados Empresa/Fazenda":
            if selected_empresa and selected_fazenda:
                return f"Empresa/Fazenda: {selected_empresa} / {selected_fazenda}"
            elif selected_empresa:
                return f"Empresa: {selected_empresa}"
            return "Empresa/Fazenda"
        elif tipo_dado == "Dados por Município":
            if selected_uf and selected_municipio:
                return f"Município: {selected_municipio} / {selected_uf}"
            elif selected_municipio:
                return f"Município: {selected_municipio}"
            return "Município"
        return "Todos os Dados"

    filtro_desc = descricao_filtro()
    periodo_desc = f"{start_date.strftime('%m/%Y')} a {end_date.strftime('%m/%Y')}"

    def resumo_mensal_from_df(df: pd.DataFrame) -> pd.DataFrame:
        rows = []

        for (mes_ano, ano, mes_num, mes), g in df.groupby(["MES_ANO", "ANO", "MES_NUM", "MES"], dropna=False):
            row = {
                "MES_ANO": mes_ano,
                "ANO": int(ano) if pd.notna(ano) else np.nan,
                "MES_NUM": int(mes_num) if pd.notna(mes_num) else np.nan,
                "MES": mes,
            }

            areas = area_por_fazenda(g)
            areas_valid = pd.to_numeric(areas, errors="coerce").dropna()
            areas_valid = areas_valid[areas_valid > 0]

            row["AREA_PRODU"] = float(areas_valid.sum()) if not areas_valid.empty else np.nan

            if "PRECIP_CHIRPS_MM" in g.columns:
                precip = pd.to_numeric(g["PRECIP_CHIRPS_MM"], errors="coerce")
                row["Precipitação Total (mm)"] = float(precip.sum(skipna=True)) if precip.notna().any() else np.nan
                row["Precipitação Média Ponderada (mm)"] = weighted_mean(g["PRECIP_CHIRPS_MM"], g["AREA_PRODU"])
                row["Precipitação Máxima (mm)"] = float(precip.max(skipna=True)) if precip.notna().any() else np.nan
                row["Precipitação Mínima (mm)"] = float(precip.min(skipna=True)) if precip.notna().any() else np.nan

            if "TEMP_MEDIA_C" in g.columns:
                row["Média Temp Ponderada (°C)"] = weighted_mean(g["TEMP_MEDIA_C"], g["AREA_PRODU"])

            if "TEMP_MIN_C" in g.columns:
                temp_min = pd.to_numeric(g["TEMP_MIN_C"], errors="coerce")
                row["Temp Mínima (°C)"] = float(temp_min.min(skipna=True)) if temp_min.notna().any() else np.nan

            if "TEMP_MAX_C" in g.columns:
                temp_max = pd.to_numeric(g["TEMP_MAX_C"], errors="coerce")
                row["Temp Máxima (°C)"] = float(temp_max.max(skipna=True)) if temp_max.notna().any() else np.nan

            if "AMPLITUDE_TERMICA_C" in g.columns:
                row["Amplitude Térmica Ponderada (°C)"] = weighted_mean(g["AMPLITUDE_TERMICA_C"], g["AREA_PRODU"])

            if "UMID_MEDIA_PCT" in g.columns:
                row["Umidade Média Ponderada (%)"] = weighted_mean(g["UMID_MEDIA_PCT"], g["AREA_PRODU"])

            if "DIAS_SEM_CHUVA" in g.columns:
                dias_sem = pd.to_numeric(g["DIAS_SEM_CHUVA"], errors="coerce")
                row["Dias sem Chuva"] = float(dias_sem.max(skipna=True)) if dias_sem.notna().any() else np.nan

            rows.append(row)

        out = pd.DataFrame(rows)

        if not out.empty:
            out["DATA_ORDENACAO"] = pd.to_datetime(out["MES_ANO"] + "-01", errors="coerce")
            out = out.sort_values("DATA_ORDENACAO").copy()

            if "AREA_PRODU" in out.columns:
                out["AREA_PRODU"] = pd.to_numeric(out["AREA_PRODU"], errors="coerce").round(1)

            for c in [
                "Precipitação Total (mm)",
                "Precipitação Média Ponderada (mm)",
                "Precipitação Máxima (mm)",
                "Precipitação Mínima (mm)",
                "Média Temp Ponderada (°C)",
                "Temp Mínima (°C)",
                "Temp Máxima (°C)",
                "Amplitude Térmica Ponderada (°C)",
                "Umidade Média Ponderada (%)",
                "Dias sem Chuva",
            ]:
                if c in out.columns:
                    out[c] = pd.to_numeric(out[c], errors="coerce").round(2)

        return out

    def resumo_anual_from_resumo_mensal(resumo_mes: pd.DataFrame) -> pd.DataFrame:
        if resumo_mes is None or resumo_mes.empty:
            return pd.DataFrame()

        rows = []

        for ano, g in resumo_mes.groupby("ANO", dropna=False):
            row = {"ANO": int(ano) if pd.notna(ano) else np.nan}

            if "AREA_PRODU" in g.columns:
                area = pd.to_numeric(g["AREA_PRODU"], errors="coerce")
                row["AREA_PRODU"] = float(area.mean(skipna=True)) if area.notna().any() else np.nan

            if "Precipitação Média Ponderada (mm)" in g.columns:
                precip_media_pond_mes = pd.to_numeric(g["Precipitação Média Ponderada (mm)"], errors="coerce")
                row["Precipitação Total (mm)"] = (
                    float(precip_media_pond_mes.sum(skipna=True))
                    if precip_media_pond_mes.notna().any() else np.nan
                )

            if all(c in g.columns for c in ["Precipitação Média Ponderada (mm)", "AREA_PRODU"]):
                row["Precipitação Média Ponderada (mm)"] = weighted_mean(
                    g["Precipitação Média Ponderada (mm)"],
                    g["AREA_PRODU"]
                )

            if "Precipitação Máxima (mm)" in g.columns:
                precip_max = pd.to_numeric(g["Precipitação Máxima (mm)"], errors="coerce")
                row["Precipitação Máxima (mm)"] = float(precip_max.max(skipna=True)) if precip_max.notna().any() else np.nan

            if "Precipitação Mínima (mm)" in g.columns:
                precip_min = pd.to_numeric(g["Precipitação Mínima (mm)"], errors="coerce")
                row["Precipitação Mínima (mm)"] = float(precip_min.min(skipna=True)) if precip_min.notna().any() else np.nan

            if all(c in g.columns for c in ["Média Temp Ponderada (°C)", "AREA_PRODU"]):
                row["Média Temp Ponderada (°C)"] = weighted_mean(
                    g["Média Temp Ponderada (°C)"],
                    g["AREA_PRODU"]
                )

            if "Temp Mínima (°C)" in g.columns:
                temp_min = pd.to_numeric(g["Temp Mínima (°C)"], errors="coerce")
                row["Temp Mínima (°C)"] = float(temp_min.min(skipna=True)) if temp_min.notna().any() else np.nan

            if "Temp Máxima (°C)" in g.columns:
                temp_max = pd.to_numeric(g["Temp Máxima (°C)"], errors="coerce")
                row["Temp Máxima (°C)"] = float(temp_max.max(skipna=True)) if temp_max.notna().any() else np.nan

            if all(c in g.columns for c in ["Amplitude Térmica Ponderada (°C)", "AREA_PRODU"]):
                row["Amplitude Térmica Ponderada (°C)"] = weighted_mean(
                    g["Amplitude Térmica Ponderada (°C)"],
                    g["AREA_PRODU"]
                )

            if all(c in g.columns for c in ["Umidade Média Ponderada (%)", "AREA_PRODU"]):
                row["Umidade Média Ponderada (%)"] = weighted_mean(
                    g["Umidade Média Ponderada (%)"],
                    g["AREA_PRODU"]
                )

            if "Dias sem Chuva" in g.columns:
                dias_sem = pd.to_numeric(g["Dias sem Chuva"], errors="coerce")
                row["Dias sem Chuva"] = float(dias_sem.max(skipna=True)) if dias_sem.notna().any() else np.nan

            rows.append(row)

        out = pd.DataFrame(rows)

        if not out.empty:
            if "AREA_PRODU" in out.columns:
                out["AREA_PRODU"] = pd.to_numeric(out["AREA_PRODU"], errors="coerce").round(1)

            for c in [
                "Precipitação Total (mm)",
                "Precipitação Média Ponderada (mm)",
                "Precipitação Máxima (mm)",
                "Precipitação Mínima (mm)",
                "Média Temp Ponderada (°C)",
                "Temp Mínima (°C)",
                "Temp Máxima (°C)",
                "Amplitude Térmica Ponderada (°C)",
                "Umidade Média Ponderada (%)",
                "Dias sem Chuva",
            ]:
                if c in out.columns:
                    out[c] = pd.to_numeric(out[c], errors="coerce").round(2)

            out = out.sort_values("ANO").copy()

        return out

    resumo_mes = resumo_mensal_from_df(df_work)
    resumo_ano = resumo_anual_from_resumo_mensal(resumo_mes)

    # ----------------------------------------------------
    # 3) Resumo Executivo
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="section-title">Resumo Executivo</div>', unsafe_allow_html=True)
    st.caption(f"Filtro: {filtro_desc} | Período: {periodo_desc}")

    area_total_resumo = np.nan
    num_fazendas_resumo = 0
    num_empresas_resumo = 0
    num_registros_resumo = len(df_work)

    try:
        if "AREA_PRODU" in df_work.columns and "FAZENDA" in df_work.columns:
            area_total_resumo = float(
                df_work.groupby("FAZENDA", dropna=False)["AREA_PRODU"].first().sum(skipna=True)
            )

        if "FAZENDA" in df_work.columns:
            num_fazendas_resumo = int(df_work["FAZENDA"].dropna().nunique())

        if "EMPRESA" in df_work.columns:
            num_empresas_resumo = int(df_work["EMPRESA"].dropna().nunique())
    except Exception:
        pass

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Área analisada (ha)", f"{area_total_resumo:.1f}" if pd.notna(area_total_resumo) else "N/A")
    with r2:
        st.metric("Fazendas", str(num_fazendas_resumo))
    with r3:
        st.metric("Empresas", str(num_empresas_resumo))
    with r4:
        st.metric("Registros", f"{num_registros_resumo:,}".replace(",", "."))

    # ----------------------------------------------------
    # 4) Painel de Métricas
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="section-title">Painel de Métricas</div>', unsafe_allow_html=True)
    st.caption(f"Filtro: {filtro_desc} | Período: {periodo_desc}")

    precip_total_periodo = np.nan
    precip_media_anual = np.nan
    precip_media_mensal = np.nan
    precip_maxima = np.nan

    if not resumo_ano.empty and "Precipitação Total (mm)" in resumo_ano.columns:
        serie_total_anual = pd.to_numeric(resumo_ano["Precipitação Total (mm)"], errors="coerce")
        if serie_total_anual.notna().any():
            precip_total_periodo = float(serie_total_anual.sum(skipna=True))
            precip_media_anual = float(serie_total_anual.mean(skipna=True))

    if not resumo_mes.empty and "Precipitação Média Ponderada (mm)" in resumo_mes.columns:
        serie_media_pond_mensal = pd.to_numeric(resumo_mes["Precipitação Média Ponderada (mm)"], errors="coerce")
        if serie_media_pond_mensal.notna().any():
            precip_maxima = float(serie_media_pond_mensal.max(skipna=True))

    if not resumo_mes.empty and all(c in resumo_mes.columns for c in ["Precipitação Média Ponderada (mm)", "AREA_PRODU"]):
        precip_media_mensal = weighted_mean(
            resumo_mes["Precipitação Média Ponderada (mm)"],
            resumo_mes["AREA_PRODU"]
        )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Precipitação Total Ponderada (mm)", f"{precip_total_periodo:.2f}" if pd.notna(precip_total_periodo) else "N/A")
    with c2:
        st.metric("Precipitação Média Anual (mm)", f"{precip_media_anual:.2f}" if pd.notna(precip_media_anual) else "N/A")
    with c3:
        st.metric("Precipitação Média Mensal (mm)", f"{precip_media_mensal:.2f}" if pd.notna(precip_media_mensal) else "N/A")
    with c4:
        st.metric("Precipitação Máxima (mm)", f"{precip_maxima:.2f}" if pd.notna(precip_maxima) else "N/A")

    # ----------------------------------------------------
    # 5) Tabela — Resumo por ANO
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="section-title">Tabela — Resumo por ANO</div>', unsafe_allow_html=True)
    st.caption(f"Filtro: {filtro_desc} | Período: {periodo_desc}")

    if not resumo_ano.empty:
        ordem_ano = [
            "ANO", "AREA_PRODU", "Precipitação Total (mm)", "Precipitação Média Ponderada (mm)",
            "Precipitação Máxima (mm)", "Precipitação Mínima (mm)", "Média Temp Ponderada (°C)",
            "Temp Mínima (°C)", "Temp Máxima (°C)", "Amplitude Térmica Ponderada (°C)",
            "Umidade Média Ponderada (%)", "Dias sem Chuva",
        ]
        resumo_ano = resumo_ano[[c for c in ordem_ano if c in resumo_ano.columns]]

        st.success(f"✅ Resumo anual gerado: {len(resumo_ano)} anos")
        st.dataframe(resumo_ano, use_container_width=True, height=260)

        excel_bytes_ano = df_to_excel_bytes(resumo_ano, sheet_name="Resumo_Ano")
        st.download_button(
            label="⬇️ Baixar Resumo por ANO (.xlsx)",
            data=excel_bytes_ano,
            file_name="resumo_ano.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_resumo_ano"
        )
    else:
        st.warning("⚠️ Não foi possível gerar o resumo por ano.")

    # ----------------------------------------------------
    # 6) Tabela — Resumo por Mês
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="section-title">Tabela — Resumo por Mês</div>', unsafe_allow_html=True)
    st.caption(f"Filtro: {filtro_desc} | Período: {periodo_desc}")

    if not resumo_mes.empty:
        ordem_mes = [
            "MES_ANO", "ANO", "MES", "AREA_PRODU",
            "Precipitação Média Ponderada (mm)", "Precipitação Máxima (mm)",
            "Precipitação Mínima (mm)", "Média Temp Ponderada (°C)",
            "Temp Mínima (°C)", "Temp Máxima (°C)", "Amplitude Térmica Ponderada (°C)",
            "Umidade Média Ponderada (%)", "Dias sem Chuva",
        ]
        resumo_mes_exibir = resumo_mes[[c for c in ordem_mes if c in resumo_mes.columns]].copy()

        st.success(f"✅ Resumo mensal gerado: {len(resumo_mes_exibir)} meses")
        st.dataframe(resumo_mes_exibir, use_container_width=True, height=420)

        excel_bytes_mes = df_to_excel_bytes(resumo_mes_exibir, sheet_name="Resumo_Mes")
        st.download_button(
            label="⬇️ Baixar Resumo por MÊS (.xlsx)",
            data=excel_bytes_mes,
            file_name="resumo_mes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_resumo_mes"
        )
    else:
        st.warning("⚠️ Não foi possível gerar o resumo por mês.")

    # ----------------------------------------------------
    # 7) Gráficos na ordem solicitada
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="section-title">Gráficos</div>', unsafe_allow_html=True)
    st.caption(f"Filtro: {filtro_desc} | Período: {periodo_desc}")

    grafico_ano_base = resumo_ano.copy() if not resumo_ano.empty else pd.DataFrame()
    if not grafico_ano_base.empty:
        grafico_ano_base["X_LABEL"] = grafico_ano_base["ANO"].astype(str)

    grafico_mes_base = resumo_mes.copy() if not resumo_mes.empty else pd.DataFrame()
    if not grafico_mes_base.empty:
        grafico_mes_base["X_LABEL"] = grafico_mes_base["MES_ANO"].astype(str)

    default_mes_checkbox = False if (not resumo_ano.empty and len(resumo_ano) > 2) else True

    def titulo_grafico(base_titulo: str) -> str:
        return f"{base_titulo} | {tipo_dado} | {filtro_desc} | Período: {periodo_desc}"

    # 7.1 Precipitação Total
    st.markdown("**Precipitação Total**")
    mostrar_precip_total_por_mes = st.checkbox(
        "Exibir Precipitação Total por Mês",
        value=(default_mes_checkbox if not grafico_mes_base.empty else False),
        key="mostrar_por_mes_precipitacao_total"
    )

    if mostrar_precip_total_por_mes and not grafico_mes_base.empty and "Precipitação Média Ponderada (mm)" in grafico_mes_base.columns:
        base_plot = grafico_mes_base.copy()
        y_col = "Precipitação Média Ponderada (mm)"
        fig = px.bar(
            base_plot.dropna(subset=[y_col]),
            x="X_LABEL", y=y_col,
            title=titulo_grafico("Precipitação Total")
        )
        fig.update_layout(xaxis_title="Mês", yaxis_title="Precipitação Total")
        st.plotly_chart(fig, use_container_width=True)
    elif not grafico_ano_base.empty and "Precipitação Total (mm)" in grafico_ano_base.columns:
        base_plot = grafico_ano_base.copy()
        y_col = "Precipitação Total (mm)"
        fig = px.bar(
            base_plot.dropna(subset=[y_col]),
            x="X_LABEL", y=y_col,
            title=titulo_grafico("Precipitação Total")
        )
        fig.update_layout(xaxis_title="Ano", yaxis_title="Precipitação Total")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados para exibir o gráfico Precipitação Total.")

    # Função auxiliar para os demais gráficos
    def plot_grafico_ordenado(col_plot, titulo):
        fonte_mes = not grafico_mes_base.empty and col_plot in grafico_mes_base.columns
        fonte_ano = not grafico_ano_base.empty and col_plot in grafico_ano_base.columns

        if not fonte_mes and not fonte_ano:
            return

        st.markdown(f"**{titulo}**")
        checkbox_key = f"mostrar_por_mes_{col_plot}"

        mostrar_por_mes = st.checkbox(
            f"Exibir {titulo} por Mês",
            value=(default_mes_checkbox if fonte_mes else False),
            key=checkbox_key
        )

        if mostrar_por_mes and fonte_mes:
            base_plot = grafico_mes_base.copy()
            x_col = "X_LABEL"
            x_title = "Mês"
        elif fonte_ano:
            base_plot = grafico_ano_base.copy()
            x_col = "X_LABEL"
            x_title = "Ano"
        elif fonte_mes:
            base_plot = grafico_mes_base.copy()
            x_col = "X_LABEL"
            x_title = "Mês"
        else:
            st.info(f"Sem dados para exibir o gráfico {titulo}.")
            return

        fig = px.bar(
            base_plot.dropna(subset=[col_plot]),
            x=x_col, y=col_plot,
            title=titulo_grafico(titulo)
        )
        fig.update_layout(xaxis_title=x_title, yaxis_title=titulo)
        st.plotly_chart(fig, use_container_width=True)

    # Ordem solicitada
    plot_grafico_ordenado("Precipitação Média Ponderada (mm)", "Precipitação Média Ponderada")
    plot_grafico_ordenado("Precipitação Máxima (mm)", "Precipitação Máxima")
    plot_grafico_ordenado("Média Temp Ponderada (°C)", "Média Temp Ponderada")
    plot_grafico_ordenado("Temp Mínima (°C)", "Temp Mínima")
    plot_grafico_ordenado("Temp Máxima (°C)", "Temp Máxima")
    plot_grafico_ordenado("Umidade Média Ponderada (%)", "Umidade Média Ponderada")
    plot_grafico_ordenado("Precipitação Mínima (mm)", "Precipitação Mínima")

    # ----------------------------------------------------
    # 8) Tabela Comparativo entre anos
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="section-title">Tabela Comparativo entre anos</div>', unsafe_allow_html=True)
    st.caption(f"Filtro: {filtro_desc} | Período: {periodo_desc}")

    comparativo_ano_exibir = pd.DataFrame()

    if not resumo_ano.empty and "Precipitação Total (mm)" in resumo_ano.columns:
        comparativo_ano = resumo_ano.copy()
        comparativo_ano["Precipitação Total (mm)"] = pd.to_numeric(
            comparativo_ano["Precipitação Total (mm)"], errors="coerce"
        )
        comparativo_ano = comparativo_ano.sort_values("ANO").copy()
        comparativo_ano["Variação da Precipitação (%)"] = (
            comparativo_ano["Precipitação Total (mm)"].pct_change() * 100
        ).round(2)

        ordem_comp = ["ANO", "Precipitação Total (mm)", "Variação da Precipitação (%)"]
        comparativo_ano_exibir = comparativo_ano[[c for c in ordem_comp if c in comparativo_ano.columns]]

        st.dataframe(comparativo_ano_exibir, use_container_width=True, height=220)
    else:
        st.info("Sem dados suficientes para o comparativo entre anos.")

    # ----------------------------------------------------
    # 9) Gráfico variação de Precipitação entre Anos
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="section-title">Gráfico variação de Precipitação entre Anos</div>', unsafe_allow_html=True)
    st.caption(f"Filtro: {filtro_desc} | Período: {periodo_desc}")

    if not comparativo_ano_exibir.empty and "Variação da Precipitação (%)" in comparativo_ano_exibir.columns:
        if comparativo_ano_exibir["Variação da Precipitação (%)"].notna().any():
            fig_comp = px.bar(
                comparativo_ano_exibir.dropna(subset=["Variação da Precipitação (%)"]),
                x="ANO",
                y="Variação da Precipitação (%)",
                title=f"Variação de Precipitação entre Anos | {tipo_dado} | {filtro_desc} | Período: {periodo_desc}"
            )
            fig_comp.update_layout(
                xaxis_title="Ano",
                yaxis_title="Variação da Precipitação (%)"
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Não há variação calculável entre anos para exibir.")
    else:
        st.info("Sem dados suficientes para o gráfico de variação entre anos.")

    # ----------------------------------------------------
    # 10) Contexto do filtro aplicado
    # ----------------------------------------------------
    st.markdown("---")
    with st.expander("ℹ️ Contexto do filtro aplicado", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tipo de dado", tipo_dado)
        c2.metric("Data inicial", str(start_date))
        c3.metric("Data final", str(end_date))
        c4.metric("Registros", str(len(df_csv)))

        f1, f2, f3, f4 = st.columns(4)
        f1.write(f"**UF:** {selected_uf if selected_uf else '—'}")
        f2.write(f"**Município:** {selected_municipio if selected_municipio else '—'}")
        f3.write(f"**Empresa:** {selected_empresa if selected_empresa else '—'}")
        f4.write(f"**Fazenda:** {selected_fazenda if selected_fazenda else '—'}")

    # ----------------------------------------------------
    # 11) Diagnóstico rápido — valores válidos
    # ----------------------------------------------------
    st.markdown("---")
    with st.expander("🧪 Diagnóstico rápido — valores válidos", expanded=False):
        cols_check = [
            "AREA_PRODU",
            "PRECIP_CHIRPS_MM",
            "TEMP_MEDIA_C",
            "UMID_MEDIA_PCT",
            "DIAS_SEM_CHUVA",
        ]
        info = {}
        for c in cols_check:
            if c in df_work.columns:
                info[c] = f"{int(df_work[c].notna().sum())} / {len(df_work)}"

        st.write(info if info else "Nenhuma coluna esperada foi encontrada.")
        st.write("Colunas disponíveis:", list(df_work.columns))
