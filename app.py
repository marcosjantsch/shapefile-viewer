import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os
import pandas as pd
import json
from pathlib import Path
import tempfile
import zipfile

# =========================================
# CONFIG
# =========================================
DEFAULT_PATH = "Shape\GEO.shp"  # ajuste se quiser

st.set_page_config(
    page_title="Visualizador de Shapefile",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================
# HELPERS
# =========================================
def _safe_convert_timestamps(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Converte colunas datetime/object (que possam conter Timestamp) para string, exceto geometry."""
    gdf = gdf.copy()
    for col in gdf.columns:
        if col == "geometry":
            continue
        try:
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].astype(str)
            elif gdf[col].dtype == "object":
                gdf[col] = gdf[col].apply(lambda x: str(x) if pd.notna(x) else None)
        except Exception:
            pass
    return gdf

def _ensure_wgs84(gdf: gpd.GeoDataFrame, fallback_epsg: int = 31982) -> gpd.GeoDataFrame:
    """
    Folium (Leaflet) exige lat/lon (EPSG:4326).
    Se o shape estiver em UTM (ex: EPSG:31982), reprojeta.
    Se CRS vier None, define fallback e reprojeta.
    """
    gdf = gdf.copy()

    if gdf.crs is None:
        # Se o .prj não veio/está ausente, usar fallback (SIRGAS 2000 / UTM 22S = EPSG:31982)
        gdf = gdf.set_crs(epsg=fallback_epsg)

    # Reprojetar para WGS84 (lat/lon)
    try:
        gdf = gdf.to_crs(epsg=4326)
    except Exception as e:
        raise RuntimeError(f"Falha ao reprojetar para EPSG:4326. CRS atual: {gdf.crs}. Erro: {e}")

    return gdf

def gdf_to_geojson_dict(gdf: gpd.GeoDataFrame) -> dict:
    """GeoDataFrame -> dict GeoJSON (para Folium)."""
    return json.loads(gdf.to_json())

@st.cache_data(show_spinner=False)
def load_shapefile_from_path(file_path: str, fallback_epsg: int = 31982) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(file_path)
    gdf = _safe_convert_timestamps(gdf)
    gdf = _ensure_wgs84(gdf, fallback_epsg=fallback_epsg)  # <<<<< ESSENCIAL
    return gdf

@st.cache_data(show_spinner=False)
def load_shapefile_from_upload(uploaded_file, fallback_epsg: int = 31982) -> gpd.GeoDataFrame:
    """
    Aceita:
    - .shp (mas precisa ter os demais arquivos junto no mesmo diretório - difícil via upload)
    - .zip contendo .shp + .shx + .dbf (+ .prj recomendado)
    """
    suffix = Path(uploaded_file.name).suffix.lower()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        if suffix == ".zip":
            zip_path = tmpdir / uploaded_file.name
            zip_path.write_bytes(uploaded_file.getbuffer())

            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(tmpdir)

            shp_files = list(tmpdir.rglob("*.shp"))
            if not shp_files:
                raise RuntimeError("ZIP não contém nenhum arquivo .shp.")
            shp_path = shp_files[0]  # pega o primeiro .shp encontrado
            gdf = gpd.read_file(shp_path)

        elif suffix == ".shp":
            # Upload de .shp sozinho raramente funciona (faltam .dbf/.shx/.prj)
            shp_path = tmpdir / uploaded_file.name
            shp_path.write_bytes(uploaded_file.getbuffer())
            gdf = gpd.read_file(shp_path)
        else:
            raise RuntimeError("Envie um .zip (recomendado) ou .shp.")

        gdf = _safe_convert_timestamps(gdf)
        gdf = _ensure_wgs84(gdf, fallback_epsg=fallback_epsg)  # <<<<< ESSENCIAL
        return gdf

# =========================================
# SIDEBAR
# =========================================
st.sidebar.title("⚙️ Menu Lateral")
st.sidebar.markdown("---")

fallback_epsg = st.sidebar.number_input(
    "EPSG fallback (se CRS vier vazio)",
    value=31982,  # SIRGAS 2000 / UTM 22S
    step=1
)

st.sidebar.subheader("Fonte do Shapefile")
source_mode = st.sidebar.radio("Escolha:", ["Caminho no disco", "Upload (.zip)"], index=0)

gdf = None
load_error = None

try:
    if source_mode == "Caminho no disco":
        file_path = st.sidebar.text_input("Caminho do .shp", value=DEFAULT_PATH)
        if file_path and os.path.exists(file_path):
            gdf = load_shapefile_from_path(file_path, fallback_epsg=fallback_epsg)
        elif file_path:
            st.sidebar.error(f"Arquivo não encontrado: {file_path}")

    else:
        uploaded = st.sidebar.file_uploader("Envie um .zip com o shapefile", type=["zip", "shp"])
        if uploaded is not None:
            gdf = load_shapefile_from_upload(uploaded, fallback_epsg=fallback_epsg)

except Exception as e:
    load_error = str(e)

st.sidebar.markdown("---")

if load_error:
    st.sidebar.error("Erro ao carregar/reprojetar:")
    st.sidebar.write(load_error)

if gdf is not None:
    st.sidebar.success("📍 Dados carregados com sucesso!")
    st.sidebar.write(f"**Total de feições:** {len(gdf)}")
    st.sidebar.write(f"**CRS (após reprojeção):** {gdf.crs}")
else:
    st.sidebar.warning("Nenhum dado carregado ainda.")

# Opções
st.sidebar.subheader("Opções")
show_all = st.sidebar.checkbox("Mostrar todas as feições", value=True)

# =========================================
# MAIN (TABS)
# =========================================
tab1, tab2, tab3 = st.tabs(["🗺️ Mapa Principal", "📊 Informações", "📋 Dados"])

# ===== ABA 1: MAPA =====
with tab1:
    st.header("Mapa Principal")

    if gdf is not None and len(gdf) > 0:
        try:
            # GeoJSON
            geojson_data = gdf_to_geojson_dict(gdf)

            # Mapa base
            m = folium.Map(tiles="OpenStreetMap", zoom_control=True)

            # Bounds em lat/lon (agora correto)
            bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]  => lon/lat
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

            # Popup fields (sem geometry)
            fields = [c for c in gdf.columns if c != "geometry"]

            folium.GeoJson(
                data=geojson_data,
                name="Shapefile",
                style_function=lambda x: {
                    "fillColor": "#00AA00",
                    "color": "#000000",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.5,
                },
                popup=folium.GeoJsonPopup(fields=fields, labels=True),
                tooltip=folium.GeoJsonTooltip(fields=fields[: min(6, len(fields))], labels=True),
            ).add_to(m)

            folium.LayerControl(collapsed=False).add_to(m)

            # Exibir
            st_folium(m, width=1400, height=600)

        except Exception as e:
            st.error(f"Erro ao exibir mapa: {e}")
    else:
        st.info("Carregue um shapefile para ver o mapa.")

# ===== ABA 2: INFO =====
with tab2:
    st.header("Informações do Shapefile")

    if gdf is not None and len(gdf) > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Feições", len(gdf))
        with col2:
            st.metric("CRS (WGS84)", str(gdf.crs))
        with col3:
            st.metric("Tipo de Geometria", ", ".join(map(str, gdf.geometry.type.unique())))

        st.markdown("---")

        st.subheader("Colunas")
        st.write(gdf.columns.tolist())

        st.subheader("Limites Geográficos (lon/lat)")
        bounds = gdf.total_bounds
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Longitude mínima:** {bounds[0]:.6f}")
            st.write(f"**Latitude mínima:** {bounds[1]:.6f}")
        with c2:
            st.write(f"**Longitude máxima:** {bounds[2]:.6f}")
            st.write(f"**Latitude máxima:** {bounds[3]:.6f}")

        st.markdown("---")
        st.subheader("Checagem rápida (centro aproximado)")
        cx = (bounds[0] + bounds[2]) / 2
        cy = (bounds[1] + bounds[3]) / 2
        st.write(f"Centro (lon, lat): ({cx:.6f}, {cy:.6f})")

    else:
        st.info("Nenhum dado carregado.")

# ===== ABA 3: TABELA =====
with tab3:
    st.header("Tabela de Dados")

    if gdf is not None and len(gdf) > 0:
        df_display = gdf.drop(columns=["geometry"], errors="ignore").copy()

        # Garantir datetime -> string (para Streamlit)
        for col in df_display.columns:
            if pd.api.types.is_datetime64_any_dtype(df_display[col]):
                df_display[col] = df_display[col].astype(str)

        st.dataframe(df_display, use_container_width=True, height=420)

        st.markdown("---")
        st.subheader("Estatísticas (colunas numéricas)")
        try:
            st.write(df_display.describe())
        except Exception:
            st.write("Sem colunas numéricas suficientes para estatísticas.")
    else:
        st.info("Nenhum dado carregado.")
