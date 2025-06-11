import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Cargar datos
excel = pd.ExcelFile("datos_restaurante_actualizado.xlsx")
ventas = excel.parse("ventas")
ingredientes = excel.parse("ingredientes")
stock = excel.parse("stock")

st.set_page_config(page_title="Gestión Restaurante IA", layout="wide")

st.title("📊 Dashboard Inteligente para Restaurantes")

seccion = st.sidebar.radio("Ir a sección:", ["📈 Predicción de Demanda", "📦 Gestión de Inventario", "🍽️ Menú del Día", "👨‍🍳 Planificación de Personal"])

# =================== PREDICCIÓN DE DEMANDA ===================
if seccion == "📈 Predicción de Demanda":
    st.header("📈 Predicción estimada de platos servidos por día")

    dias = st.selectbox("Selecciona rango de días:", [7, 14, 30])
    hoy = datetime.today()
    fechas = [hoy + timedelta(days=i) for i in range(dias)]

    # Estimar demanda total con variación aleatoria y patrón por día de semana
    base_demanda = {
        "Lunes": 50, "Martes": 55, "Miércoles": 60,
        "Jueves": 65, "Viernes": 80, "Sábado": 100, "Domingo": 90
    }

    demanda = []
    for fecha in fechas:
        dia = fecha.strftime("%A")
        media = base_demanda.get(dia, 60)
        estimado = int(random.gauss(media, 10))  # variación
        demanda.append(max(0, estimado))

    fig = go.Figure(data=go.Scatter(x=fechas, y=demanda, mode='lines+markers', name='Platos estimados'))
    fig.update_layout(title="Demanda Estimada de Platos", xaxis_title="Fecha", yaxis_title="Nº de platos", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# =================== GESTIÓN DE INVENTARIO ===================
elif seccion == "📦 Gestión de Inventario":
    st.header("📦 Estado de Ingredientes")

    hoy = datetime.today()
    stock["fecha_caducidad"] = pd.to_datetime(stock["fecha_caducidad"])
    stock["estado"] = "✅ OK"

    # Marcar problemas
    stock.loc[stock["stock_actual"] < stock["stock_minimo"], "estado"] = "🔴 Bajo stock"
    stock.loc[(stock["fecha_caducidad"] - hoy).dt.days < 2, "estado"] = "🟠 Próximo a caducar"

    st.dataframe(stock.style.applymap(
        lambda val: 'background-color: #ffcccc' if val == '🔴 Bajo stock' else ('background-color: #fff3cd' if val == '🟠 Próximo a caducar' else ''),
        subset=['estado']
    ))

# =================== MENÚ DEL DÍA ===================
elif seccion == "🍽️ Menú del Día":
    st.header("🍽️ Recomendación de menú para hoy")

    hoy = datetime.today()
    dia_semana = hoy.strftime("%A")

    # Buscar platos que pueden hacerse según stock
    platos_recomendables = []
    for plato in ingredientes["plato"].unique():
        ingredientes_plato = ingredientes[ingredientes["plato"] == plato]
        disponible = True
        for _, row in ingredientes_plato.iterrows():
            ing = row["ingrediente"]
            cantidad = row["cantidad_por_plato"]
            ing_stock = stock[stock["ingrediente"] == ing]
            if ing_stock.empty or ing_stock.iloc[0]["stock_actual"] < cantidad or ing_stock.iloc[0]["fecha_caducidad"] < hoy + timedelta(days=1):
                disponible = False
                break
        if disponible:
            platos_recomendables.append(plato)

    if platos_recomendables:
        st.success("Menú sugerido (según stock y caducidad):")
        for plato in platos_recomendables[:3]:
            st.markdown(f"- 🍽️ **{plato}**")
    else:
        st.error("No hay platos recomendables hoy por falta de stock o caducidad cercana.")

# =================== PERSONAL ===================
elif seccion == "👨‍🍳 Planificación de Personal":
    st.header("👨‍🍳 Recomendación de personal según demanda")

    dias = 7
    hoy = datetime.today()
    fechas = [hoy + timedelta(days=i) for i in range(dias)]
    base_demanda = {
        "Lunes": 50, "Martes": 55, "Miércoles": 60,
        "Jueves": 65, "Viernes": 80, "Sábado": 100, "Domingo": 90
    }

    resumen = []
    for fecha in fechas:
        dia = fecha.strftime("%A")
        estimado = int(random.gauss(base_demanda.get(dia, 60), 10))
        clientes = max(0, estimado)
        cocineros = max(1, clientes // 30)
        camareros = max(1, clientes // 20)
        resumen.append({
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Día": dia,
            "Clientes estimados": clientes,
            "Cocineros": cocineros,
            "Camareros": camareros
        })

    st.dataframe(pd.DataFrame(resumen))


