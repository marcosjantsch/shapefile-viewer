import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import warnings

warnings.filterwarnings('ignore')

# =========================================
# 1. CONFIGURAÇÃO
# =========================================
st.set_page_config(
    page_title="Visualizador de Shapefile e Dados Climáticos",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================
# 2. FUNÇÕES AUXILIARES
# =========================================
@st.cache_data
def load_shapefile(file_path):
    """Carrega shapefile com cache e reprojeção WGS84."""
    try:
        gdf = gpd.read_file(file_path)
        if gdf.crs != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')
        return gdf
    except Exception as e:
        st.error(f"Erro ao carregar shapefile: {e}")
        return None

@st.cache_data
def load_csv(file_path):
    """Carrega CSV com detecção automática de codificação e separador."""
    try:
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        
        for encoding in encodings:
            try:
                # Tentar com ponto-e-vírgula
                df = pd.read_csv(file_path, encoding=encoding, sep=';')
                # Remover espaços extras dos nomes das colunas
                df.columns = df.columns.str.strip()
                # Limpar dados
                df = df.dropna(how='all')
                df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
                return df
            except:
                try:
                    # Tentar com vírgula
                    df = pd.read_csv(file_path, encoding=encoding, sep=',')
                    df.columns = df.columns.str.strip()
                    df = df.dropna(how='all')
                    df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
                    return df
                except:
                    continue
        
        st.error("Não foi possível detectar a codificação do arquivo CSV")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")
        return None

def validate_columns(df, required_cols, df_name="DataFrame"):
    """Valida se as colunas obrigatórias existem."""
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.warning(f"Colunas ausentes no {df_name}: {', '.join(missing_cols)}")
        return False
    return True

def convert_timestamps(df):
    """Converte timestamps para string."""
    df_copy = df.copy()
    for col in df_copy.select_dtypes(include=['datetime64[ns]']).columns:
        df_copy[col] = df_copy[col].astype(str)
    return df_copy

def generate_map(gdf_filtered, tipo_exibicao):
    """Gera mapa Folium com cores dinâmicas."""
    if gdf_filtered.empty:
        return folium.Map(location=[-15.0, -55.0], zoom_start=4)
    
    m = folium.Map()
    bounds = gdf_filtered.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    
    color_map = {
        'Todos os Dados': 'gray',
        'Dados por Estado': 'green',
        'Dados por Empresa': 'blue',
        'Dados Empresa/Fazenda': 'red',
        'Dados por Município': 'orange'
    }
    color = color_map.get(tipo_exibicao, 'blue')
    
    for _, row in gdf_filtered.iterrows():
        geom = row.geometry
        popup_text = (
            f"<b>UF:</b> {row.get('UF', 'N/A')}<br>"
            f"<b>Município:</b> {row.get('MUNICIPIO', 'N/A')}<br>"
            f"<b>Empresa:</b> {row.get('EMPRESA', 'N/A')}<br>"
            f"<b>Fazenda:</b> {row.get('FAZENDA', 'N/A')}"
        )
        
        folium.GeoJson(
            geom,
            style_function=lambda x: {
                'fillColor': color,
                'color': color,
                'weight': 1,
                'fillOpacity': 0.6
            },
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row.get('UF', 'N/A')} - {row.get('FAZENDA', 'N/A')}"
        ).add_to(m)
    
    return m

def calculate_metrics(gdf_filtered):
    """Calcula métricas do GeoDataFrame."""
    num_features = len(gdf_filtered)
    num_ufs = gdf_filtered['UF'].nunique() if 'UF' in gdf_filtered.columns else 0
    num_empresas = gdf_filtered['EMPRESA'].nunique() if 'EMPRESA' in gdf_filtered.columns else 0
    num_fazendas = gdf_filtered['FAZENDA'].nunique() if 'FAZENDA' in gdf_filtered.columns else 0
    num_municipios = gdf_filtered['MUNICIPIO'].nunique() if 'MUNICIPIO' in gdf_filtered.columns else 0
    return num_features, num_ufs, num_empresas, num_fazendas, num_municipios

def add_logo_sidebar():
    """Exibe logo na sidebar."""
    logo_path = 'logo.gif'
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)

