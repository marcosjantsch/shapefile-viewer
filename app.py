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
def load_csv_from_url_robust(url, year):
    """Carrega CSV de URL com tratamento robusto de codificação."""
    
    if 'example.com' in url:
        return generate_fictitious_csv_data(year)

    try:
        if '1drv.ms' in url and 'download=1' not in url:
            if '?' in url:
                url = url + '&download=1'
            else:
                url = url + '?download=1'
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        separators = [';', ',', '\t', '|']
        
        for encoding in encodings:
            for separator in separators:
                try:
                    content = response.content.decode(encoding)
                    df = pd.read_csv(
                        io.StringIO(content),
                        sep=separator,
                        on_bad_lines='skip',
                        engine='python'
                    )
                    
                    if len(df.columns) > 1:
                        df.columns = df.columns.str.strip()
                        return df
                except Exception:
                    continue
        
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao baixar arquivo da URL {url}: {e}")
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
        "Todos os Dados": "gray",
        "Dados por Estado": "green",
        "Dados por Empresa": "blue",
        "Dados Empresa/Fazenda": "red",
        "Dados por Município": "orange",
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
st.sidebar.subheader("Período")
start_date = st.sidebar.date_input("Data Inicial", value=date(2020, 1, 1))
end_date = st.sidebar.date_input("Data Final", value=date.today())
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
# CARREGAR CSVs — CORRIGIDO
# =====================================================================
df_csv = pd.DataFrame()

if st.session_state.aplicar:
    urls = load_urls()
    years = get_years_in_range(start_date, end_date)

    if years:
        with st.spinner(f"Carregando dados climáticos (anos: {', '.join(map(str, years))})..."):
            df_csv = pd.DataFrame()

            for y in years:
                url = get_url_by_year(urls, y)
            
                if not url:
                    log_container.warning(f"⚠️ Sem URL para o ano {y}")
                    continue
            
                try:
                    df_y = load_csv_from_url_robust(url, y)
            
                    if df_y is None or df_y.empty:
                        continue
            
                    log_container.success(f"✅ {y}: carregado ({df_y.shape[0]} linhas)")
            
                    # 🔥 FILTRAR ANTES DE ACUMULAR
                    if "DATA" in df_y.columns:
                        df_y["DATA"] = pd.to_datetime(df_y["DATA"], errors="coerce")
                        df_y = df_y.dropna(subset=["DATA"])
                        df_y = df_y[
                            (df_y["DATA"].dt.date >= start_date) &
                            (df_y["DATA"].dt.date <= end_date)
                        ]
            
                    # 🔥 FILTRO POR TIPO
                    if tipo_dado == "Dados por Estado" and selected_uf and "UF" in df_y.columns:
                        df_y = df_y[df_y["UF"].astype(str) == str(selected_uf)]
            
                    elif tipo_dado == "Dados por Empresa" and selected_empresa and "EMPRESA" in df_y.columns:
                        df_y = df_y[df_y["EMPRESA"].astype(str) == str(selected_empresa)]
            
                    elif (
                        tipo_dado == "Dados Empresa/Fazenda"
                        and selected_empresa
                        and selected_fazenda
                        and all(c in df_y.columns for c in ["EMPRESA", "FAZENDA"])
                    ):
                        df_y = df_y[
                            (df_y["EMPRESA"].astype(str) == str(selected_empresa)) &
                            (df_y["FAZENDA"].astype(str) == str(selected_fazenda))
                        ]
            
                    elif (
                        tipo_dado == "Dados por Município"
                        and selected_uf
                        and selected_municipio
                        and all(c in df_y.columns for c in ["UF", "MUNICIPIO"])
                    ):
                        df_y = df_y[
                            (df_y["UF"].astype(str) == str(selected_uf)) &
                            (df_y["MUNICIPIO"].astype(str) == str(selected_municipio))
                        ]
            
                    # 🔥 CONCAT CONTROLADO (sem lista gigante)
                    df_csv = pd.concat([df_csv, df_y], ignore_index=True)
            
                except Exception as e:
                    log_container.error(f"❌ {y}: erro {e}")
            
            log_container.info(f"📦 Total de {len(df_csv)} registros após carga otimizada")

        # ✅ FILTRAR POR DATA (APENAS SE df_csv NÃO ESTIVER VAZIO)
        if not df_csv.empty and "DATA" in df_csv.columns:
            df_csv["DATA"] = pd.to_datetime(df_csv["DATA"], errors="coerce")
            df_csv = df_csv.dropna(subset=["DATA"])
            df_csv = df_csv[(df_csv["DATA"].dt.date >= start_date) & (df_csv["DATA"].dt.date <= end_date)].copy()
            logger.info(f"Após filtro de data: {len(df_csv)} registros")

        # ✅ FILTRAR POR MODO (APENAS SE df_csv NÃO ESTIVER VAZIO)
        if not df_csv.empty:
            if tipo_dado == "Dados por Estado" and selected_uf and "UF" in df_csv.columns:
                df_csv = df_csv[df_csv["UF"].astype(str) == str(selected_uf)]

            elif tipo_dado == "Dados por Empresa" and selected_empresa and "EMPRESA" in df_csv.columns:
                df_csv = df_csv[df_csv["EMPRESA"].astype(str) == str(selected_empresa)]

            elif (
                tipo_dado == "Dados Empresa/Fazenda"
                and selected_empresa
                and selected_fazenda
                and all(c in df_csv.columns for c in ["EMPRESA", "FAZENDA"])
            ):
                df_csv = df_csv[
                    (df_csv["EMPRESA"].astype(str) == str(selected_empresa))
                    & (df_csv["FAZENDA"].astype(str) == str(selected_fazenda))
                ]

            elif (
                tipo_dado == "Dados por Município"
                and selected_uf
                and selected_municipio
                and all(c in df_csv.columns for c in ["UF", "MUNICIPIO"])
            ):
                df_csv = df_csv[
                    (df_csv["UF"].astype(str) == str(selected_uf))
                    & (df_csv["MUNICIPIO"].astype(str) == str(selected_municipio))
                ]

            logger.info(f"Após filtro de modo: {len(df_csv)} registros")
            log_container.success(f"🔎 Após filtros: {len(df_csv)} registros")


