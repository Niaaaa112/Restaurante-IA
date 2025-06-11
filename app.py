# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from babel.dates import format_date

# ---------- CONFIGURACION VISUAL ----------
st.set_page_config(page_title="Restaurante IA", layout="wide")

# ---------- CARGA DE DATOS ----------
@st.cache_data

def cargar_datos():
    excel_file = "https://github.com/Niaaaa112/Restaurante-IA/raw/main/datos_restaurante_completo.xlsx"
    excel = pd.ExcelFile(excel_file)
    ventas = pd.read_excel(excel, sheet_name="ventas")
    ingredientes = pd.read_excel(excel, sheet_name="ingredientes")
    stock = pd.read_excel(excel, sheet_name="stock")
    return ventas, ingredientes, stock

ventas, ingredientes, stock = cargar_datos()

# ---------- SIDEBAR ----------
seccion = st.sidebar.selectbox("Selecciona una sección:", [
    "📈 Predicción de Demanda",
    "📦 Inventario",
    "🍽️ Menú del Día",
    "👨‍🍳 Personal",
    "📊 Dashboard Resumen"
])

# ---------- FUNCIONES AUXILIARES ----------
def traducir_dia(fecha):
    return format_date(fecha, format='EEEE', locale='es_ES')

def simular_prediccion(fecha_base, dias):
    dias_pred = []
    platos = ventas["plato"].unique()
    for i in range(dias):
        fecha = fecha_base + timedelta(days=i)
        dia = fecha.weekday()
        festivo = 1 if dia in [5,6] else 0
        clima = np.random.choice(["soleado", "lluvioso", "nublado"])
        for plato in platos:
            base = ventas[ventas["plato"]==plato]["unidades"].mean()
            factor_dia = 1 + (0.1 if dia in [4,5] else -0.05)
            factor_clima = 0.9 if clima == "lluvioso" else 1.0
            pred = max(0, int(base * factor_dia * factor_clima * np.random.uniform(0.8,1.2)))
            dias_pred.append({"fecha": fecha, "plato": plato, "unidades": pred})
    return pd.DataFrame(dias_pred)


# ---------- PREDICCION DEMANDA ----------
if seccion == "📈 Predicción de Demanda":
    st.title("📈 Predicción de Demanda por Plato")
    st.markdown("Predicción realista para los próximos 7 días según el plato.")
    hoy = datetime.today().date()
    df_pred = simular_prediccion(hoy, 7)

    fig = px.bar(df_pred, x="fecha", y="unidades", color="plato", barmode="group",
                 title="Demanda Estimada por Día", height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df_pred.pivot(index="fecha", columns="plato", values="unidades").fillna(0), height=300)


# ---------- INVENTARIO ----------
if seccion == "📦 Inventario":
    st.title("📦 Gestión de Inventario")
    stock["estado"] = np.where(stock["stock_actual"] <= stock["stock_minimo"], "Bajo", "OK")
    resumen = stock["estado"].value_counts().reset_index()
    resumen.columns = ["estado", "cantidad"]

    col1, col2 = st.columns([1,2])
    with col1:
        st.metric("Ingredientes OK", resumen[resumen.estado == "OK"]["cantidad"].values[0])
        st.metric("Ingredientes Bajo Stock", resumen[resumen.estado == "Bajo"]["cantidad"].values[0])

    with col2:
        fig = px.pie(resumen, names="estado", values="cantidad", title="Estado del Inventario",
                     color_discrete_sequence=["#EF553B", "#00CC96"])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Ingredientes críticos")
    criticos = stock[stock.estado == "Bajo"].sort_values("stock_actual")
    st.dataframe(criticos, height=300)


# ---------- MENÚ DEL DÍA ----------
if seccion == "🍽️ Menú del Día":
    st.title("🍽️ Sugerencia de Menús Semanales")
    platos = ventas[["plato", "tipo_plato"]].drop_duplicates()

    dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes"]
    menu = {}
    usados = []
    for dia in dias_semana:
        primer = platos[(platos.tipo_plato == "primer") & (~platos.plato.isin(usados))].sample(1)
        segundo = platos[(platos.tipo_plato == "segundo") & (~platos.plato.isin(usados))].sample(1)
        postre = platos[(platos.tipo_plato == "postre") & (~platos.plato.isin(usados))].sample(1)
        usados += [primer.plato.values[0], segundo.plato.values[0], postre.plato.values[0]]
        menu[dia] = {
            "Primer Plato": primer.plato.values[0],
            "Segundo Plato": segundo.plato.values[0],
            "Postre": postre.plato.values[0]
        }

    df_menu = pd.DataFrame(menu).T
    st.dataframe(df_menu)


# ---------- PLANIFICACION DE PERSONAL ----------
if seccion == "👨‍🍳 Personal":
    st.title("👨‍🍳 Planificación del Personal")
    hoy = datetime.today().date()
    pred = simular_prediccion(hoy, 7)
    resumen = pred.groupby("fecha")["unidades"].sum().reset_index()
    resumen["cocineros"] = (resumen["unidades"] / 40).apply(np.ceil)
    resumen["camareros"] = (resumen["unidades"] / 30).apply(np.ceil)

    st.subheader("Demanda y Personal Recomendado")
    st.dataframe(resumen)

    fig = px.line(resumen, x="fecha", y=["cocineros", "camareros"], markers=True,
                  title="Recomendación de Personal", height=400)
    st.plotly_chart(fig, use_container_width=True)


# ---------- DASHBOARD RESUMEN ----------
if seccion == "📊 Dashboard Resumen":
    st.title("📊 Dashboard General del Restaurante")
    st.markdown("Resumen visual del estado actual")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Platos Vendidos", ventas.unidades.sum())
    with col2:
        st.metric("Ingresos Totales (€)", int(ventas.unidades @ ventas.precio))
    with col3:
        st.metric("Ingredientes en Bajo Stock", stock[stock.stock_actual <= stock.stock_minimo].shape[0])

    st.subheader("Ranking de Platos Más Vendidos")
    top = ventas.groupby("plato")["unidades"].sum().sort_values(ascending=False).head(10)
    fig = px.bar(top, x=top.values, y=top.index, orientation="h", title="Top 10 Platos", height=400)
    st.plotly_chart(fig, use_container_width=True)