def init_session_state():
    """Inicializa session state."""
    if 'tipo_dado' not in st.session_state:
        st.session_state.tipo_dado = 'Todos os Dados'
    if 'uf_filter' not in st.session_state:
        st.session_state.uf_filter = None
    if 'empresa_filter' not in st.session_state:
        st.session_state.empresa_filter = None
    if 'fazenda_filter' not in st.session_state:
        st.session_state.fazenda_filter = None
    if 'municipio_filter' not in st.session_state:
        st.session_state.municipio_filter = None

# =========================================
# 3. CARREGAMENTO DE DADOS
# =========================================
GEO_PATH = 'Shape/Geo.shp'
CSV_PATH = 'Dados.csv'

if not os.path.exists(GEO_PATH):
    st.error(f"Arquivo não encontrado: {GEO_PATH}")
    st.stop()

gdf = load_shapefile(GEO_PATH)
if gdf is None:
    st.stop()

gdf = convert_timestamps(gdf)

# Carregar CSV
df_csv = None
if os.path.exists(CSV_PATH):
    df_csv = load_csv(CSV_PATH)
    if df_csv is not None:
        df_csv = convert_timestamps(df_csv)
else:
    st.warning(f"Arquivo não encontrado: {CSV_PATH}")

init_session_state()

# =========================================
# 4. SIDEBAR
# =========================================
st.sidebar.title("")
add_logo_sidebar()

st.sidebar.markdown("---")
st.sidebar.header("Filtros")

# Selectbox Tipo de Dado
tipo_dado = st.sidebar.selectbox(
    "Tipo de Dado",
    ['Todos os Dados', 'Dados por Estado', 'Dados por Empresa', 'Dados Empresa/Fazenda', 'Dados por Município'],
    key='tipo_dado'
)

st.sidebar.markdown("---")

# Filtros dinâmicos
gdf_filtered = gdf.copy()
tipo_exibicao = tipo_dado
selected_uf = None
selected_empresa = None
selected_fazenda = None
selected_municipio = None

if tipo_dado == 'Dados por Estado':
    uf_options = sorted(gdf['UF'].unique())
    selected_uf = st.sidebar.selectbox("Selecione UF", uf_options)
    gdf_filtered = gdf[gdf['UF'] == selected_uf]
    tipo_exibicao = 'Dados por Estado'

elif tipo_dado == 'Dados por Empresa':
    empresa_options = sorted(gdf['EMPRESA'].unique())
    selected_empresa = st.sidebar.selectbox("Selecione Empresa", empresa_options)
    gdf_filtered = gdf[gdf['EMPRESA'] == selected_empresa]
    tipo_exibicao = 'Dados por Empresa'

elif tipo_dado == 'Dados Empresa/Fazenda':
    empresa_options = sorted(gdf['EMPRESA'].unique())
    selected_empresa = st.sidebar.selectbox("Selecione Empresa", empresa_options)
    
    if selected_empresa:
        fazenda_options = sorted(gdf[gdf['EMPRESA'] == selected_empresa]['FAZENDA'].unique())
        selected_fazenda = st.sidebar.selectbox("Selecione Fazenda", fazenda_options)
        
        gdf_filtered = gdf[
            (gdf['EMPRESA'] == selected_empresa) &
            (gdf['FAZENDA'] == selected_fazenda)
        ]
    tipo_exibicao = 'Dados Empresa/Fazenda'

elif tipo_dado == 'Dados por Município':
    uf_options = sorted(gdf['UF'].unique())
    selected_uf = st.sidebar.selectbox("Selecione UF", uf_options)
    
    if selected_uf:
        municipio_options = sorted(gdf[gdf['UF'] == selected_uf]['MUNICIPIO'].unique())
        selected_municipio = st.sidebar.selectbox("Selecione Município", municipio_options)
        
        gdf_filtered = gdf[
            (gdf['UF'] == selected_uf) &
            (gdf['MUNICIPIO'] == selected_municipio)
        ]
    tipo_exibicao = 'Dados por Município'

st.sidebar.markdown("---")

# Status
st.sidebar.success("✅ Geo.shp carregado!")
st.sidebar.write(f"📊 Total de Feições: {len(gdf)}")
st.sidebar.write(f"🎯 Feições Filtradas: {len(gdf_filtered)}")

