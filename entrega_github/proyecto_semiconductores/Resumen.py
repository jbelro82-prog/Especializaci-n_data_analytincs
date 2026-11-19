"""Página principal del dashboard: resumen del proyecto."""
import numpy as np
import plotly.express as px
import streamlit as st

from utils import COLORES_REGION, fmt, indicadores, leer, nivel_hhi, origen_chips

st.set_page_config(page_title="Dependencia de chips en España", page_icon="🔷", layout="wide")

st.title("¿Existe riesgo de dependencia de proveedores en las importaciones de chips de España?")
st.caption("Previsión de la demanda y selección de proveedores · Importaciones de chips por país de origen "
           "(Datacomex), años completos 2015–2025 · Valor en euros corrientes")

origen = origen_chips()
ind = indicadores(origen)
valor_region = origen.groupby("region")["valor_eur"].sum()
cuota_ue = valor_region.get("UE", 0) / valor_region.sum() * 100

# Cuota de Asia antes y después de la crisis de chips
antes = origen[origen["anio"] <= 2021].groupby("region")["valor_eur"].sum()
despues = origen[origen["anio"] >= 2022].groupby("region")["valor_eur"].sum()
asia_antes = antes["Asia"] / antes.sum() * 100
asia_despues = despues["Asia"] / despues.sum() * 100

# Previsión y reparto (guardados en 4_prevision.ipynb)
prevision = leer("prevision_2026")
kg_2026 = prevision["combinacion"].sum()
reparto = leer("reparto_propuesto")
coste_actual = reparto["coste_actual_eur"].sum()
coste_propuesto = reparto["coste_final_eur"].sum()          # propuesta final: tope 40 % por país y Asia ≤ 15 %
asia_r = reparto["region"] == "Asia"
hhi_kg = lambda kg: ((kg / kg.sum() * 100) ** 2).sum()

# ---- Indicadores clave
st.subheader("Indicadores clave")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Valor importado de chips (2015–2025)", f"{fmt(origen['valor_eur'].sum() / 1e6)} M€")
c2.metric(f"HHI por origen (concentración {nivel_hhi(ind['hhi'])})", fmt(ind["hhi"]))
c3.metric("CR3 (3 primeros países)", f"{fmt(ind['cr3'])} %")
c4.metric("Nº equivalente de proveedores", fmt(ind["n_equivalente"]))

c5, c6, c7, c8 = st.columns(4)
c5.metric("Cuota de la UE en el valor", f"{fmt(cuota_ue)} %")
c6.metric("Cuota de Asia (2022–2025)", f"{fmt(asia_despues)} %",
          f"+{fmt(asia_despues - asia_antes)} puntos frente a 2015–2021", delta_color="inverse")
c7.metric("Previsión de demanda 2026", f"{fmt(kg_2026 / 1e6)} M kg")
c8.metric("Coste de diversificar (frente a hoy)", f"+{fmt((coste_propuesto / coste_actual - 1) * 100)} %")

# ---- Evolución por región
st.subheader("Valor importado de chips por región de origen")
anual = origen.groupby(["anio", "region"], as_index=False)["valor_eur"].sum()
anual["millones_eur"] = anual["valor_eur"] / 1e6
anual["cuota_%"] = anual["valor_eur"] / anual.groupby("anio")["valor_eur"].transform("sum") * 100
fig = px.bar(anual, x="anio", y="millones_eur", color="region", color_discrete_map=COLORES_REGION,
             category_orders={"region": ["UE", "Asia", "resto"]}, text=anual["cuota_%"].map("{:.0f} %".format),
             hover_data={"cuota_%": ":.2f"},
             labels={"anio": "Año", "millones_eur": "Millones de €", "region": "Región", "cuota_%": "% del año"})
fig.update_traces(textposition="inside", insidetextanchor="middle", textfont_size=11)
fig.update_layout(legend_title_text="Región", hovermode="x unified", uniformtext_minsize=10, uniformtext_mode="hide")
fig.update_xaxes(dtick=1)
st.plotly_chart(fig, width="stretch")

