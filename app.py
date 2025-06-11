# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from babel.dates import format_date
from datetime import datetime, timedelta
import locale

# Configuracion de pagina
st.set_page_config(
    page_title="Restaurante IA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS para diseño atractivo y soporte modo claro/oscuro
st.markdown("""
<style>
    body {
        font-family: 'Segoe UI', sans-serif;
    }
    .main {
        background-color: transparent;
    }
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar de navegación
st.sidebar.title("📊 Menú de navegación")
seccion = st.sidebar.radio("Ir a:", [
    "Resumen",
    "📈 Predicción de demanda",
    "📦 Gestión de inventario",
    "📋 Menú del día",
    "👨‍🍳 Planificación de personal"
])

# Cargar datos desde GitHub (debes haber subido correctamente el archivo)
url = "https://github.com/Niaaaa112/Restaurante-IA/raw/main/datos_restaurante_completo.xlsx"
excel = pd.ExcelFile(url)
ventas = pd.read_excel(excel, sheet_name="ventas")
ingredientes = pd.read_excel(excel, sheet_name="ingredientes")
stock = pd.read_excel(excel, sheet_name="stock")

# Preprocesamiento básico
ventas["fecha"] = pd.to_datetime(ventas["fecha"])

# ------------------ SECCIÓN: RESUMEN ------------------
if seccion == "Resumen":
    st.title("📊 Panel de control del restaurante")

    total_ventas = ventas["unidades"].sum()
    total_ingresos = (ventas["unidades"] * ventas["precio"]).sum()
    platos_vendidos = ventas.groupby("plato")["unidades"].sum().sort_values(ascending=False).head(5)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("🍽️ Platos vendidos", f"{total_ventas:,}")
    with col2:
        st.metric("💰 Ingresos totales", f"€{total_ingresos:,.2f}")

    st.subheader("🥇 Top 5 platos más vendidos")
    st.bar_chart(platos_vendidos)

# ------------------ SECCIÓN: PREDICCIÓN ------------------
elif seccion == "📈 Predicción de demanda":
    st.title("📈 Predicción de demanda por plato")

    dias_futuros = 7
    platos = ventas["plato"].unique()
    fechas_futuras = [datetime.today() + timedelta(days=i) for i in range(dias_futuros)]

    predicciones = []
    for fecha in fechas_futuras:
        for plato in platos:
            base = ventas[ventas["plato"] == plato]["unidades"].mean()
            clima = np.random.choice(["soleado", "lluvioso", "nublado"])
            festivo = fecha.weekday() >= 5
            ajuste = 1.2 if clima == "soleado" else 0.9 if clima == "lluvioso" else 1.0
            ajuste *= 1.3 if festivo else 1.0
            estimado = int(np.round(base * ajuste))
            predicciones.append({
                "fecha": fecha.date(),
                "plato": plato,
                "prediccion": estimado
            })
    df_pred = pd.DataFrame(predicciones)

    st.subheader("📅 Selecciona número de días a mostrar")
    dias_opcion = st.selectbox("Días:", [7, 14, 30])
    df_show = df_pred[df_pred["fecha"] <= (datetime.today() + timedelta(days=dias_opcion)).date()]
    fig = px.bar(df_show, x="fecha", y="prediccion", color="plato", title="Demanda estimada de platos")
    st.plotly_chart(fig, use_container_width=True)

# ------------------ SECCIÓN: INVENTARIO ------------------
elif seccion == "📦 Gestión de inventario":
    st.title("📦 Inventario de ingredientes")

    stock["estado"] = np.where(
        stock["stock_actual"] < stock["stock_minimo"], "Bajo", "OK"
    )

    st.dataframe(stock, use_container_width=True)

    resumen_estado = stock["estado"].value_counts().reset_index()
    resumen_estado.columns = ["estado", "cantidad"]
    fig = px.pie(resumen_estado, names="estado", values="cantidad",
                 title="Estado del Inventario", color_discrete_sequence=["red", "green"])
    st.plotly_chart(fig)

# ------------------ SECCIÓN: MENÚ ------------------
elif seccion == "📋 Menú del día":
    st.title("📋 Menú semanal")
    dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes"]

    disponibles = stock[stock["stock_actual"] > stock["stock_minimo"]]
    platos_validos = ingredientes[ingredientes["ingrediente"].isin(disponibles["ingrediente"])]
    platos_disponibles = platos_validos["plato"].unique()
    platos = ventas[ventas["plato"].isin(platos_disponibles)].drop_duplicates("plato")

    for dia in dias_semana:
        usados = []
        primer = platos[(platos.tipo_plato == "primer") & (~platos.plato.isin(usados))].sample(1)
        usados += primer["plato"].tolist()
        segundo = platos[(platos.tipo_plato == "segundo") & (~platos.plato.isin(usados))].sample(1)
        usados += segundo["plato"].tolist()
        postre = platos[(platos.tipo_plato == "postre") & (~platos.plato.isin(usados))].sample(1)

        with st.expander(f"📅 {dia.capitalize()}"):
            st.markdown(f"**Primer plato:** {primer['plato'].values[0] if not primer.empty else 'No disponible'}")
            st.markdown(f"**Segundo plato:** {segundo['plato'].values[0] if not segundo.empty else 'No disponible'}")
            st.markdown(f"**Postre:** {postre['plato'].values[0] if not postre.empty else 'No disponible'}")

# ------------------ SECCIÓN: PERSONAL ------------------
elif seccion == "👨‍🍳 Planificación de personal":
    st.title("👨‍🍳 Planificación del personal")

    demanda_dias = df_pred.groupby("fecha")["prediccion"].sum().reset_index()
    demanda_dias["cocineros"] = (demanda_dias["prediccion"] / 50).apply(np.ceil).astype(int)
    demanda_dias["camareros"] = (demanda_dias["prediccion"] / 30).apply(np.ceil).astype(int)

    for _, row in demanda_dias.iterrows():
        with st.expander(f"📅 {row['fecha'].strftime('%A, %d de %B')} - Estimado: {row['prediccion']} clientes"):
            st.markdown(f"👨‍🍳 Cocineros necesarios: **{row['cocineros']}**")
            st.markdown(f"🧑‍💼 Camareros necesarios: **{row['camareros']}**")
