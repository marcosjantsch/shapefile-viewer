# services/climate_service.py
from __future__ import annotations

import io
from datetime import date
from typing import List, Optional

import pandas as pd
import requests
import streamlit as st

from config_urls import get_url_by_year, load_urls
from date_service import parse_date_safe


DEBUG_CLIMATE = True


def _debug_write(msg: str) -> None:
    if DEBUG_CLIMATE:
        st.write(msg)


def _debug_code(value: str, language: str = "") -> None:
    if DEBUG_CLIMATE:
        st.code(value, language=language)


def get_years_in_range(start_date: date, end_date: date) -> List[int]:
    if start_date is None or end_date is None or end_date < start_date:
        return []
    return list(range(start_date.year, end_date.year + 1))


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

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

    out = out.rename(columns={k: v for k, v in rename_map.items() if k in out.columns})

    for c in out.columns:
        if out[c].dtype == "object":
            out[c] = out[c].astype(str).str.strip()

    return out


def _preview_bytes(content: bytes, limit: int = 500) -> str:
    try:
        return content[:limit].decode("utf-8", errors="ignore")
    except Exception:
        return "<não foi possível decodificar prévia>"


def _looks_like_excel(content: bytes, content_type: str) -> bool:
    ct = (content_type or "").lower()

    if "spreadsheetml" in ct or "excel" in ct or "officedocument" in ct:
        return True

    # XLSX é um ZIP; normalmente começa com PK
    if content[:2] == b"PK":
        return True

    # XLS binário antigo
    if content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return True

    return False


def _try_read_excel(content: bytes, year: int) -> Optional[pd.DataFrame]:
    try:
        df = pd.read_excel(io.BytesIO(content))
        if df is None or df.empty:
            _debug_write(f"⚠️ Ano {year}: Excel lido, mas vazio.")
            return None

        df = _normalize_columns(df)
        _debug_write(f"✅ Ano {year}: arquivo lido como Excel com {len(df)} linhas.")
        return df
    except Exception as e:
        _debug_write(f"⚠️ Ano {year}: falha ao ler como Excel -> {e}")
        return None


def _try_read_csv(content: bytes, year: int) -> Optional[pd.DataFrame]:
    encodings = ["utf-8", "utf-8-sig", "latin-1", "iso-8859-1", "cp1252"]
    separators = [";", ",", "\t", "|"]

    for enc in encodings:
        try:
            text = content.decode(enc)
        except Exception:
            continue

        for sep in separators:
            try:
                df = pd.read_csv(
                    io.StringIO(text),
                    sep=sep,
                    engine="python",
                    on_bad_lines="skip",
                )

                if df is None or df.empty or len(df.columns) <= 1:
                    continue

                df = _normalize_columns(df)
                _debug_write(
                    f"✅ Ano {year}: arquivo lido como CSV "
                    f"(encoding={enc}, separador={repr(sep)}) com {len(df)} linhas."
                )
                return df

            except Exception:
                continue

    _debug_write(f"❌ Ano {year}: não foi possível interpretar o conteúdo como CSV.")
    return None


@st.cache_data(show_spinner=False)
def load_csv_from_url_robust(url: str, year: int) -> Optional[pd.DataFrame]:
    try:
        url = str(url).strip().replace("\\", "/")

        # tenta forçar download para links curtos OneDrive
        if "1drv.ms" in url and "download=1" not in url:
            url = url + ("&download=1" if "?" in url else "?download=1")

        _debug_write(f"### 🔎 Ano {year} — diagnóstico de carregamento")
        _debug_write("🔗 URL utilizada:")
        _debug_code(url)

        response = requests.get(
            url,
            timeout=180,
            allow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            },
        )

        _debug_write(f"📡 Status HTTP: {response.status_code}")
        _debug_write(f"🌍 URL final após redirecionamento:")
        _debug_code(response.url)

        content_type = response.headers.get("Content-Type", "N/A")
        content_length = len(response.content or b"")

        _debug_write(f"📄 Content-Type: {content_type}")
        _debug_write(f"📦 Tamanho recebido: {content_length} bytes")

        response.raise_for_status()

        content = response.content or b""
        if not content:
            _debug_write(f"❌ Ano {year}: resposta vazia.")
            return None

        preview = _preview_bytes(content)
        _debug_write("🔍 Prévia do conteúdo recebido:")
        _debug_code(preview)

        preview_lower = preview.lower()

        # detecta HTML para evidenciar problema de link
        if "<html" in preview_lower or "<!doctype html" in preview_lower:
            _debug_write(
                f"❌ Ano {year}: a URL retornou HTML em vez de CSV/Excel. "
                f"Isso indica página de visualização/redirecionamento."
            )
            return None

        # tenta Excel primeiro quando parecer Excel
        if _looks_like_excel(content, content_type):
            df_excel = _try_read_excel(content, year)
            if df_excel is not None and not df_excel.empty:
                return df_excel

        # tenta CSV
        df_csv = _try_read_csv(content, year)
        if df_csv is not None and not df_csv.empty:
            return df_csv

        # fallback: mesmo sem assinatura clara, tenta Excel
        df_excel_fallback = _try_read_excel(content, year)
        if df_excel_fallback is not None and not df_excel_fallback.empty:
            return df_excel_fallback

        _debug_write(f"❌ Ano {year}: conteúdo recebido, mas não foi possível ler como CSV nem Excel.")
        return None

    except requests.exceptions.RequestException as e:
        _debug_write(f"❌ Ano {year}: erro HTTP/rede ao buscar arquivo -> {e}")
        return None
    except Exception as e:
        _debug_write(f"❌ Ano {year}: erro inesperado -> {e}")
        return None


