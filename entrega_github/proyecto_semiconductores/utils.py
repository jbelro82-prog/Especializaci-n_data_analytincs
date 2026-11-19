"""Funciones comunes del dashboard: lectura de las tablas del modelo de datos e indicadores."""
from pathlib import Path

import pandas as pd
import streamlit as st

PROC = Path(__file__).parent / "datos" / "procesados"
FIN = "2025-12-01"                       # periodo común del análisis: años completos 2015-2025

CODIGOS = {"id_pais": str, "partner": str, "codigo": str, "familia": str, "partida": str,
           "rama_codigo": str, "nace": str}
COLORES_REGION = {"UE": "#1f77b4", "Asia": "#d62728", "resto": "#2ca02c"}


@st.cache_data
def leer(nombre):
    """Lee una tabla de datos/procesados: códigos como texto y solo lo vacío como NaN ("NA" = Namibia)."""
    ruta = PROC / f"{nombre}.csv"
    columnas = pd.read_csv(ruta, nrows=0).columns
    return pd.read_csv(ruta, dtype=CODIGOS, keep_default_na=False, na_values=[""],
                       parse_dates=["fecha"] if "fecha" in columnas else False)


@st.cache_data
def origen_chips():
    """Importaciones de chips por país de ORIGEN (Datacomex): países reales, 2015-2025."""
    d = (leer("hechos_origen")
         .merge(leer("dim_producto")[["codigo", "bloque"]], on="codigo")
         .merge(leer("dim_pais_origen")[["id_pais", "pais", "tipo_socio", "ue", "region"]], on="id_pais"))
    d = d[(d["bloque"] == "chips") & (d["tipo_socio"] == "país") & (d["fecha"] <= FIN)].copy()
    d["anio"] = d["fecha"].dt.year
    return d


@st.cache_data
def expedicion_chips():
    """Importaciones de chips por país de EXPEDICIÓN (Comext): socios reales, 2015-2025."""
    d = (leer("hechos_expedicion_es")
         .merge(leer("dim_producto")[["codigo", "bloque"]], on="codigo")
         .merge(leer("dim_socio_comext")[["partner", "nombre", "tipo_socio", "ue"]], on="partner"))
    d = d[(d["bloque"] == "chips") & (d["tipo_socio"] != "no especificado") & (d["fecha"] <= FIN)].copy()
    d["anio"] = d["fecha"].dt.year
    return d.rename(columns={"nombre": "pais"})


def indicadores(d):
    """HHI, CR3 y número equivalente de proveedores a partir del valor (€) por país."""
    cuotas = d.groupby("pais")["valor_eur"].sum()
    cuotas = cuotas / cuotas.sum() * 100
    hhi = (cuotas ** 2).sum()
    return {"hhi": hhi, "cr3": cuotas.nlargest(3).sum(), "n_equivalente": 10_000 / hhi}


def nivel_hhi(hhi):
    """Escala de cuatro niveles (guías de EE. UU. de 2010 y 2023)."""
    if hhi < 1_500:
        return "baja"
    if hhi < 1_800:
        return "moderada"
    if hhi < 2_500:
        return "alta"
    return "muy alta"


def fmt(x, decimales=2):
    """Formato inglés: coma para los miles y punto para los decimales."""
    return f"{x:,.{decimales}f}"