# ---- Contexto sectorial (TIO 2022)
st.subheader("Quién usa la electrónica importada en España (Tablas Input-Output 2022, INE)")
tio = leer("tio_cpa26").copy()
tio["cuota_%"] = tio["importado_m_eur"] / tio["importado_m_eur"].sum() * 100
tio["puesto"] = tio["importado_m_eur"].rank(ascending=False, method="min").astype(int)
# Industria manufacturera (NACE 10-33): usa la electrónica como componente para fabricar; el resto, como equipo terminado
nace_inicio = tio["nace"].str.extract(r"^(\d+)")[0].astype(float)
tio["tipo"] = np.where(nace_inicio.between(10, 33), "Industria (componente para fabricar)", "Servicios y otros (equipos terminados)")
tio["sector"] = tio["rama_nombre"].where(tio["rama_nombre"].str.len() <= 45,
                                         tio["rama_nombre"].str[:43].str.rstrip(" ,;") + "…")   # nombre corto
mostrar = tio[(tio["puesto"] <= 15)].sort_values("importado_m_eur")
fig_tio = px.bar(mostrar, x="importado_m_eur", y="sector", orientation="h", color="tipo", hover_name="rama_nombre",
                 text=mostrar["cuota_%"].map("{:.2f} %".format),
                 color_discrete_map={"Industria (componente para fabricar)": "#1f77b4",
                                     "Servicios y otros (equipos terminados)": "#9aa5b8"},
                 hover_data={"cuota_%": ":.2f", "puesto": True, "tipo": False, "sector": False},
                 labels={"importado_m_eur": "Millones de € importados (CPA 26)",
                         "sector": "", "tipo": "", "cuota_%": "% del total", "puesto": "Puesto"})
fig_tio.update_traces(textposition="outside", textfont_size=11, cliponaxis=False)
fig_tio.update_xaxes(range=[0, mostrar["importado_m_eur"].max() * 1.12])
fig_tio.update_yaxes(tickfont_size=11, categoryorder="total ascending")
fig_tio.update_layout(legend=dict(orientation="h", y=-0.25))
st.plotly_chart(fig_tio, width="stretch")
st.caption("Los 15 sectores que más usan, con su % del total importado. CPA 26 incluye ordenadores, móviles y otros "
           "productos electrónicos, no solo chips: los servicios compran sobre todo equipos terminados; la industria los "
           "usa como componente.")

# ---- Hallazgos
st.subheader("Hallazgos principales")
st.markdown(f"""
- **Resultado 1 · Riesgo de dependencia:** por país de origen, la concentración es **{nivel_hhi(ind['hhi'])}**
  (HHI {fmt(ind['hhi'])}; {fmt(ind['n_equivalente'])} proveedores equivalentes), pero el peso de **Asia crece**
  tras la crisis de chips: del {fmt(asia_antes)} % al {fmt(asia_despues)} % del valor (Mann-Whitney, p < 0.05).
- **Resultado 2 · Previsión:** la combinación de seasonal naive, Holt-Winters y XGBoost es el método más preciso;
  prevé **{fmt(kg_2026 / 1e6)} millones de kg** para 2026. El machine learning no mejora a Holt-Winters (H2 no se confirma).
- **Resultado 3 · Proveedores:** la propuesta final reparte la demanda entre 24 países con un tope del 40 % por país
  y del 15 % para Asia: la concentración en kg baja de **muy alta a moderada** (HHI {fmt(hhi_kg(reparto['kg_actual']))} →
  {fmt(hhi_kg(reparto['kg_final']))}) y Asia pasa del {fmt(reparto.loc[asia_r, 'kg_actual'].sum() / reparto['kg_actual'].sum() * 100)} %
  al {fmt(reparto.loc[asia_r, 'kg_final'].sum() / reparto['kg_final'].sum() * 100)} % de los kg, con un coste de
  **+{fmt((coste_propuesto / coste_actual - 1) * 100)} %**. Reducir más Asia concentraría en Alemania: falta capacidad
  fuera de Asia, que es lo que buscan el PERTE Chip y la Chips Act.
""")