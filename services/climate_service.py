# services/climate_service.py
import io
from typing import Optional, List
from datetime import date
import pandas as pd
import requests
import streamlit as st
from config_urls import load_urls, get_url_by_year

def get_years_in_range(start_date: date, end_date: date) -> List[int]:
    if start_date is None or end_date is None or end_date < start_date:
        return []
    return list(range(start_date.year, end_date.year + 1))

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

        if "1drv.ms" in url and "download=1" not in url:
            url = url + ("&download=1" if "?" in url else "?download=1")

        st.write(f"🔗 Ano {year} - URL utilizada:")
        st.code(url)

        response = requests.get(url, timeout=180)

        st.write(f"📡 Status HTTP: {response.status_code}")

        content_type = response.headers.get("Content-Type", "N/A")
        st.write(f"📄 Content-Type: {content_type}")

        content = response.content
        st.write(f"📦 Tamanho do arquivo: {len(content)} bytes")

        # MOSTRAR INÍCIO DO CONTEÚDO (IMPORTANTE)
        try:
            preview = content[:300].decode("utf-8", errors="ignore")
            st.write("🔍 Prévia do conteúdo:")
            st.code(preview)
        except:
            st.write("⚠️ Não foi possível mostrar prévia do conteúdo")

def load_climate_data(filtro):
    df_csv = pd.DataFrame()
    urls = load_urls()
    years = get_years_in_range(filtro["start_date"], filtro["end_date"])
    log_container = filtro["log_container"]

    if not years:
        return df_csv

    frames = []

    for y in years:
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

    if not frames:
        return pd.DataFrame()

    df_csv = pd.concat(frames, ignore_index=True)
    df_csv = _normalize_columns(df_csv)

    if "DATA" in df_csv.columns:
        df_csv["DATA"] = pd.to_datetime(df_csv["DATA"], errors="coerce", dayfirst=True)
        df_csv = df_csv.dropna(subset=["DATA"]).copy()

        start_period = pd.Period(filtro["start_date"], freq="M")
        end_period = pd.Period(filtro["end_date"], freq="M")

        df_csv["MES_ANO"] = df_csv["DATA"].dt.to_period("M")
        df_csv = df_csv[
            (df_csv["MES_ANO"] >= start_period) &
            (df_csv["MES_ANO"] <= end_period)
        ].copy()

        df_csv["MES_ANO"] = df_csv["MES_ANO"].astype(str)

    tipo = filtro["tipo_dado"]

    if tipo == "Dados por Estado" and filtro["selected_uf"] and "UF" in df_csv.columns:
        df_csv = df_csv[df_csv["UF"].astype(str) == str(filtro["selected_uf"])]

    elif tipo == "Dados por Empresa" and filtro["selected_empresa"] and "EMPRESA" in df_csv.columns:
        df_csv = df_csv[df_csv["EMPRESA"].astype(str) == str(filtro["selected_empresa"])]

    elif (
        tipo == "Dados Empresa/Fazenda"
        and filtro["selected_empresa"] and filtro["selected_fazenda"]
        and all(c in df_csv.columns for c in ["EMPRESA", "FAZENDA"])
    ):
        df_csv = df_csv[
            (df_csv["EMPRESA"].astype(str) == str(filtro["selected_empresa"])) &
            (df_csv["FAZENDA"].astype(str) == str(filtro["selected_fazenda"]))
        ]

    elif (
        tipo == "Dados por Município"
        and filtro["selected_uf"] and filtro["selected_municipio"]
        and all(c in df_csv.columns for c in ["UF", "MUNICIPIO"])
    ):
        df_csv = df_csv[
            (df_csv["UF"].astype(str) == str(filtro["selected_uf"])) &
            (df_csv["MUNICIPIO"].astype(str) == str(filtro["selected_municipio"]))
        ]

    log_container.info(f"📦 Total final: {len(df_csv)} registros")
    return df_csv
