"""Página 4: selección de proveedores y reparto (resultado 3)."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils import COLORES_REGION, fmt, leer, nivel_hhi

st.set_page_config(page_title="Proveedores", page_icon="🔷", layout="wide")
st.title("Resultado 3 · Selección de proveedores")
st.caption("¿A quién comprar y cuánto a cada uno para reducir el riesgo? Países de origen de los chips, "
           "enero 2023 – diciembre 2025 (sin 2022 por el acopio tras la crisis).")

proveedores = leer("proveedores_puntuados")
demanda = leer("prevision_2026")["combinacion"].sum()

# ---- Matriz ABC-XYZ
st.subheader("Matriz ABC-XYZ: importancia (ABC, €) frente a estabilidad (XYZ, CV de los kg mensuales)")
col_a, col_b = st.columns([2, 1])
fig = px.scatter(proveedores, x="cuota", y="cv", color="region", hover_name="pais", log_x=True, log_y=True,
                 color_discrete_map={**COLORES_REGION, "no especificado": "grey"},
                 hover_data={"clase": True, "cuota": ":.2f", "cv": ":.2f", "region": False},
                 labels={"cuota": "% del valor 2023–2025 (escala log)", "cv": "CV de los kg mensuales (%, escala log)",
                         "region": "Región"})
for umbral in (50, 100):
    fig.add_hline(y=umbral, line_dash="dot", line_color="grey")
fig.update_xaxes(tickvals=[0.0001, 0.001, 0.01, 0.1, 1, 10], ticktext=["0.0001", "0.001", "0.01", "0.1", "1", "10"])
fig.update_yaxes(tickvals=[10, 25, 50, 100, 250, 500], ticktext=["10", "25", "50", "100", "250", "500"])
col_a.plotly_chart(fig, width="stretch")
matriz = pd.crosstab(proveedores["clase_abc"], proveedores["clase_xyz"], margins=True, margins_name="total")
matriz.index.name, matriz.columns.name = "ABC", "XYZ"
col_b.dataframe(matriz, width="stretch")
col_b.markdown("""
- **A / B / C:** primer 80 % del valor / hasta el 95 % / resto.
- **X / Y / Z:** CV ≤ 50 % estable / 50–100 % variable / > 100 % irregular.
- **AX:** Taiwán · **AZ (crítico):** China · **BX:** Tailandia.
""")

# ---- Puntuación
st.subheader("Puntuación ponderada de los 24 candidatos (A + B + CY)")
candidatos = proveedores[proveedores["candidato"]].sort_values("puntuacion", ascending=False)
st.dataframe(candidatos[["posicion", "pais", "region", "clase", "kg_medio_mes", "cv", "eur_kg_mediano", "puntuacion"]],
             hide_index=True, width="stretch",
             column_config={"posicion": "Puesto", "pais": "País", "region": "Región", "clase": "Clase",
                            "kg_medio_mes": st.column_config.NumberColumn("Kg medios al mes", format="%,.2f"),
                            "cv": st.column_config.NumberColumn("CV (%)", format="%.2f"),
                            "eur_kg_mediano": st.column_config.NumberColumn("€/kg mediano", format="%,.2f"),
                            "puntuacion": st.column_config.ProgressColumn("Puntuación (0–100)", format="%.2f",
                                                                         min_value=0, max_value=100)})
st.caption("Cada criterio se pasa a percentil (0–1) dentro de los candidatos y se pondera al 25 %: volumen (más kg), "
           "estabilidad (menos CV), coste (menos €/kg) y riesgo de región (UE = 1, resto = 0.5, Asia = 0).")

# ---- Reparto con topes interactivos
st.subheader(f"Reparto de la demanda prevista para 2026 ({fmt(demanda / 1e6)} M kg)")
col_t1, col_t2 = st.columns(2)
tope = col_t1.slider("Tope por país (% de los kg)", 20, 60, 40, step=5) / 100
tope_asia = col_t2.slider("Tope para Asia (% de los kg; 100 = sin tope)", 5, 100, 15, step=5) / 100
st.caption("Propuesta final (decisión del 17 nov): tope por país 40 % y Asia ≤ 15 %.")

c = candidatos.set_index("pais").copy()
c["limite_kg"] = np.minimum(c["kg_medio_mes"] * 12, tope * demanda)
asia = c["region"] == "Asia"

def reparto_proporcional(c, demanda):
    """Reparte en proporción a la puntuación; quien llega a su límite se queda en él y el resto se reparte."""
    asignado = pd.Series(0.0, index=c.index)
    libres = list(c.index)
    pendiente = demanda
    while pendiente > 1 and libres:
        parte = c.loc[libres, "puntuacion"] / c.loc[libres, "puntuacion"].sum() * pendiente
        excede = parte > c.loc[libres, "limite_kg"] - asignado[libres]
        if excede.any():
            for pais in parte[excede].index:
                pendiente -= c.loc[pais, "limite_kg"] - asignado[pais]
                asignado[pais] = c.loc[pais, "limite_kg"]
                libres.remove(pais)
        else:
            asignado[libres] += parte
            pendiente = 0
    return asignado

def reparto_con_tope_asia(c, demanda, tope_asia):
    """Asia recibe lo que le tocaría sin tope, como máximo el tope; el resto va a los países no asiáticos."""
    sin_tope = reparto_proporcional(c, demanda)
    cupo_asia = min(sin_tope[asia].sum(), tope_asia * demanda)
    asignado = pd.Series(0.0, index=c.index)
    asignado[asia] = reparto_proporcional(c[asia], cupo_asia)
    asignado[~asia] = reparto_proporcional(c[~asia], demanda - cupo_asia)
    return asignado

def hhi(x):
    return ((x / x.sum() * 100) ** 2).sum()

c["kg_propuestos"] = reparto_con_tope_asia(c, demanda, tope_asia)
c["kg_actual"] = c["kg_medio_mes"] / c["kg_medio_mes"].sum() * demanda
cubierto = c["kg_propuestos"].sum()
coste_prop = (c["kg_propuestos"] * c["eur_kg_mediano"]).sum()
coste_act = (c["kg_actual"] * c["eur_kg_mediano"]).sum()

if cubierto < demanda * 0.999:
    st.warning(f"Con estos topes solo se cubren {fmt(cubierto / 1e6)} M kg de {fmt(demanda / 1e6)}: "
               "no hay capacidad suficiente entre los candidatos.")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Asia (% de los kg)", f"{fmt(c.loc[asia, 'kg_propuestos'].sum() / demanda * 100)} %",
          f"hoy: {fmt(c.loc[asia, 'kg_actual'].sum() / demanda * 100)} %", delta_color="off", delta_arrow="off")
m2.metric(f"País con más kg ({c['kg_propuestos'].idxmax()})", f"{fmt(c['kg_propuestos'].max() / demanda * 100)} %",
          f"hoy: {fmt(c['kg_actual'].max() / demanda * 100)} %", delta_color="off", delta_arrow="off")
m3.metric(f"HHI en kg ({nivel_hhi(hhi(c['kg_propuestos']))})", fmt(hhi(c["kg_propuestos"])),
          f"hoy: {fmt(hhi(c['kg_actual']))}", delta_color="off", delta_arrow="off")
m4.metric("Coste del reparto", f"{fmt(coste_prop / 1e6)} M€", f"hoy: {fmt(coste_act / 1e6)} M€",
          delta_color="off", delta_arrow="off")
m5.metric("Coste de diversificar", f"{coste_prop / coste_act * 100 - 100:+.2f} %")

grafico = (c[["region", "kg_actual", "kg_propuestos"]].reset_index()
           .melt(id_vars=["pais", "region"], var_name="escenario", value_name="kg"))
grafico["escenario"] = grafico["escenario"].map({"kg_actual": "Situación actual", "kg_propuestos": "Propuesta"})
grafico["millones_kg"] = grafico["kg"] / 1e6
orden = c.sort_values("kg_propuestos", ascending=False).index.tolist()
fig_r = px.bar(grafico, x="pais", y="millones_kg", color="escenario", barmode="group",
               category_orders={"pais": orden}, color_discrete_sequence=["#bdbdbd", "#d62728"],
               labels={"pais": "", "millones_kg": "Millones de kg", "escenario": ""})
fig_r.add_hline(y=tope * demanda / 1e6, line_dash="dot", line_color="grey",
                annotation_text=f"tope {tope * 100:.0f} %")
st.plotly_chart(fig_r, width="stretch")

# ---- El dilema: reducir Asia concentra en otros países
st.subheader("El dilema: reducir Asia concentra en otros países")
filas = []
for t in [1.0, 0.20, 0.15, 0.10, 0.05]:
    kg = reparto_con_tope_asia(c, demanda, t)
    filas.append({"Tope para Asia": "sin tope" if t == 1.0 else f"{t * 100:.0f} %",
                  "Asia (% kg)": kg[asia].sum() / demanda * 100,
                  "País con más kg (%)": kg.max() / demanda * 100,
                  "HHI en kg": hhi(kg),
                  "Coste frente a hoy (%)": ((kg * c["eur_kg_mediano"]).sum() / coste_act - 1) * 100})
st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch",
             column_config={k: st.column_config.NumberColumn(k, format="%.2f") for k in
                            ["Asia (% kg)", "País con más kg (%)", "HHI en kg", "Coste frente a hoy (%)"]})
st.caption(f"Con el tope por país actual ({tope * 100:.0f} %). Las alternativas no asiáticas son pequeñas: lo que se "
           "quita a Asia va sobre todo a Alemania. En la práctica, el tope recorta a China, el proveedor crítico (AZ).")

st.info("**H3 se confirma con matices:** hay proveedores alternativos para repartir la demanda y reducir la "
        "concentración, pero son pequeños y diversificar encarece la compra. Para reducir también Asia hay que "
        "concentrar más en Alemania: falta capacidad de fabricación fuera de Asia, que es lo que buscan crear el "
        "PERTE Chip y la Chips Act europea.")
st.caption("Regla: cada país recibe una parte proporcional a su puntuación, con tres límites: el tope por país, el tope "
           "para Asia y su capacidad (kg medios al año que ya envió en 2023–2025). Valoración: kg × €/kg mediano. "
           "Situación actual: los mismos kg con las cuotas reales de 2023–2025. **Limitaciones:** todos los kg de chips "
           "se tratan como intercambiables, aunque cada país vende tipos distintos; el €/kg refleja la mezcla de "
           "productos; el origen \"Alemania\" puede incluir chips asiáticos reexpedidos. Es una propuesta orientativa.")