def _apply_date_filters(df_csv: pd.DataFrame, filtro: dict) -> pd.DataFrame:
    if "DATA" not in df_csv.columns:
        st.warning("⚠️ Coluna DATA não encontrada após carregamento.")
        return df_csv

    df_csv = df_csv.copy()
    df_csv["DATA"] = parse_date_safe(df_csv["DATA"])
    total_antes = len(df_csv)

    df_csv = df_csv.dropna(subset=["DATA"]).copy()
    total_depois = len(df_csv)

    if DEBUG_CLIMATE:
        st.write(f"🗓️ DATA convertida com sucesso: {total_depois} de {total_antes} linhas mantidas.")

    if df_csv.empty:
        st.warning("⚠️ Todos os registros foram descartados após converter DATA.")
        return df_csv

    start_period = pd.Period(filtro["start_date"], freq="M")
    end_period = pd.Period(filtro["end_date"], freq="M")

    df_csv["MES_ANO"] = df_csv["DATA"].dt.to_period("M")
    df_csv = df_csv[
        (df_csv["MES_ANO"] >= start_period) &
        (df_csv["MES_ANO"] <= end_period)
    ].copy()

    df_csv["MES_ANO"] = df_csv["MES_ANO"].astype(str)

    if DEBUG_CLIMATE:
        st.write(f"📅 Registros após filtro de período: {len(df_csv)}")

    return df_csv


def _apply_dimension_filters(df_csv: pd.DataFrame, filtro: dict) -> pd.DataFrame:
    tipo = filtro["tipo_dado"]

    if DEBUG_CLIMATE:
        st.write(f"🧭 Tipo de filtro: {tipo}")

    if tipo == "Dados por Estado" and filtro["selected_uf"] and "UF" in df_csv.columns:
        st.write(f"🔹 Filtrando UF = {filtro['selected_uf']}")
        df_csv = df_csv[df_csv["UF"].astype(str) == str(filtro["selected_uf"])]

    elif tipo == "Dados por Empresa" and filtro["selected_empresa"] and "EMPRESA" in df_csv.columns:
        st.write(f"🔹 Filtrando EMPRESA = {filtro['selected_empresa']}")
        df_csv = df_csv[df_csv["EMPRESA"].astype(str) == str(filtro["selected_empresa"])]

    elif (
        tipo == "Dados Empresa/Fazenda"
        and filtro["selected_empresa"]
        and filtro["selected_fazenda"]
        and all(c in df_csv.columns for c in ["EMPRESA", "FAZENDA"])
    ):
        st.write(
            f"🔹 Filtrando EMPRESA = {filtro['selected_empresa']} | "
            f"FAZENDA = {filtro['selected_fazenda']}"
        )
        df_csv = df_csv[
            (df_csv["EMPRESA"].astype(str) == str(filtro["selected_empresa"])) &
            (df_csv["FAZENDA"].astype(str) == str(filtro["selected_fazenda"]))
        ]

    elif (
        tipo == "Dados por Município"
        and filtro["selected_uf"]
        and filtro["selected_municipio"]
        and all(c in df_csv.columns for c in ["UF", "MUNICIPIO"])
    ):
        st.write(
            f"🔹 Filtrando UF = {filtro['selected_uf']} | "
            f"MUNICIPIO = {filtro['selected_municipio']}"
        )
        df_csv = df_csv[
            (df_csv["UF"].astype(str) == str(filtro["selected_uf"])) &
            (df_csv["MUNICIPIO"].astype(str) == str(filtro["selected_municipio"]))
        ]

    else:
        if DEBUG_CLIMATE:
            st.write("ℹ️ Nenhum filtro dimensional adicional aplicado.")

    if DEBUG_CLIMATE:
        st.write(f"📌 Registros após filtros dimensionais: {len(df_csv)}")

    return df_csv


def load_climate_data(filtro):
    df_csv = pd.DataFrame()
    urls = load_urls()
    years = get_years_in_range(filtro["start_date"], filtro["end_date"])
    log_container = filtro["log_container"]

    if not years:
        log_container.warning("⚠️ Intervalo de datas inválido ou vazio.")
        return df_csv

    frames = []

    st.write("## 📂 Diagnóstico dos arquivos climáticos")
    st.write(f"Anos solicitados: {years}")

    for y in years:
        url = get_url_by_year(urls, y)

        if not url:
            log_container.warning(f"⚠️ Sem URL para o ano {y}")
            st.warning(f"⚠️ Ano {y}: URL não encontrada no config_urls.py")
            continue

        df_y = load_csv_from_url_robust(url, y)

        if df_y is None or df_y.empty:
            log_container.warning(f"⚠️ Ano {y} sem dados válidos")
            st.error(f"❌ Ano {y}: arquivo não pôde ser carregado.")
            continue

        st.success(f"✅ Ano {y}: carregado com {len(df_y)} linhas e {len(df_y.columns)} colunas.")
        st.write(f"Colunas do ano {y}: {list(df_y.columns)}")

        frames.append(df_y)
        log_container.success(f"✅ {y}: carregado")

    if not frames:
        st.error("❌ Nenhum arquivo anual foi carregado com sucesso.")
        return pd.DataFrame()

    df_csv = pd.concat(frames, ignore_index=True)
    df_csv = _normalize_columns(df_csv)

    st.write(f"📦 Total concatenado antes de DATA/filtros: {len(df_csv)} registros")

    df_csv = _apply_date_filters(df_csv, filtro)
    if df_csv.empty:
        st.error("❌ Nenhum registro restou após o tratamento de DATA/período.")
        return df_csv

    df_csv = _apply_dimension_filters(df_csv, filtro)

    log_container.info(f"📦 Total final: {len(df_csv)} registros")
    st.write(f"## ✅ Total final após todos os filtros: {len(df_csv)} registros")

    return df_csv
