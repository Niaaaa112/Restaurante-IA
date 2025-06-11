# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(page_title="Gestión Restaurante IA", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
    [data-testid="stSidebar"] > div:first-child {
        background-color: #f5f5f5;
    }
    .block-container {
        padding: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# === CARGA DE DATOS ===
file_path = "datos_restaurante_completo.xlsx"
df_ventas = pd.read_excel(file_path, sheet_name="ventas")
df_ingredientes = pd.read_excel(file_path, sheet_name="ingredientes")
df_stock = pd.read_excel(file_path, sheet_name="stock")

# Conversión de fechas
df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])
df_stock["fecha_caducidad"] = pd.to_datetime(df_stock["fecha_caducidad"])

# === MENÚ LATERAL ===
menu = st.sidebar.selectbox("Menú", [
    "Dashboard",
    "Predicción de Demanda",
    "Gestión de Inventario",
    "Menú del Día",
    "Planificación de Personal",
    "Sugerencias de Compra"
])

# === FUNCIÓN: Predicción Simple con variación ===
def predecir_demanda(df, dias=7):
    base = df.groupby("plato")["unidades"].mean().reset_index()
    predicciones = []
    for i in range(dias):
        fecha = datetime.now().date() + timedelta(days=i)
        for _, row in base.iterrows():
            variacion = np.random.normal(1, 0.1)
            predicciones.append({
                "fecha": fecha,
                "plato": row["plato"],
                "prediccion": int(row["unidades"] * variacion)
            })
    return pd.DataFrame(predicciones)

# === FUNCIÓN: Menú Semanal ===
def generar_menu(df_platos, df_stock):
    dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes"]
    menu = []
    usados = []

    for dia in dias_semana:
        dia_menu = {"día": dia.capitalize()}
        for tipo in ["entrante", "principal", "postre"]:
            disponibles = df_platos[(df_platos.tipo_plato == tipo) & (~df_platos.plato.isin(usados))]
            if not disponibles.empty:
                plato_elegido = disponibles.sample(1).iloc[0]
                usados.append(plato_elegido.plato)
                dia_menu[tipo] = plato_elegido.plato
            else:
                dia_menu[tipo] = "No disponible"
        menu.append(dia_menu)
    return pd.DataFrame(menu)

# === FUNCIÓN: Planificación de Personal ===
def planificar_personal(df_pred):
    resumen = df_pred.groupby("fecha")["prediccion"].sum().reset_index()
    resumen["cocineros"] = resumen["prediccion"].apply(lambda x: max(1, x // 40))
    resumen["camareros"] = resumen["prediccion"].apply(lambda x: max(1, x // 30))
    return resumen

# === DASHBOARD ===
if menu == "Dashboard":
    st.title("📊 Dashboard de Resumen")

    col1, col2 = st.columns(2)
    with col1:
        platos_pop = df_ventas.groupby("plato")["unidades"].sum().sort_values(ascending=False).head(5)
        st.metric("🥇 Plato más vendido", platos_pop.idxmax(), f"{platos_pop.max()} uds")
    with col2:
        bajo_stock = df_stock[df_stock["stock_actual"] < df_stock["stock_minimo"]]
        st.metric("⚠️ Ingredientes bajos", len(bajo_stock))

# === PREDICCIÓN DE DEMANDA ===
elif menu == "Predicción de Demanda":
    st.title("📈 Predicción de Demanda (próximos 7 días)")
    df_pred = predecir_demanda(df_ventas)
    grafico = df_pred.groupby(["fecha", "plato"])["prediccion"].sum().reset_index()
    fig = px.bar(grafico, x="fecha", y="prediccion", color="plato", barmode="stack")
    st.plotly_chart(fig, use_container_width=True)

# === INVENTARIO ===
elif menu == "Gestión de Inventario":
    st.title("📦 Gestión de Inventario")
    df_stock["estado"] = df_stock.apply(lambda row: "🟥 Crítico" if row["stock_actual"] < row["stock_minimo"]
                                  else ("🟨 Bajo" if row["stock_actual"] <= row["stock_minimo"] * 1.2 else "🟩 OK"), axis=1)
    st.dataframe(df_stock.style.applymap(lambda x: "color:red" if "🟥" in str(x) else ("color:orange" if "🟨" in str(x) else "color:green"), subset=["estado"]))

    fig = px.bar(df_stock, x="ingrediente", y="stock_actual", color="estado", title="Estado del Inventario")
    st.plotly_chart(fig, use_container_width=True)

# === MENÚ DEL DÍA ===
elif menu == "Menú del Día":
    st.title("🍽️ Menú de la Semana")
    menu_df = generar_menu(df_ventas, df_stock)
    st.dataframe(menu_df.set_index("día"))

# === PERSONAL ===
elif menu == "Planificación de Personal":
    st.title("👨‍🍳 Planificación de Personal")
    df_pred = predecir_demanda(df_ventas)
    plan = planificar_personal(df_pred)
    st.dataframe(plan)

    fig = px.line(plan, x="fecha", y=["cocineros", "camareros"], markers=True)
    st.plotly_chart(fig, use_container_width=True)

# === SUGERENCIAS DE COMPRA ===
elif menu == "Sugerencias de Compra":
    st.title("🛒 Sugerencias de Compra")
    df_stock["necesita_compra"] = df_stock["stock_actual"] < df_stock["stock_minimo"]
    sugerencias = df_stock[df_stock["necesita_compra"]]
    st.dataframe(sugerencias[["ingrediente", "stock_actual", "stock_minimo"]])

    if not sugerencias.empty:
        st.success("Se recomienda reponer los ingredientes listados.")
    else:
        st.info("Todo el inventario está en buen estado.")
