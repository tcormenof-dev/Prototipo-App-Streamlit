
import os
import re
import sqlite3
from typing import Iterable, List, Tuple, Optional
from utils import log_timing

import pandas as pd
import streamlit as st
from utils import log_timing

# ------------------------------------
# Lectura flexible (CSV/Excel)
# ------------------------------------
@log_timing
@st.cache_data(show_spinner=False)
def read_data_flexible(path_or_url: str, sep: str = ",", encoding: str = "utf-8") -> pd.DataFrame:
    import requests, io

    path_or_url = path_or_url.strip()
    if not path_or_url:
        raise ValueError("Ruta/URL vacía.")
    lower = path_or_url.lower()

    # Si es web (https/http)
    if lower.startswith("http"):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0 Safari/537.36"
        }
        resp = requests.get(path_or_url, headers=headers)
        resp.raise_for_status()

        if lower.endswith(".xlsx") or lower.endswith(".xls"):
            return pd.read_excel(io.BytesIO(resp.content))
        else:
            return pd.read_csv(io.BytesIO(resp.content), sep=sep, encoding=encoding)
    else:
        # Lectura local
        if lower.endswith(".xlsx") or lower.endswith(".xls"):
            return pd.read_excel(path_or_url)
        else:
            return pd.read_csv(path_or_url, sep=sep, encoding=encoding)

# ------------------------------------
# SQLite helpers + cache largo
# ------------------------------------
@st.cache_resource(show_spinner=False)
def get_conn(db_path: str = "data/coverage.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
    except Exception:
        pass
    return conn

def _safe_cols(df: pd.DataFrame, candidates: Iterable[str]) -> List[str]:
    return [c for c in candidates if c in df.columns]

@st.cache_data(show_spinner=False)
def build_sql_cache_long(
    df: pd.DataFrame,
    db_path: str = "data/coverage.db",
    table_raw: str = "coverage_raw",
    table_long: str = "coverage_long",
    techs: Optional[List[str]] = None,
    rebuild: bool = False,
):
    """
    1) Guarda RAW.
    2) Precalcula % por tecnología (máx entre operadores) y genera tabla 'larga' (coverage_long).
    3) Crea índices.
    Si rebuild=False y coverage_long ya existe con filas, no rehace nada.
    """
    if techs is None:
        techs = ["2G", "3G", "4G", "5G"]

    conn = get_conn(db_path)

    # Si ya existe y no queremos rebuild, salimos rápido
    if not rebuild:
        try:
            cur = conn.execute(f"SELECT COUNT(1) FROM {table_long};")
            count = cur.fetchone()[0]
            if count and count > 0:
                return  # ya está listo
        except Exception:
            pass

    # 1) Persistir RAW (reemplaza)
    df.to_sql(table_raw, conn, if_exists="replace", index=False)

    # 2) Precalcular por tecnología
    g = df.copy()
    # columnas de contexto frecuentes; ajusta si tu dataset tiene otras
    id_cols = _safe_cols(g, ["CentroPoblado", "Latitud", "Longitud", "Departamento", "Provincia", "Distrito", "Ambito"])

    tech_value_cols = []
    for tech in techs:
        patt = re.compile(rf".*_{tech.upper()}_CG(\+CAR)?$", re.IGNORECASE)
        tech_cols = [c for c in g.columns if patt.match(c)]
        if not tech_cols:
            continue
        for c in tech_cols:
            g[c] = pd.to_numeric(g[c], errors="coerce")
        col_out = f"pct_{tech.upper()}"
        g[col_out] = g[tech_cols].max(axis=1, skipna=True)
        # normaliza a 0-100 si vinieran 0-1
        if pd.notna(g[col_out].mean()) and g[col_out].mean() <= 1:
            g[col_out] = g[col_out] * 100
        tech_value_cols.append(col_out)

    if not tech_value_cols:
        raise ValueError("No se detectaron columnas de cobertura por tecnología en el dataset.")

    long_df = g[id_cols + tech_value_cols].melt(
        id_vars=id_cols,
        value_vars=tech_value_cols,
        var_name="tech_col",
        value_name="pct"
    )
    long_df["tech"] = long_df["tech_col"].str.replace("pct_", "", regex=False).str.upper()
    long_df = long_df.drop(columns=["tech_col"])

    # 3) Persistir LONG + índices
    long_df.to_sql(table_long, conn, if_exists="replace", index=False)
    try:
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_cov_long_cp ON {table_long}(CentroPoblado);")
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_cov_long_tech ON {table_long}(tech);")
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_cov_long_amb ON {table_long}(Ambito);")
        conn.commit()
    except Exception:
        pass

@st.cache_data(show_spinner=False)
def sql_df(query: str, params: Tuple = (), db_path: str = "data/coverage.db") -> pd.DataFrame:
    conn = get_conn(db_path)
    return pd.read_sql_query(query, conn, params=params)

@st.cache_data(show_spinner=False)
def q_centros(db_path: str = "data/coverage.db") -> list:
    df = sql_df(
        "SELECT DISTINCT CentroPoblado FROM coverage_long WHERE CentroPoblado IS NOT NULL ORDER BY 1;",
        db_path=db_path,
    )
    return df["CentroPoblado"].dropna().astype(str).tolist()

@st.cache_data(show_spinner=False)
def q_map_by_tech(tech: str, db_path: str = "data/coverage.db") -> pd.DataFrame:
    return sql_df(
        """
        SELECT CentroPoblado, Latitud, Longitud, pct
        FROM coverage_long
        WHERE tech = ? AND Latitud IS NOT NULL AND Longitud IS NOT NULL
        """,
        (tech.upper(),),
        db_path=db_path,
    )

@st.cache_data(show_spinner=False)
def q_values_by_tech(tech: str, db_path: str = "data/coverage.db") -> pd.DataFrame:
    return sql_df(
        "SELECT pct FROM coverage_long WHERE tech = ?;",
        (tech.upper(),),
        db_path=db_path,
    )

@st.cache_data(show_spinner=False)
def q_values_by_cp(cp: str, db_path: str = "data/coverage.db") -> pd.DataFrame:
    return sql_df(
        "SELECT tech, pct FROM coverage_long WHERE CentroPoblado = ?;",
        (cp,),
        db_path=db_path,
    )

@st.cache_data(show_spinner=False)
def q_values_by_cps(cps: list, db_path: str = "data/coverage.db") -> pd.DataFrame:
    """
    Retorna tech, pct y CentroPoblado para una lista de Centros Poblados.
    """
    if not cps:
        return pd.DataFrame(columns=["tech", "pct", "CentroPoblado"])
    placeholders = ",".join(["?"] * len(cps))
    query = f"""
        SELECT tech, pct, CentroPoblado
        FROM coverage_long
        WHERE CentroPoblado IN ({placeholders})
    """
    return sql_df(query, tuple(cps), db_path=db_path)
