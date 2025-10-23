
import os
import pandas as pd
import streamlit as st
import altair as alt
from utils import log_timing

def _pretty_cp(x):
    import re
    if x is None:
        return ""
    s = str(x).strip()
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    keep_lower = {"de", "del", "la", "las", "los", "y", "e", "o", "u", "al"}
    words = s.split(" ")
    fixed = []
    for i, w in enumerate(words):
        wl = w.lower()
        if wl in keep_lower and i != 0:
            fixed.append(wl)
        else:
            fixed.append(w.capitalize() if not w.isupper() else w)
    return " ".join(fixed)

# --- Local modules ---
from load_data import (
    read_data_flexible,
    build_sql_cache_long,
    q_centros,
    q_map_by_tech,
    q_values_by_tech,
    q_values_by_cp,
    q_values_by_cps,

)

# try to use user's cleaning if available
try:
    from processing import clean_df  # type: ignore
except Exception:
    clean_df = None  # fallback later

st.set_page_config(page_title="Cobertura Móvil (SQL dashboards)", layout="wide")
st.title("Cobertura móvil — Dashboards con SQL")

# -------------------------------
# Sidebar: entrada de datos
# -------------------------------
with st.sidebar:
    st.header("Fuente de datos")
    data_url = st.text_input(
        "URL o ruta local (.xlsx, .csv)",
        value="https://www.datosabiertos.gob.pe/sites/default/files/Porcentaje%20de%20cobertura%20movil%20por%20centro%20poblado%20empresa%20operadora%20y%20tecnolog%C3%ADa_F.xlsx",
        help="Puedes pegar una URL de datos abiertos o un path local. Ejemplo: /path/archivo.xlsx",
    )
    sep = st.text_input("Separador (CSV)", value=",")
    encoding = st.text_input("Encoding (CSV)", value="utf-8")
    st.caption("Para Excel, el separador/encoding no aplica.")

    st.divider()
    st.header("Opciones de rendimiento")
    use_cache_build = st.checkbox("Cachear ETL", value=True)
    st.caption("Mantén activado para no recomputar al cambiar parámetros.")
    st.divider()

if not data_url:
    st.info("Ingresa una URL o ruta local de datos para continuar.")
    st.stop()

# -------------------------------
# Carga RAW + limpieza
# -------------------------------
try:
    raw_df = read_data_flexible(data_url, sep=sep, encoding=encoding)
except Exception as e:
    st.error(f"Error leyendo la fuente: {e}")
    st.stop()

if raw_df is None or raw_df.empty:
    st.error("No se cargaron datos.")
    st.stop()

df_preview = raw_df.copy()

# Usa clean_df del usuario si existe
if callable(clean_df):
    try:
        cl_df = clean_df(raw_df.copy())
    except Exception as e:
        st.warning(f"clean_df falló, usaré el RAW sin limpiar. Detalle: {e}")
        cl_df = raw_df.copy()
else:
    cl_df = raw_df.copy()

if "CentroPoblado" in cl_df.columns:
    cl_df["CentroPoblado"] = cl_df["CentroPoblado"].astype(str).str.strip()

# --------------------------------
# Construir cache largo en SQLite
# --------------------------------
try:
    build_sql_cache_long(cl_df, rebuild=not use_cache_build)
except Exception as e:
    st.error(f"Error construyendo el cache SQL: {e}")
    st.stop()

alt.data_transformers.disable_max_rows()

# --------------------------------
# Auditoría rápida (opcional)
# --------------------------------
with st.expander("Vista previa y descriptivos (auditoría)"):
    st.write("**Preview (10 filas)**")
    st.dataframe(df_preview.head(10), use_container_width=True)
    try:
        st.write("**Columnas y tipos**")
        info_df = pd.DataFrame({
            "columna": df_preview.columns,
            "dtype": [str(df_preview[c].dtype) for c in df_preview.columns],
            "nulos": [int(df_preview[c].isna().sum()) for c in df_preview.columns],
        })
        st.dataframe(info_df, use_container_width=True)
    except Exception:
        pass

# --------------------------------
# Mapas por tecnología (SQL)
# --------------------------------
st.subheader("Mapa por tipo de red")
TECHS = ["2G", "3G", "4G", "5G"]
tech = st.radio("Elige la tecnología", TECHS, horizontal=True, index=2)

map_df = q_map_by_tech(tech)
if map_df.empty:
    st.warning(f"No hay datos georreferenciados para {tech}.")
