import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random
import locale

# Configurar idioma español para días de la semana
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

# Cargar datos
excel = pd.ExcelFile("datos_restaurante_actualizado.xlsx")
ventas = excel.parse("ventas")
ingredientes = excel.parse("ingredientes")
stock = excel.parse("stock")

st.set_page_config(page_title="Restaurante IA", layout="wide")

st.title("🍽️ App Inteligente para Restaurantes")

seccion = st.sidebar.radio("Ir a sección:", ["📊 Predicción de Demanda", "📦 Gestión de Inventario", "📅 Menú Semanal", "👨‍🍳 Planificación de Personal"])

# =================== PREDICCIÓN DE DEMANDA ===================
if seccion == "📊 Predicción de Demanda":
    st.header("📊 Predicción por tipo de plato")

    dias = st.selectbox("Mostrar predicción para:", [7, 14, 30])
    platos = ventas["plato"].unique()
    hoy = datetime.today()
    fechas = [hoy + timedelta(days=i) for i in range(dias)]

    prediccion = []

    for fecha in fechas:
        dia = fecha.strftime("%A")
        for plato in platos:
            base = ventas[ventas["plato"] == plato]["unidades"].mean()
            variacion = random.uniform(0.8, 1.2)
            estimado = int(base * variacion)
            prediccion.append({"Fecha": fecha.date(), "Plato": plato, "Unidades estimadas": estimado})

    pred_df = pd.DataFrame(prediccion)
    fig = px.bar(pred_df, x="Fecha", y="Unidades estimadas", color="Plato", barmode="group", title="Demanda estimada por tipo de plato")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pred_df)

# =================== GESTIÓN DE INVENTARIO ===================
elif seccion == "📦 Gestión de Inventario":
    st.header("📦 Estado del Inventario")

    hoy = datetime.today()
    stock["fecha_caducidad"] = pd.to_datetime(stock["fecha_caducidad"])
    stock["estado"] = "✅ OK"

    stock.loc[stock["stock_actual"] < stock["stock_minimo"], "estado"] = "🔴 Bajo stock"
    stock.loc[(stock["fecha_caducidad"] - hoy).dt.days < 2, "estado"] = "⚠️ Próximo a caducar"
    st.dataframe(stock[["ingrediente", "stock_actual", "stock_minimo", "fecha_caducidad", "estado"]])

# =================== MENÚ SEMANAL ===================
elif seccion == "📅 Menú Semanal":
    st.header("📅 Menú recomendado de lunes a viernes")

    hoy = datetime.today()
    dias_menu = [hoy + timedelta(days=i) for i in range(5)]
    platos_disponibles = []

    for fecha in dias_menu:
        dia_nombre = fecha.strftime("%A")
        disponibles = []
        for plato in ingredientes["plato"].unique():
            necesario = ingredientes[ingredientes["plato"] == plato]
            es_apto = True
            for _, fila in necesario.iterrows():
                ing = fila["ingrediente"]
                cantidad = fila["cantidad_por_plato"]
                fila_stock = stock[stock["ingrediente"] == ing]
                if fila_stock.empty or fila_stock.iloc[0]["stock_actual"] < cantidad or fila_stock.iloc[0]["fecha_caducidad"] < hoy + timedelta(days=1):
                    es_apto = False
                    break
            if es_apto:
                disponibles.append(plato)

        tipo_entrante = [p for p in disponibles if ventas[ventas["plato"] == p]["tipo_plato"].iloc[0] == "entrante"]
        tipo_principal = [p for p in disponibles if ventas[ventas["plato"] == p]["tipo_plato"].iloc[0] == "principal"]
        tipo_postre = [p for p in disponibles if ventas[ventas["plato"] == p]["tipo_plato"].iloc[0] == "postre"] if "postre" in ventas["tipo_plato"].unique() else []

        st.subheader(f"📅 {dia_nombre} ({fecha.strftime('%d/%m')})")
        st.markdown(f"- 🥗 **Entrante:** {tipo_entrante[0] if tipo_entrante else 'No disponible'}")
        st.markdown(f"- 🍛 **Principal:** {tipo_principal[0] if tipo_principal else 'No disponible'}")
        st.markdown(f"- 🍮 **Postre:** {tipo_postre[0] if tipo_postre else 'No disponible'}")

# =================== PLANIFICACIÓN DE PERSONAL ===================
elif seccion == "👨‍🍳 Planificación de Personal":
    st.header("👨‍🍳 Recomendación de Personal según Demanda")

    base = {
        "lunes": 50, "martes": 60, "miércoles": 65,
        "jueves": 70, "viernes": 90, "sábado": 110, "domingo": 95
    }

    datos = []
    for i in range(7):
        fecha = datetime.today() + timedelta(days=i)
        dia = fecha.strftime("%A").lower()
        estimado = int(random.gauss(base.get(dia, 60), 10))
        cocineros = max(1, estimado // 30)
        camareros = max(1, estimado // 20)
        datos.append({
            "Fecha": fecha.strftime("%d/%m/%Y"),
            "Día": fecha.strftime("%A"),
            "Clientes estimados": estimado,
            "Cocineros necesarios": cocineros,
            "Camareros necesarios": camareros
        })

    st.dataframe(pd.DataFrame(datos))


