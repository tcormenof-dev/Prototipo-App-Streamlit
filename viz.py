import pandas as pd
import streamlit as st
from utils import log_timing

@log_timing
@st.cache_data(show_spinner=False)
def plot_map_from_sql(
    df: pd.DataFrame,
    lat_col: str = "Latitud",
    lon_col: str = "Longitud",
    label_col: str = "CentroPoblado",
    value_col: str = "pct",
    radius: int = 400,
    initial_zoom: float = 5.0,
):
    import pydeck as pdk

    def _color_from_threshold_sql(p):
        if pd.isna(p): return [180, 180, 180]
        if p < 25: return [200, 0, 0]
        if p < 50: return [255, 140, 0]
        if p < 75: return [230, 200, 0]
        return [0, 170, 0]

    data = df.copy()
    data[lat_col] = pd.to_numeric(data[lat_col], errors="coerce")
    data[lon_col] = pd.to_numeric(data[lon_col], errors="coerce")
    data[value_col] = pd.to_numeric(data[value_col], errors="coerce")
    data = data.dropna(subset=[lat_col, lon_col])

    data["__color__"] = data[value_col].apply(_color_from_threshold_sql)

    view_state = pdk.ViewState(
        latitude=float(data[lat_col].mean()),
        longitude=float(data[lon_col].mean()),
        zoom=initial_zoom,
        pitch=0,
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=data,
        get_position=f"[{lon_col}, {lat_col}]",
        get_fill_color="__color__",
        get_radius=radius,
        pickable=True,
        auto_highlight=True,
        stroked=True,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
    )
    tooltip = {
        "html": f"{{{label_col}}}<br/>Cobertura: {{{value_col}}}%",
        "style": {"backgroundColor": "rgba(0,0,0,0.85)", "color": "white"},
    }
    deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)
    st.pydeck_chart(deck, use_container_width=True)
