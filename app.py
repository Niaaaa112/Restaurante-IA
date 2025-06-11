# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="IA para Restaurantes", layout="wide")

# Sidebar
st.sidebar.title("📊 Dashboard")
page = st.sidebar.radio("Ir a:", ["Predicción", "Gestión de Inventario", "Menú", "Personal"])

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("📁 Subir archivo Excel", type=["xlsx"])

if uploaded_file:
    # Carga los datos
    ventas = pd.read_excel(uploaded_file, sheet_name="ventas")
    ingredientes = pd.read_excel(uploaded_file, sheet_name="ingredientes")
    stock = pd.read_excel(uploaded_file, sheet_name="stock")

    # Simula una predicción simple por día
    demanda = ventas.groupby("dia_semana")["unidades"].sum().reindex([
        "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
    ])

    if page == "Predicción":
        st.title("🔮 Predicción de Demanda")
        st.write("Estimación de ventas por día de la semana:")

        fig, ax = plt.subplots()
        demanda.plot(kind="line", marker="o", ax=ax)
        ax.set_ylabel("Platos vendidos")
        st.pyplot(fig)

        st.markdown("#### Selecciona un rango")
        st.selectbox("Próximos días", ["7 días", "14 días", "30 días"])

    elif page == "Gestión de Inventario":
        st.title("📦 Gestión de Inventario")
        alertas = stock[stock["stock_actual"] < stock["stock_minimo"]]
        if alertas.empty:
            st.success("✅ No hay alertas de stock bajo.")
        else:
            st.error("⚠️ Ingredientes con stock bajo:")
            st.dataframe(alertas)

    elif page == "Menú":
        st.title("📋 Optimización del Menú")
        top_platos = ventas.groupby("plato")["unidades"].sum().sort_values(ascending=False).head(5)
        st.write("🥇 Platos más populares:")
        st.bar_chart(top_platos)

    elif page == "Personal":
        st.title("🧑‍🍳 Planificación del Personal")
        st.write("Sugerencia: Aumentar personal en días con alta demanda (viernes a domingo).")
        st.line_chart(demanda)

else:
    st.warning("📌 Por favor, sube el archivo Excel con los datos del mes.")
