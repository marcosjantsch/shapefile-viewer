# tabs/tab_mapa.py
import numpy as np
import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
from core.settings import MAX_FEATURES_FULL_MAP


def render_tab_mapa(gdf_full, gdf_filtered, filtro):
    st.markdown('<div class="section-title">Mapa Principal</div>', unsafe_allow_html=True)

    gdf_map = gdf_filtered if st.session_state.get("aplicar", False) else gdf_full
    tipo_exib = filtro["tipo_dado"] if st.session_state.get("aplicar", False) else "Todos os Dados"

    if gdf_map is None or gdf_map.empty:
        st.info("Nenhuma geometria disponível para exibição no mapa.")
        return

    usar_geometria_original = st.checkbox(
        "Exibir polígonos sem simplificação",
        value=False,
        key="mapa_sem_simplificacao",
        help="Mostra as geometrias originais do shapefile. Pode deixar o mapa mais pesado."
    )

    gdf_map = gdf_map.copy()

    if usar_geometria_original and "__geometry_original__" in gdf_map.columns:
        gdf_map["geometry"] = gdf_map["__geometry_original__"]

    area_total_mapa = (
        float(pd.to_numeric(gdf_map["AREA_T"], errors="coerce").sum())
        if "AREA_T" in gdf_map.columns else np.nan
    )
    area_produ_mapa = (
        float(pd.to_numeric(gdf_map["AREA_PRODU"], errors="coerce").sum())
        if "AREA_PRODU" in gdf_map.columns else np.nan
    )
    n_municipios = (
        int(gdf_map["MUNICIPIO"].dropna().astype(str).nunique())
        if "MUNICIPIO" in gdf_map.columns else 0
    )
    n_fazendas = (
        int(gdf_map["FAZENDA"].dropna().astype(str).nunique())
        if "FAZENDA" in gdf_map.columns else 0
    )
    n_feicoes = len(gdf_map)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Fazendas", str(n_fazendas))
    c2.metric("Área total (ha)", f"{area_total_mapa:.1f}" if pd.notna(area_total_mapa) else "N/A")
    c3.metric("Área produtiva (ha)", f"{area_produ_mapa:.1f}" if pd.notna(area_produ_mapa) else "N/A")
    c4.metric("Municípios", str(n_municipios))
    c5.metric("Feições", f"{n_feicoes:,}".replace(",", "."))

    if len(gdf_map) > MAX_FEATURES_FULL_MAP:
        st.warning(f"⚠️ Muitas feições ({len(gdf_map)}). Renderizando apenas {MAX_FEATURES_FULL_MAP}.")
        gdf_map = gdf_map.head(MAX_FEATURES_FULL_MAP)

    m = folium.Map(tiles=None, control_scale=True)
    bounds = gdf_map.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", show=True).add_to(m)
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri World Imagery",
        show=False,
    ).add_to(m)

    color_map = {
        "Todos os Dados": "#DFF500",
        "Dados por Estado": "#F500B4",
        "Dados por Empresa": "#00C4F5",
        "Dados Empresa/Fazenda": "#FF3B30",
        "Dados por Município": "#F5C400",
    }
    color = color_map.get(tipo_exib, "#3388ff")

    for col in ["AREA_T", "AREA_PRODU"]:
        if col in gdf_map.columns:
            gdf_map[col] = pd.to_numeric(gdf_map[col], errors="coerce").round(1)

    if "AREA_T" in gdf_map.columns:
        gdf_map["AREA_T_TXT"] = gdf_map["AREA_T"].apply(
            lambda x: f"{x:.1f} ha" if pd.notna(x) else "N/A"
        )

    if "AREA_PRODU" in gdf_map.columns:
        gdf_map["AREA_PRODU_TXT"] = gdf_map["AREA_PRODU"].apply(
            lambda x: f"{x:.1f} ha" if pd.notna(x) else "N/A"
        )

    tooltip_fields = [
        c for c in ["UF", "MUNICIPIO", "EMPRESA", "FAZENDA", "AREA_T_TXT", "AREA_PRODU_TXT"]
        if c in gdf_map.columns
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

    # remove a coluna auxiliar de geometria antes de converter para GeoJSON
    gdf_render = gdf_map.drop(columns=["__geometry_original__"], errors="ignore").copy()

    folium.GeoJson(
        gdf_render.to_json(),
        name="Fazendas",
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
        ),
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    st_folium(
        m,
        width=1400,
        height=620,
        key="mapa_principal",
        returned_objects=[],
    )