"""Página 2: riesgo de dependencia (resultado 1)."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils import COLORES_REGION, expedicion_chips, fmt, indicadores, nivel_hhi, origen_chips

st.set_page_config(page_title="Dependencia", page_icon="🔷", layout="wide")
st.title("Resultado 1 · Riesgo de dependencia")
st.caption("¿Cuánto se concentran las importaciones de chips de España y de qué origen son? "
           "Valor en euros corrientes; países reales.")

origen = origen_chips()
expedicion = expedicion_chips()

# ---- Control: periodo
inicio, fin = st.slider("Periodo", 2015, 2025, (2015, 2025))
o = origen[origen["anio"].between(inicio, fin)]
e = expedicion[expedicion["anio"].between(inicio, fin)]
ind_o, ind_e = indicadores(o), indicadores(e)

# ---- Indicadores: origen frente a expedición
st.subheader(f"Concentración {inicio}–{fin}: país de origen frente a país de expedición")
c1, c2, c3 = st.columns(3)
c1.metric("HHI por origen (Datacomex)", fmt(ind_o["hhi"]), f"concentración {nivel_hhi(ind_o['hhi'])}",
          delta_color="off", delta_arrow="off")
c2.metric("HHI por expedición (Comext)", fmt(ind_e["hhi"]), f"concentración {nivel_hhi(ind_e['hhi'])}",
          delta_color="off", delta_arrow="off")
c3.metric("Proveedores equivalentes (origen / expedición)",
          f"{fmt(ind_o['n_equivalente'])} / {fmt(ind_e['n_equivalente'])}")
st.caption("El país de **expedición** es desde donde se envía la mercancía (Alemania y Países Bajos actúan "
           "como distribuidores); el de **origen**, donde se fabricó. Escala del HHI: < 1,500 baja; "
           "1,500–1,800 moderada; 1,800–2,500 alta; > 2,500 muy alta (guías de EE. UU. de 2010 y 2023).")

# ---- HHI por año
def hhi_anual(d):
    cuotas = d.groupby(["anio", "pais"])["valor_eur"].sum()
    cuotas = cuotas / cuotas.groupby("anio").transform("sum") * 100
    return (cuotas ** 2).groupby("anio").sum()

hhi = pd.DataFrame({"Origen (Datacomex)": hhi_anual(o), "Expedición (Comext)": hhi_anual(e)}).reset_index()
hhi = hhi.melt(id_vars="anio", var_name="Fuente", value_name="HHI")
fig = px.line(hhi, x="anio", y="HHI", color="Fuente", markers=True, labels={"anio": "Año"},
              color_discrete_map={"Origen (Datacomex)": "#1f77b4", "Expedición (Comext)": "#ff7f0e"})
for umbral, texto in [(1500, "moderada"), (1800, "alta"), (2500, "muy alta")]:
    fig.add_hline(y=umbral, line_dash="dot", line_color="grey", annotation_text=texto,
                  annotation_position="top left")
fig.update_xaxes(dtick=1)
st.subheader("HHI por año")
st.plotly_chart(fig, width="stretch")

# ---- Cuota por región
st.subheader("Cuota de cada región de origen en el valor importado (%)")
region = o.groupby(["anio", "region"])["valor_eur"].sum()
region = (region / region.groupby("anio").transform("sum") * 100).rename("cuota").reset_index()
fig_r = px.line(region, x="anio", y="cuota", color="region", markers=True, color_discrete_map=COLORES_REGION,
                category_orders={"region": ["UE", "Asia", "resto"]},
                labels={"anio": "Año", "cuota": "% del valor", "region": "Región"})
fig_r.update_xaxes(dtick=1)
st.plotly_chart(fig_r, width="stretch")
st.info("**Prueba U de Mann-Whitney (2015–2025):** la cuota mensual de Asia es mayor en 2022–2025 que en "
        "2015–2021 (mediana 29.78 % → 40.56 %; U = 3,956.00; p = 2.26e-20). El peso de Asia crece tras la "
        "crisis de chips.")

# ---- Principales países y ABC
st.subheader(f"Principales países y análisis ABC ({inicio}–{fin})")
col_a, col_b = st.columns(2)

top_o = (o.groupby("pais")["valor_eur"].sum() / o["valor_eur"].sum() * 100).nlargest(10).rename("cuota")
top_e = (e.groupby("pais")["valor_eur"].sum() / e["valor_eur"].sum() * 100).nlargest(10).rename("cuota")
for col, top, titulo in [(col_a, top_o, "Por origen (Datacomex)"),
                         (col_b, top_e, "Por expedición (Comext; nombres en inglés)")]:
    f = px.bar(top.sort_values().reset_index(), x="cuota", y="pais", orientation="h", title=titulo,
               labels={"cuota": "% del valor", "pais": ""})
    col.plotly_chart(f, width="stretch")

abc = o.groupby(["pais", "region"])["valor_eur"].sum().reset_index().sort_values("valor_eur", ascending=False)
abc["cuota_%"] = abc["valor_eur"] / abc["valor_eur"].sum() * 100
abc["cuota_acumulada_%"] = abc["cuota_%"].cumsum()
anterior = abc["cuota_acumulada_%"] - abc["cuota_%"]
abc["clase"] = np.select([anterior < 80, anterior < 95], ["A", "B"], default="C")
resumen = abc.groupby("clase").agg(paises=("pais", "size"), cuota=("cuota_%", "sum"))

c1, c2, c3 = st.columns(3)
for col, clase in zip([c1, c2, c3], ["A", "B", "C"]):
    col.metric(f"Clase {clase}", f"{resumen.loc[clase, 'paises']} países", f"{fmt(resumen.loc[clase, 'cuota'])} % del valor",
               delta_color="off", delta_arrow="off")
st.caption("ABC (Pareto): A = países que suman el primer 80 % del valor; B = hasta el 95 %; C = el resto.")

tabla = abc[abc["clase"].isin(["A", "B"])].assign(millones_eur=lambda t: t["valor_eur"] / 1e6)
st.dataframe(tabla[["pais", "region", "clase", "millones_eur", "cuota_%", "cuota_acumulada_%"]],
             hide_index=True, width="stretch",
             column_config={"pais": "País", "region": "Región", "clase": "Clase",
                            "millones_eur": st.column_config.NumberColumn("Millones de €", format="%,.2f"),
                            "cuota_%": st.column_config.NumberColumn("Cuota (%)", format="%.2f"),
                            "cuota_acumulada_%": st.column_config.NumberColumn("Cuota acumulada (%)", format="%.2f")})