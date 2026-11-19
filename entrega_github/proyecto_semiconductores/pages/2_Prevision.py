"""Página 3: previsión de la demanda (resultado 2)."""
import plotly.graph_objects as go
import streamlit as st

from utils import fmt, leer

st.set_page_config(page_title="Previsión", page_icon="🔷", layout="wide")
st.title("Resultado 2 · Previsión de la demanda")
st.caption("¿Cuántos kg de chips importará España en 2026? Serie mensual de kg de chips (Datacomex, todos los "
           "orígenes). Los modelos se entrenan con 2015–2025; enero–agosto 2026 (provisional) solo sirve para comprobar.")

prevision = leer("prevision_2026").set_index("fecha")
evaluacion = leer("evaluacion_modelos").set_index("modelo")
NOMBRES = {"seasonal_naive": "Seasonal naive", "holt_winters": "Holt-Winters",
           "xgboost": "XGBoost", "combinacion": "Combinación (elegida)"}
COLORES = {"seasonal_naive": "#7f7f7f", "holt_winters": "#ff7f0e", "xgboost": "#2ca02c", "combinacion": "#d62728"}

# ---- Indicadores
comb = evaluacion.loc["combinacion"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Previsión 2026 (combinación)", f"{fmt(prevision['combinacion'].sum() / 1e6)} M kg")
c2.metric("Real 2025", f"{fmt(prevision.loc['2025', 'kg_real'].sum() / 1e6)} M kg")
c3.metric("MASE de la combinación (origen móvil)", fmt(comb["mase_origen_movil"]))
c4.metric("Error del total enero–agosto 2026", f"{fmt(comb['error_total_%'])} %")

# ---- Gráfico: real y previsiones
st.subheader("Kg reales y previstos")
col_a, col_b = st.columns([1, 3])
desde = col_a.selectbox("Mostrar desde", list(range(2015, 2026)), index=8)
modelos = col_b.multiselect("Modelos", list(NOMBRES), default=["combinacion"], format_func=NOMBRES.get)

real = prevision.loc[f"{desde}-01-01":, "kg_real"].dropna()
fig = go.Figure()
fig.add_scatter(x=real.index, y=real / 1e6, name="Real", line=dict(color="black"))
for m in modelos:
    serie = prevision[m].dropna()
    fig.add_scatter(x=serie.index, y=serie / 1e6, name=NOMBRES[m],
                    line=dict(color=COLORES[m], width=3 if m == "combinacion" else 1.5,
                              dash=None if m == "combinacion" else "dot"))
fig.add_vline(x="2026-01-01", line_dash="dot", line_color="grey")
fig.update_layout(yaxis_title="Millones de kg", xaxis_title="Mes", hovermode="x unified")
st.plotly_chart(fig, width="stretch")

# ---- Evaluación de los modelos
st.subheader("Evaluación de los modelos")
tabla = evaluacion.rename(index=NOMBRES)
st.dataframe(tabla, width="stretch",
             column_config={"modelo": "Modelo",
                            "mase_origen_movil": st.column_config.NumberColumn("MASE origen móvil", format="%.2f"),
                            "mase_2026": st.column_config.NumberColumn("MASE 2026", format="%.2f"),
                            "kg_previstos_ene_ago": st.column_config.NumberColumn("Previstos ene–ago (M kg)", format="%.2f"),
                            "kg_reales_ene_ago": st.column_config.NumberColumn("Reales ene–ago (M kg)", format="%.2f"),
                            "error_total_%": st.column_config.NumberColumn("Error total (%)", format="%.2f")})
st.caption("MASE: error medio de la previsión ÷ error de repetir el mismo mes del año anterior dentro del "
           "entrenamiento (< 1 mejor que esa referencia). Se comparan los modelos entre sí. Los MASE de 2026 son "
           "bajos porque 2026 es un año tranquilo y la escala incluye los años de acopio 2022–2024.")

st.info("**H2 no se confirma:** XGBoost (machine learning) no mejora a Holt-Winters en el origen móvil "
        f"({fmt(evaluacion.loc['xgboost', 'mase_origen_movil'])} frente a "
        f"{fmt(evaluacion.loc['holt_winters', 'mase_origen_movil'])}). La combinación de los tres modelos es la "
        "más precisa en las dos evaluaciones, como en las competiciones de previsión (M4). Con una sola serie corta "
        "y sin variables explicativas, el machine learning no supera a los métodos clásicos.")

with st.expander("Cómo funciona cada modelo"):
    st.markdown("""
- **Seasonal naive:** cada mes = el mismo mes del año anterior. Es el listón mínimo.
- **Holt-Winters:** suavizado exponencial (más peso a los meses recientes) con nivel, tendencia amortiguada y
  estacionalidad de 12 meses, sobre el logaritmo de los kg.
- **XGBoost:** árboles de decisión con *boosting*; aprende de los kg de hace 1, 2, 3, 6 y 12 meses, la media de los
  3 meses anteriores y el mes del año. Prevé mes a mes (recursivo).
- **Combinación:** media de las tres previsiones; los errores de cada modelo se compensan.
- **Evaluación:** MASE en un origen móvil (9 previsiones simuladas a 12 meses entre diciembre 2022 y diciembre 2024)
  y comprobación con los meses reales de 2026.
""")