# =====================================================================
# ABAS
# =====================================================================
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa Principal", "📋 Dados Shape", "📈 Dados de Clima", "📉 Análise Avançada"])

# ===== ABA 1: MAPA =====


# ===== ABA 1: MAPA PRINCIPAL (CARREGA GEO COMPLETO + CONTROLE VIA MAPA) =====
with tab1:
    st.markdown('<div class="section-title">Mapa Principal</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # 1) Define qual GEO mostrar
    #    - Ao iniciar: mostra TODO o shapefile
    #    - Após aplicar filtros: mostra filtrado
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

    # ----------------------------------------------------
    # 2) Criar mapa sem tile inicial
    # ----------------------------------------------------
    m = folium.Map(tiles=None)

    bounds = gdf_map.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # ----------------------------------------------------
    # 3) Camadas Base (controle via LayerControl)
    # ----------------------------------------------------

    # OpenStreetMap
    folium.TileLayer(
        "OpenStreetMap",
        name="OpenStreetMap",
        show=True,
    ).add_to(m)

    # Esri World Imagery
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri World Imagery",
        show=False,
    ).add_to(m)

    # Google Satélite
    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satélite",
        subdomains=["mt0", "mt1", "mt2", "mt3"],
        show=False,
    ).add_to(m)

    # Google Híbrido
    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Híbrido",
        subdomains=["mt0", "mt1", "mt2", "mt3"],
        show=False,
    ).add_to(m)

    # ----------------------------------------------------
    # 4) Camada do Shape
    # ----------------------------------------------------
    color_map = {
        "Todos os Dados": "#DFF500",
        "Dados por Estado": "#F500B4",
        "Dados por Empresa": "#00C4F5",
        "Dados Empresa/Fazenda": "red",
        "Dados por Município": "#F5C400",
    }
    color = color_map.get(tipo_exib, "blue")

    fields = [c for c in ["UF", "MUNICIPIO", "EMPRESA", "FAZENDA"] if c in gdf_map.columns]
    aliases_map = {
        "UF": "UF",
        "MUNICIPIO": "Município",
        "EMPRESA": "Empresa",
        "FAZENDA": "Fazenda",
    }
    aliases = [aliases_map.get(c, c) for c in fields]

    folium.GeoJson(
        gdf_map.to_json(),
        name="Áreas (Shape)",
        style_function=lambda x: {
            "fillColor": color,
            "color": color,
            "weight": 1,
            "fillOpacity": 0.55,
        },
        tooltip=folium.features.GeoJsonTooltip(
            fields=fields,
            aliases=aliases,
            sticky=False,
        ),
    ).add_to(m)

    # ----------------------------------------------------
    # 5) Controle de Camadas (único método de seleção)
    # ----------------------------------------------------
    folium.LayerControl(collapsed=False).add_to(m)

    # ----------------------------------------------------
    # 6) Renderização
    # ----------------------------------------------------
    st_folium(
        m,
        width=1400,
        height=600,
        key="mapa_principal",
        returned_objects=[],
    )






