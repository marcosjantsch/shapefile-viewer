# -*- coding: utf-8 -*-
import os
import io
import logging
from datetime import date
from typing import List

import numpy as np
import pandas as pd
import geopandas as gpd
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

from config_urls import load_urls, get_url_by_year

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEO_PATH = "Geo.shp"

# =========================
# SHAPEFILE
# =========================
@st.cache_data
def load_shape(path):
    if not os.path.exists(path):
        return None
    gdf = gpd.read_file(path)
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    return gdf

# =========================
# CSV OTIMIZADO
# =========================
@st.cache_data
def load_csv(url):
    response = requests.get(url)
    content = response.content.decode("utf-8", errors="ignore")

    usecols = [
        "DATA", "EMPRESA", "FAZENDA",
        "AREA_PRODU",
        "PRECIP_CHIRPS_MM",
        "TEMP_MEDIA_C"
    ]

    df = pd.read_csv(io.StringIO(content), usecols=lambda c: c in usecols)
    return df

# =========================
# SIDEBAR
# =========================
st.sidebar.title("Filtros")

start_date = st.sidebar.date_input("Data inicial", date(2020,1,1))
end_date = st.sidebar.date_input("Data final", date.today())

apply = st.sidebar.button("Aplicar")

# =========================
# SHAPE
# =========================
gdf = load_shape(GEO_PATH)

if gdf is None:
    st.error("Shapefile não encontrado")
    st.stop()

# =========================
# MAPA
# =========================
st.title("Mapa")

m = folium.Map()
folium.GeoJson(gdf).add_to(m)

st_folium(m, width=1200, height=500)

# =========================
# CARREGAMENTO OTIMIZADO
# =========================
df_csv = pd.DataFrame()

if apply:
    urls = load_urls()
    years = list(range(start_date.year, end_date.year + 1))

    with st.spinner("Carregando dados..."):
        for y in years:
            url = get_url_by_year(urls, y)

            if not url:
                continue

            try:
                df_y = load_csv(url)

                # 🔥 FILTRO ANTES DE TUDO
                df_y["DATA"] = pd.to_datetime(df_y["DATA"], errors="coerce")
                df_y = df_y.dropna(subset=["DATA"])

                df_y = df_y[
                    (df_y["DATA"].dt.date >= start_date) &
                    (df_y["DATA"].dt.date <= end_date)
                ]

                # 🔥 TIPOS EFICIENTES
                df_y["EMPRESA"] = df_y["EMPRESA"].astype("category")
                df_y["FAZENDA"] = df_y["FAZENDA"].astype("category")

                # 🔥 CONCAT CONTROLADO
                df_csv = pd.concat([df_csv, df_y], ignore_index=True)

                st.sidebar.success(f"{y}: {len(df_y)} registros")

            except Exception as e:
                st.sidebar.error(f"{y}: erro")

# =========================
# RESULTADO
# =========================
if not df_csv.empty:
    st.subheader(f"Total: {len(df_csv)} registros")

    st.dataframe(df_csv)

    # =========================
    # AGREGAÇÃO OTIMIZADA
    # =========================
    resumo = df_csv.groupby("FAZENDA").agg({
        "PRECIP_CHIRPS_MM": "sum",
        "TEMP_MEDIA_C": "mean"
    }).reset_index()

    st.subheader("Resumo por Fazenda")
    st.dataframe(resumo)

else:
    st.info("Nenhum dado carregado")