if df_csv is not None:
    st.sidebar.success("✅ Dados.csv carregado!")
    st.sidebar.write(f"📊 Total de Registros: {len(df_csv)}")

# =========================================
# 5. ABAS
# =========================================
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa Principal", "📊 Informações", "📋 Dados Shape", "📈 Dados de Clima"])

# ===== ABA 1: MAPA =====
with tab1:
    st.header("Mapa Principal")
    m = generate_map(gdf_filtered, tipo_exibicao)
    st_folium(m, width=1400, height=600)

# ===== ABA 2: INFORMAÇÕES =====
with tab2:
    st.header("Informações")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    num_features, num_ufs, num_empresas, num_fazendas, num_municipios = calculate_metrics(gdf_filtered)
    
    with col1:
        st.metric("Feições", num_features)
    with col2:
        st.metric("UFs", num_ufs)
    with col3:
        st.metric("Empresas", num_empresas)
    with col4:
        st.metric("Fazendas", num_fazendas)
    with col5:
        st.metric("Municípios", num_municipios)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Colunas do Shapefile")
        st.write(list(gdf.columns))
    
    with col2:
        st.subheader("CRS")
        st.write(f"**{gdf.crs}**")
    
    st.markdown("---")
    
    st.subheader("Limites Geográficos (lon/lat)")
    if not gdf_filtered.empty:
        bounds = gdf_filtered.total_bounds
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Longitude mínima:** {bounds[0]:.6f}")
            st.write(f"**Latitude mínima:** {bounds[1]:.6f}")
        with col2:
            st.write(f"**Longitude máxima:** {bounds[2]:.6f}")
            st.write(f"**Latitude máxima:** {bounds[3]:.6f}")

# ===== ABA 3: DADOS SHAPE =====
with tab3:
    st.header("Tabela de Dados (Shapefile)")
    
    if not gdf_filtered.empty:
        df_display = gdf_filtered.drop(columns=['geometry']).copy()
        st.dataframe(df_display, use_container_width=True, height=500)
        
        st.markdown("---")
        st.subheader("Estatísticas")
        try:
            st.write(df_display.describe())
        except Exception:
            st.write("Sem colunas numéricas suficientes para estatísticas.")
    else:
        st.info("Nenhum dado filtrado para exibir.")

# ===== ABA 4: DADOS DE CLIMA =====
with tab4:
    st.header("Dados de Clima")
    
    if df_csv is not None:
        df_filtered_csv = df_csv.copy()
        
        # Aplicar filtros
        if tipo_dado == 'Dados por Estado' and selected_uf and 'UF' in df_filtered_csv.columns:
            df_filtered_csv = df_filtered_csv[df_filtered_csv['UF'] == selected_uf]
        
        elif tipo_dado == 'Dados por Empresa' and selected_empresa and 'EMPRESA' in df_filtered_csv.columns:
            df_filtered_csv = df_filtered_csv[df_filtered_csv['EMPRESA'] == selected_empresa]
        
        elif tipo_dado == 'Dados Empresa/Fazenda' and selected_empresa and selected_fazenda:
            if 'EMPRESA' in df_filtered_csv.columns and 'FAZENDA' in df_filtered_csv.columns:
                df_filtered_csv = df_filtered_csv[
                    (df_filtered_csv['EMPRESA'] == selected_empresa) &
                    (df_filtered_csv['FAZENDA'] == selected_fazenda)
                ]
        
        elif tipo_dado == 'Dados por Município' and selected_uf and selected_municipio:
            if 'UF' in df_filtered_csv.columns and 'MUNICIPIO' in df_filtered_csv.columns:
                df_filtered_csv = df_filtered_csv[
                    (df_filtered_csv['UF'] == selected_uf) &
                    (df_filtered_csv['MUNICIPIO'] == selected_municipio)
                ]
        
        if not df_filtered_csv.empty:
            st.dataframe(df_filtered_csv, use_container_width=True, height=500)
            st.write(f"**Total de registros:** {len(df_filtered_csv)}")
            
            st.markdown("---")
            st.subheader("Estatísticas")
            try:
                st.write(df_filtered_csv.describe())
            except Exception:
                st.write("Sem colunas numéricas suficientes para estatísticas.")
        else:
            st.info("Nenhum dado de clima filtrado para exibir.")
    else:
        st.info("Arquivo Dados.csv não carregado.")