# ===== ABA 2: DADOS SHAPE (ORDENADA + REMOÇÃO LOCAL_PROJ + EXCEL) =====
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

    # Corrige possíveis variações/typos
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
    # 4) Reordenar colunas conforme solicitado
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
    # 6) Exibição
    # ----------------------------------------------------
    st.dataframe(df_shape, use_container_width=True, height=520)
    st.caption(f"Total de registros: {len(df_shape)}")
    st.caption(f"Colunas: {list(df_shape.columns)}")






# ===== ABA 3: DADOS DE CLIMA (AJUSTADA: DATA DD-MM-AAAA + ANO + MÊS + ÁREAS 1 DECIMAL + EXPORT EXCEL) =====

# ===== ABA 3: DADOS DE CLIMA (ORDEM ESPECÍFICA + EXCEL) =====
with tab3:
    st.markdown('<div class="section-title">Dados de Clima</div>', unsafe_allow_html=True)

    if not st.session_state.get("aplicar", False):
        st.info("Clique em 'Aplicar Filtros' na sidebar para carregar os dados de clima.")
        st.stop()

    if df_csv is None or df_csv.empty:
        st.warning("Nenhum dado de clima filtrado.")
        st.stop()

    # ----------------------------------------------------
    # 1) Preparação
    # ----------------------------------------------------
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

    dfc["DATA"] = pd.to_datetime(dfc["DATA"], errors="coerce")
    dfc = dfc.dropna(subset=["DATA"]).copy()

    # ----------------------------------------------------
    # 2) ANO e MÊS (PT-BR)
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
    # 3) AREA_T e AREA_PRODU com 1 casa decimal
    # ----------------------------------------------------
    for col_area in ["AREA_T", "AREA_PRODU"]:
        if col_area in dfc.columns:
            dfc[col_area] = pd.to_numeric(dfc[col_area], errors="coerce").round(1)

    # ----------------------------------------------------
    # 4) ORDEM EXATA DAS COLUNAS
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
    # 5) Exportar para Excel
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
    # 6) Exibição
    # ----------------------------------------------------
    st.dataframe(dfc, use_container_width=True, height=520)
    st.caption(f"Total de registros: {len(dfc)}")
    st.caption(f"Colunas: {list(dfc.columns)}")










