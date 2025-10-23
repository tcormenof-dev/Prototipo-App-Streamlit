from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, Any
import streamlit as st
from utils import log_timing

@log_timing
@st.cache_data(show_spinner=False)
def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Limpieza básica: strings, tipos, duplicados."""
    # 1) Limpieza de strings: quitar espacios, saltos, etc.
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace("\n", " ")
                .str.replace(r"\s+", " ", regex=True)
                .str.lower()
                .str.replace(" ", "_")
            )


    # 2) Tipos básicos: intentar numérico donde aplique
    for col in df.columns:
        if df[col].dtype == object:
            # intentar parsear como numérico sin romper strings válidas
            coerced = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='ignore')
            if not (coerced.dtype == object):
                df[col] = coerced


    # 3) Duplicados
    df = df.drop_duplicates()
    return df