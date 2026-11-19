"""Página 4: caso de negocio con una empresa ficticia de automoción (resultado 3 aplicado a una empresa)."""
import plotly.express as px
import streamlit as st

from utils import COLORES_REGION, fmt, leer

st.set_page_config(page_title="Caso de negocio", page_icon="🔷", layout="wide")
st.title("Caso de negocio 4 · Una empresa ficticia de automoción")
st.caption("Supuesto ilustrativo: una empresa de automoción que compra una parte de las importaciones españolas de chips "
           "y aplica la propuesta final de reparto (tope del 40 % por país y Asia ≤ 15 %).")

st.markdown("""
**¿Por qué automoción?:** fue uno de los sectores más afectados por la crisis de chips de 2021–2022 (unos 724,000
vehículos menos en 2021 que en 2019 y ERTE para más de 23,000 trabajadores) y usa los chips como componente para fabricar.
""")

reparto = leer("reparto_propuesto")
demanda = reparto["kg_final"].sum()
coste_final = reparto["coste_final_eur"].sum()
coste_actual = reparto["coste_actual_eur"].sum()

# ---- Control: tamaño de la empresa
cuota = st.slider("Cuota de la empresa en las importaciones españolas de chips (%)", 0.5, 5.0, 1.0, step=0.5) / 100
st.caption("Los porcentajes del reparto no cambian con la cuota; solo cambian los kg y los euros.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Kg que necesita en 2026", f"{fmt(demanda * cuota, 0)} kg")
c2.metric("Al mes", f"{fmt(demanda * cuota / 12 / 1e3)} t")
c3.metric("Coste anual del reparto", f"{fmt(coste_final * cuota / 1e6)} M€")
c4.metric("Sobrecoste por diversificar", f"{fmt((coste_final - coste_actual) * cuota / 1e6)} M€ al año",
          f"{(coste_final / coste_actual - 1) * 100:+.2f} % frente a comprar como hoy", delta_color="off", delta_arrow="off")

# ---- A quién comprar y cuánto
empresa = reparto[reparto["kg_final"] > 0].copy()
empresa["cuota_kg_%"] = empresa["kg_final"] / demanda * 100
empresa["kg_al_mes"] = empresa["kg_final"] * cuota / 12
empresa["coste_al_mes_eur"] = empresa["kg_al_mes"] * empresa["eur_kg_mediano"]
empresa = empresa.sort_values("kg_al_mes", ascending=False)

st.subheader("Plan de compras: a quién comprar y cuánto al mes")
col_a, col_b = st.columns([3, 2])
fig = px.bar(empresa.head(12).sort_values("kg_al_mes"), x="kg_al_mes", y="pais", orientation="h", color="region",
             color_discrete_map=COLORES_REGION, labels={"kg_al_mes": "Kg al mes", "pais": "", "region": "Región"})
fig.update_yaxes(categoryorder="total ascending")
col_a.plotly_chart(fig, width="stretch")
por_region = empresa.groupby("region")["cuota_kg_%"].sum().reset_index()
fig_r = px.pie(por_region, names="region", values="cuota_kg_%", color="region", color_discrete_map=COLORES_REGION,
               hole=0.5, title="Peso de cada región (% de los kg)")
col_b.plotly_chart(fig_r, width="stretch")

st.dataframe(empresa[["pais", "region", "cuota_kg_%", "kg_al_mes", "coste_al_mes_eur"]],
             hide_index=True, width="stretch",
             column_config={"pais": "País", "region": "Región",
                            "cuota_kg_%": st.column_config.NumberColumn("% de los kg", format="%.2f"),
                            "kg_al_mes": st.column_config.NumberColumn("Kg al mes", format="%,.0f"),
                            "coste_al_mes_eur": st.column_config.NumberColumn("Coste al mes (€)", format="%,.0f")})

st.info("**Recomendación para la empresa:** comprar a 24 países, sin que ninguno pase del 40 % y con Asia como máximo "
        "en el 15 % de los kg. Reduce la dependencia del proveedor crítico (China) y la concentración, a cambio de un "
        "sobrecoste del 9.80 %. La previsión de 2026 es prudente (se quedó un 14 % corta en enero–agosto): conviene "
        "un stock de seguridad y revisar el plan cada mes.")
st.caption("Supuestos: la empresa se comporta como el total español (sin datos propios, previsión de España × cuota). "
           "Todos los kg de chips se tratan como intercambiables y el coste usa el €/kg mediano de cada país. "
           "Con datos reales de la empresa (ERP) se aplicarían los mismos modelos a su propio histórico.")