# ===== ABA 4: ANÁLISE AVANÇADA (COMPLETA: ANO/MÊS + EXCEL + ÁREA 1 DECIMAL + GRÁFICOS EM BARRAS) =====
with tab4:
    st.markdown('<div class="section-title">Análise Avançada</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # 1) Guard-rails
    # ----------------------------------------------------
    if not st.session_state.get("aplicar", False):
        st.info("Clique em **'✅ Aplicar Filtros'** na sidebar para ver a análise.")
        st.stop()

    if df_csv is None or df_csv.empty:
        st.error("❌ Sem dados filtrados para análise.")
        st.info("Verifique se os dados foram carregados corretamente na aba **'Dados de Clima'**.")
        st.stop()

    # ----------------------------------------------------
    # 2) Contexto
    # ----------------------------------------------------
    st.success(f"✅ Analisando {len(df_csv)} registros no período selecionado.")

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
    # 3) Normalização + Conversão numérica BR
    # ----------------------------------------------------
    df_work = df_csv.copy()
    df_work.columns = [str(c).strip() for c in df_work.columns]

    aliases = {
        "Data": "DATA", "data": "DATA",
        "Empresa": "EMPRESA", "Fazenda": "FAZENDA",
        "Município": "MUNICIPIO", "Municipio": "MUNICIPIO",
        "PRECIP": "PRECIP_CHIRPS_MM", "PRECIP_MM": "PRECIP_CHIRPS_MM",
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

        # 1.234,56 -> 1234.56
        x.loc[both] = x.loc[both].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)

        # 123,45 -> 123.45
        only_comma = has_comma & ~has_dot
        x.loc[only_comma] = x.loc[only_comma].str.replace(",", ".", regex=False)

        return pd.to_numeric(x, errors="coerce")

    # DATA
    if "DATA" in df_work.columns:
        df_work["DATA"] = pd.to_datetime(df_work["DATA"], errors="coerce")
        df_work = df_work.dropna(subset=["DATA"]).copy()
    else:
        st.error("❌ Coluna DATA não encontrada no CSV.")
        st.stop()

    # Converter colunas numéricas relevantes (se existirem)
    numeric_candidates = [
        "AREA_PRODU",
        "PRECIP_CHIRPS_MM",
        "TEMP_MEDIA_C", "TEMP_MIN_C", "TEMP_MAX_C", "AMPLITUDE_TERMICA_C",
        "UMID_MEDIA_PCT",
        "DIAS_SEM_CHUVA",
    ]
    for c in numeric_candidates:
        if c in df_work.columns:
            df_work[c] = coerce_numeric_br(df_work[c])

    # Diagnóstico rápido
    with st.expander("🧪 Diagnóstico rápido — valores válidos", expanded=False):
        cols_check = ["AREA_PRODU", "PRECIP_CHIRPS_MM", "TEMP_MEDIA_C", "UMID_MEDIA_PCT", "DIAS_SEM_CHUVA"]
        info = {}
        for c in cols_check:
            if c in df_work.columns:
                info[c] = f"{int(df_work[c].notna().sum())} / {len(df_work)}"
        st.write(info if info else "Nenhuma coluna esperada foi encontrada.")
        st.write("Colunas disponíveis:", list(df_work.columns))

    # ----------------------------------------------------
    # 4) Funções auxiliares (ponderação + export excel)
    # ----------------------------------------------------
    def wmean(values: pd.Series, weights: pd.Series) -> float:
        v = pd.to_numeric(values, errors="coerce")
        w = pd.to_numeric(weights, errors="coerce")
        m = v.notna() & w.notna() & (w > 0)
        if m.sum() == 0:
            return float("nan")
        return float((v[m] * w[m]).sum() / w[m].sum())

    def wmean_col(g: pd.DataFrame, value_col: str, weight_col: str = "AREA_PRODU") -> float:
        if value_col not in g.columns or weight_col not in g.columns:
            return float("nan")
        return wmean(g[value_col], g[weight_col])

    import io

    def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Resumo_AnoMes") -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        return output.getvalue()

    # ----------------------------------------------------
    # 5) Painel de Métricas (apenas Precip WP com 2 casas)
    # ----------------------------------------------------
    st.markdown('<div class="section-title">Painel de Métricas</div>', unsafe_allow_html=True)

    precip_wp = np.nan
    if all(c in df_work.columns for c in ["FAZENDA", "AREA_PRODU", "PRECIP_CHIRPS_MM"]):
        areas = df_work.groupby("FAZENDA")["AREA_PRODU"].first()
        p_sum = df_work.groupby("FAZENDA")["PRECIP_CHIRPS_MM"].sum(min_count=1)
        tmp = pd.concat([areas.rename("A"), p_sum.rename("P")], axis=1).dropna()
        tmp = tmp[tmp["A"] > 0]
        if not tmp.empty:
            precip_wp = float((tmp["P"] * tmp["A"]).sum() / tmp["A"].sum())

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            "Precipitação (média ponderada por AREA_PRODU)",
            f"{precip_wp:.2f}" if pd.notna(precip_wp) else "N/A",
        )
    with c2:
        st.metric(" ", " ")
    with c3:
        st.metric(" ", " ")

    # ----------------------------------------------------
    # 6) TABELA — RESUMO POR ANO/MÊS (precip ponderada por área)
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="section-title">Tabela — Resumo por Ano/Mês</div>', unsafe_allow_html=True)

    required_cols = ["DATA", "FAZENDA", "AREA_PRODU", "PRECIP_CHIRPS_MM"]
    missing_req = [c for c in required_cols if c not in df_work.columns]
    if missing_req:
        st.error(f"❌ Não foi possível gerar o resumo por Ano/Mês. Faltando colunas: {missing_req}")
        st.stop()

    dfm = df_work.copy()
    dfm["ANO_MES"] = dfm["DATA"].dt.to_period("M").astype(str)

    # Agrega por FAZENDA + ANO_MES (bloco mensal por fazenda)
    agg_faz_mes = {
        "AREA_PRODU": "first",
        "PRECIP_CHIRPS_MM": "sum",
    }
    if "TEMP_MEDIA_C" in dfm.columns:
        agg_faz_mes["TEMP_MEDIA_C"] = "mean"
    if "AMPLITUDE_TERMICA_C" in dfm.columns:
        agg_faz_mes["AMPLITUDE_TERMICA_C"] = "mean"
    if "UMID_MEDIA_PCT" in dfm.columns:
        agg_faz_mes["UMID_MEDIA_PCT"] = "mean"
    if "TEMP_MAX_C" in dfm.columns:
        agg_faz_mes["TEMP_MAX_C"] = "max"
    if "TEMP_MIN_C" in dfm.columns:
        agg_faz_mes["TEMP_MIN_C"] = "min"
    if "DIAS_SEM_CHUVA" in dfm.columns:
        agg_faz_mes["DIAS_SEM_CHUVA"] = "max"

    faz_mes = (
        dfm.groupby(["ANO_MES", "FAZENDA"], dropna=False)
        .agg(agg_faz_mes)
        .reset_index()
        .rename(columns={
            "PRECIP_CHIRPS_MM": "PRECIP_MENSAL",
            "TEMP_MEDIA_C": "TEMP_MEDIA_MENSAL",
            "AMPLITUDE_TERMICA_C": "AMP_TERMICA_MENSAL",
            "UMID_MEDIA_PCT": "UMID_MEDIA_MENSAL",
            "TEMP_MAX_C": "TEMP_MAX_MENSAL",
            "TEMP_MIN_C": "TEMP_MIN_MENSAL",
            "DIAS_SEM_CHUVA": "DIAS_SEM_CHUVA_MAX_MENSAL",
        })
    )

    # Segurança de pesos
    faz_mes["AREA_PRODU"] = pd.to_numeric(faz_mes["AREA_PRODU"], errors="coerce")
    faz_mes = faz_mes.dropna(subset=["AREA_PRODU"])
    faz_mes = faz_mes[faz_mes["AREA_PRODU"] > 0].copy()

    # Agrega por ANO_MES (resultado final)
    out_rows = []
    for ano_mes, g in faz_mes.groupby("ANO_MES", dropna=False):
        row = {"Ano/Mês": str(ano_mes)}

        # AREA_PRODU consolidada no mês = soma das áreas (por fazenda)
        row["AREA_PRODU"] = float(g["AREA_PRODU"].sum(skipna=True))

        # Precipitação: MÉDIA PONDERADA por AREA_PRODU do TOTAL mensal por fazenda
        row["Precipitação (mm)"] = wmean_col(g, "PRECIP_MENSAL", "AREA_PRODU")

        # Médias mensais (ponderadas por área) das médias por fazenda
        row["Média Temp (°C)"] = wmean_col(g, "TEMP_MEDIA_MENSAL", "AREA_PRODU") if "TEMP_MEDIA_MENSAL" in g.columns else np.nan
        row["Média Amplitude Térmica (°C)"] = wmean_col(g, "AMP_TERMICA_MENSAL", "AREA_PRODU") if "AMP_TERMICA_MENSAL" in g.columns else np.nan
        row["Média Umidade (%)"] = wmean_col(g, "UMID_MEDIA_MENSAL", "AREA_PRODU") if "UMID_MEDIA_MENSAL" in g.columns else np.nan

        # Extremos no mês (entre fazendas)
        row["Maior Temp (°C)"] = float(pd.to_numeric(g.get("TEMP_MAX_MENSAL"), errors="coerce").max(skipna=True)) if "TEMP_MAX_MENSAL" in g.columns else np.nan
        row["Menor Temp (°C)"] = float(pd.to_numeric(g.get("TEMP_MIN_MENSAL"), errors="coerce").min(skipna=True)) if "TEMP_MIN_MENSAL" in g.columns else np.nan

        # Máx dias sem chuva no mês (por fazenda) -> pondera por área
        row["Máx Dias Sem Chuva (média ponderada)"] = wmean_col(g, "DIAS_SEM_CHUVA_MAX_MENSAL", "AREA_PRODU") if "DIAS_SEM_CHUVA_MAX_MENSAL" in g.columns else np.nan

        out_rows.append(row)

    resumo_mes = pd.DataFrame(out_rows)

    # Ordena Ano/Mês
    resumo_mes["_DT"] = pd.to_datetime(resumo_mes["Ano/Mês"] + "-01", errors="coerce")
    resumo_mes = resumo_mes.sort_values("_DT").drop(columns=["_DT"])

    # Arredondamentos
    if "AREA_PRODU" in resumo_mes.columns:
        resumo_mes["AREA_PRODU"] = pd.to_numeric(resumo_mes["AREA_PRODU"], errors="coerce").round(1)  # 1 casa
    if "Precipitação (mm)" in resumo_mes.columns:
        resumo_mes["Precipitação (mm)"] = pd.to_numeric(resumo_mes["Precipitação (mm)"], errors="coerce").round(2)

    for c in [
        "Média Temp (°C)", "Média Amplitude Térmica (°C)", "Média Umidade (%)",
        "Maior Temp (°C)", "Menor Temp (°C)", "Máx Dias Sem Chuva (média ponderada)"
    ]:
        if c in resumo_mes.columns:
            resumo_mes[c] = pd.to_numeric(resumo_mes[c], errors="coerce").round(2)

    st.success(f"✅ Resumo gerado: {len(resumo_mes)} períodos (Ano/Mês)")
    st.dataframe(resumo_mes, use_container_width=True, height=420)

    # Exportação DIRETO para Excel
    excel_bytes = df_to_excel_bytes(resumo_mes, sheet_name="Resumo_AnoMes")
    st.download_button(
        label="⬇️ Baixar Tabela em Excel (.xlsx)",
        data=excel_bytes,
        file_name="resumo_ano_mes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ----------------------------------------------------
    # 7) GRÁFICOS — um por item da tabela (BARRAS) (SEM AREA_PRODU)
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="section-title">Gráficos por Ano/Mês</div>', unsafe_allow_html=True)

    chart_df = resumo_mes.copy()
    chart_df["DATA_REF"] = pd.to_datetime(chart_df["Ano/Mês"] + "-01", errors="coerce")
    chart_df = chart_df.sort_values("DATA_REF").copy()

    cols_plot = [
        c for c in chart_df.columns
        if c not in ["Ano/Mês", "DATA_REF", "AREA_PRODU"]
    ]

    for col in cols_plot:
        fig = px.bar(
            chart_df.dropna(subset=["DATA_REF"]),
            x="DATA_REF",
            y=col,
            title=col,
        )
        fig.update_layout(xaxis_title="Ano/Mês", yaxis_title=col)
        st.plotly_chart(fig, use_container_width=True)


        
logger.info("App carregado com sucesso.")

