# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import calendar
from datetime import datetime, timedelta
from babel.dates import format_date

# ---------- CONFIGURACIÓN GENERAL ----------
st.set_page_config(
    page_title="Restaurante Inteligente",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- ESTILOS PERSONALIZADOS ----------
st.markdown("""
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
        }
        .title {
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 20px;
        }
        .card {
            background-color: #f9f9f9;
            padding: 1.2rem;
            border-radius: 1rem;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            margin-bottom: 1.5rem;
        }
        @media (prefers-color-scheme: dark) {
            .card {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        }
    </style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3075/3075977.png", width=100)
st.sidebar.title("📊 Panel de Control")
seccion = st.sidebar.radio("Ir a:", ["Resumen", "Predicción de Demanda", "Gestión de Inventario", "Menú del Día", "Planificación de Personal"])

# ---------- CARGA DE DATOS ----------
@st.cache_data

def cargar_datos():
    url = "https://github.com/Niaaaa112/Restaurante-IA/raw/main/datos_restaurante_completo.xlsx"
    excel = pd.ExcelFile(url)
    ventas = pd.read_excel(excel, "ventas")
    ingredientes = pd.read_excel(excel, "ingredientes")
    stock = pd.read_excel(excel, "stock")
    return ventas, ingredientes, stock

ventas, ingredientes, stock = cargar_datos()

# ---------- FUNCIÓN UTILIDADES ----------
def obtener_dias_proximos(n=7):
    hoy = datetime.today()
    return [(hoy + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]

def clasificar_stock(row):
    if row["stock_actual"] <= row["stock_minimo"]:
        return "Bajo"
    elif row["stock_actual"] < row["stock_minimo"] * 1.5:
        return "Medio"
    else:
        return "Alto"

# ---------- RESUMEN ----------
if seccion == "Resumen":
    st.markdown("<h1 class='title'>📌 Resumen Ejecutivo</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        total_ventas = ventas["unidades"].sum()
        st.metric("Total de Platos Vendidos", total_ventas)

    with col2:
        ingresos = (ventas["unidades"] * ventas["precio"]).sum()
        st.metric("Ingresos Totales (€)", f"{ingresos:,.2f}")

    with col3:
        bajo_stock = stock[stock["stock_actual"] <= stock["stock_minimo"]].shape[0]
        st.metric("Ingredientes en Bajo Stock", bajo_stock)

# ---------- PREDICCIÓN DE DEMANDA ----------
elif seccion == "Predicción de Demanda":
    st.markdown("<h1 class='title'>📈 Predicción de Demanda</h1>", unsafe_allow_html=True)
    dias = st.selectbox("Seleccionar rango de predicción:", [7, 14, 30])

    fechas = obtener_dias_proximos(dias)
    np.random.seed(42)
    predicciones = []
    platos = ventas["plato"].unique()

    for fecha in fechas:
        for plato in platos:
            predicciones.append({
                "fecha": fecha,
                "plato": plato,
                "prediccion": np.random.poisson(lam=5)
            })

    df_pred = pd.DataFrame(predicciones)

    st.write("### Predicción por Plato")
    fig = px.bar(df_pred.groupby(["fecha", "plato"]).sum().reset_index(),
                 x="fecha", y="prediccion", color="plato",
                 labels={"prediccion": "Unidades Previstas"},
                 barmode="stack", height=500)
    st.plotly_chart(fig, use_container_width=True)

# ---------- GESTIÓN DE INVENTARIO ----------
elif seccion == "Gestión de Inventario":
    st.markdown("<h1 class='title'>📦 Gestión de Inventario</h1>", unsafe_allow_html=True)

    stock["estado"] = stock.apply(clasificar_stock, axis=1)
    resumen = stock["estado"].value_counts().reset_index()
    resumen.columns = ["estado", "cantidad"]

    fig = px.pie(resumen, names="estado", values="cantidad",
                 color_discrete_sequence=px.colors.qualitative.Safe,
                 title="Estado General del Stock")
    st.plotly_chart(fig)

    st.write("### Ingredientes en Bajo Stock")
    st.dataframe(stock[stock["estado"] == "Bajo"], use_container_width=True)

# ---------- MENÚ DEL DÍA ----------
elif seccion == "Menú del Día":
    st.markdown("<h1 class='title'>🍽️ Menú Sugerido (Lunes a Viernes)</h1>", unsafe_allow_html=True)
    dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes"]

    platos = ventas.drop_duplicates(subset=["plato", "tipo_plato"])

    for i, dia in enumerate(dias_semana):
        usados = []
        st.markdown(f"#### {dia.title()}")
        col1, col2, col3 = st.columns(3)

        with col1:
            primer = platos[(platos.tipo_plato == "primer") & (~platos.plato.isin(usados))]
            if not primer.empty:
                eleccion = primer.sample(1).iloc[0]
                usados.append(eleccion.plato)
                st.success(eleccion.plato)
            else:
                st.warning("No disponible")

        with col2:
            segundo = platos[(platos.tipo_plato == "segundo") & (~platos.plato.isin(usados))]
            if not segundo.empty:
                eleccion = segundo.sample(1).iloc[0]
                usados.append(eleccion.plato)
                st.info(eleccion.plato)
            else:
                st.warning("No disponible")

        with col3:
            postre = platos[(platos.tipo_plato == "postre") & (~platos.plato.isin(usados))]
            if not postre.empty:
                eleccion = postre.sample(1).iloc[0]
                usados.append(eleccion.plato)
                st.success(eleccion.plato)
            else:
                st.warning("No disponible")

# ---------- PLANIFICACIÓN DE PERSONAL ----------
elif seccion == "Planificación de Personal":
    st.markdown("<h1 class='title'>👨‍🍳 Planificación de Personal</h1>", unsafe_allow_html=True)

    demanda_dias = df_pred.groupby("fecha")["prediccion"].sum().reset_index()
    demanda_dias["cocineros"] = (demanda_dias["prediccion"] / 20).apply(np.ceil)
    demanda_dias["camareros"] = (demanda_dias["prediccion"] / 15).apply(np.ceil)

    fig = px.bar(demanda_dias, x="fecha", y=["cocineros", "camareros"],
                 barmode="group", title="Recomendación de Personal")
    st.plotly_chart(fig, use_container_width=True)

    st.write("### Justificación por Demanda")
    st.dataframe(demanda_dias, use_container_width=True)