else:
    # Sanitizar numéricos
    map_df["Latitud"] = pd.to_numeric(map_df["Latitud"], errors="coerce")
    map_df["Longitud"] = pd.to_numeric(map_df["Longitud"], errors="coerce")
    map_df["pct"] = pd.to_numeric(map_df["pct"], errors="coerce")
    map_df = map_df.dropna(subset=["Latitud", "Longitud"])

    try:
        from viz import plot_map_from_sql
        plot_map_from_sql(map_df)
    except Exception as e:
        st.info(f"Usando mapa embebido (viz.plot_map_from_sql no disponible). Detalle: {e}")
        import pydeck as pdk
        def _color_from_threshold_sql(p):
            if pd.isna(p): return [180, 180, 180]
            if p < 25: return [200, 0, 0]
            if p < 50: return [255, 140, 0]
            if p < 75: return [230, 200, 0]
            return [0, 170, 0]
        map_df["__color__"] = map_df["pct"].apply(_color_from_threshold_sql)
        view_state = pdk.ViewState(
            latitude=float(map_df["Latitud"].mean()),
            longitude=float(map_df["Longitud"].mean()),
            zoom=5.0, pitch=0
        )
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[Longitud, Latitud]",
            get_fill_color="__color__",
            get_radius=400, pickable=True, auto_highlight=True,
            stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1,
        )
        tooltip = {"html": "{CentroPoblado}<br/>Cobertura: {pct}%", "style":{"backgroundColor":"rgba(0,0,0,0.85)","color":"white"}}
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip), use_container_width=True)

# --------------------------------
# Estadísticas Generales por Tecnología (SQL)
# --------------------------------
st.subheader("Estadísticas de cobertura por tecnología")
rows = []
for t in TECHS:
    vals = q_values_by_tech(t)["pct"].dropna()
    if vals.empty:
        continue
    rows.append({
        "Tecnología": tech,
        "Media": float(vals.mean()),
        "Mediana": float(vals.median()),
        "Máximo": float(vals.max()),
        "Mínimo": float(vals.min())
    })

if rows:
    stats_df = pd.DataFrame(rows)
    melted = stats_df.melt(id_vars=["Tecnología"], var_name="Métrica", value_name="Cobertura (%)")
    chart = (
        alt.Chart(melted)
        .mark_bar()
        .encode(
            x=alt.X("Métrica:N", title=""),
            y=alt.Y("Cobertura (%):Q", title="Porcentaje"),
            color="Métrica:N",
            column=alt.Column("Tecnología:N", header=alt.Header(titleOrient="bottom", labelOrient="bottom")),
            tooltip=["Tecnología", "Métrica", alt.Tooltip("Cobertura (%):Q", format=".2f")]
        )
        .properties(title="Estadísticas por tecnología", height=300)
    ).interactive()
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No se pudieron calcular estadísticas generales.")

# --------------------------------
# Cobertura por Centro Poblado (SQL)
# --------------------------------
st.subheader("Cobertura por Centro Poblado")
centros = q_centros()
if not centros:
    st.warning("No hay Centros Poblados en la base.")
else:
    cps = st.multiselect("Selecciona uno o varios Centros Poblados", options=centros, format_func=_pretty_cp)
    agg_metric = st.radio("Estadística", ["Media","Mediana","Máximo","Mínimo"], horizontal=True)

    if cps:
        if len(cps) == 1:
            cp_df = q_values_by_cp(cps[0])
        else:
            cp_df = q_values_by_cps(cps)

        if cp_df.empty:
            st.warning("Sin datos para los CP seleccionados.")
        else:
            cp_df["pct"] = pd.to_numeric(cp_df["pct"], errors="coerce")
            grp = cp_df.groupby("tech")["pct"]
            agg_map = {
                "Media": grp.mean(),
                "Mediana": grp.median(),
                "Máximo": grp.max(),
                "Mínimo": grp.min(),
            }
            show = agg_map[agg_metric].reset_index().rename(columns={"tech":"Tecnología", "pct": agg_metric})
            titulo_suffix = f"en {len(cps)} centro(s) poblado(s) seleccionado(s)"
            chart = (
                alt.Chart(show)
                .mark_bar()
                .encode(
                    x=alt.X("Tecnología:N", title="Tecnología"),
                    y=alt.Y(f"{agg_metric}:Q", title=f"{agg_metric} de Cobertura (%)"),
                    tooltip=["Tecnología", alt.Tooltip(agg_metric, format=".2f")]
                )
                .properties(title=f"{agg_metric} por tecnología {titulo_suffix}", height=300)
            ).interactive()
            st.altair_chart(chart, use_container_width=True)

            with st.expander("Ver detalle (filas utilizadas)"):
                if "CentroPoblado" in cp_df.columns:
                    cp_df = cp_df.assign(CentroPobladoPretty=cp_df["CentroPoblado"].apply(_pretty_cp))
                st.dataframe(cp_df, use_container_width=True)