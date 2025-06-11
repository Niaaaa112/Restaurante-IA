import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import timedelta, datetime
import calendar
import locale

# Establecer idioma en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, '')

st.set_page_config(page_title="Dashboard Restaurante IA", layout="wide")
st.title("🌟 Dashboard Inteligente para Restaurantes")

# Cargar datos desde GitHub
url_excel = "https://github.com/Niaaaa112/Restaurante-IA/raw/refs/heads/main/datos_restaurante_completo.xlsx"
excel = pd.ExcelFile(url_excel)
ventas = pd.read_excel(excel, sheet_name="ventas")
ingredientes = pd.read_excel(excel, sheet_name="ingredientes")
stock = pd.read_excel(excel, sheet_name="stock")

# Preprocesar fechas
ventas["fecha"] = pd.to_datetime(ventas["fecha"])
stock["fecha_caducidad"] = pd.to_datetime(stock["fecha_caducidad"])

# Sidebar de navegación
seccion = st.sidebar.radio("Selecciona una sección:", ["Predicción de Demanda", "Inventario", "Recomendación de Menú", "Planificación de Personal"])

# === PREDICCIÓN DE DEMANDA ===
if seccion == "Predicción de Demanda":
    st.header(":bar_chart: Predicción de Demanda de Platos")

    dias = st.slider("Selecciona días a predecir:", 1, 30, 7)
    fecha_max = ventas["fecha"].max()
    fechas_futuras = [fecha_max + timedelta(days=i) for i in range(1, dias + 1)]

    # Simular predicción de demanda por plato usando promedio y condiciones
    predicciones = []
    for fecha in fechas_futuras:
        dia_semana = calendar.day_name[fecha.weekday()]
        clima = np.random.choice(["soleado", "nublado", "lluvioso"])
        festivo = np.random.choice([0, 1], p=[0.8, 0.2])

        for plato in ventas["plato"].unique():
            demanda_base = ventas[ventas["plato"] == plato]["unidades"].mean()
            ajuste = 1.2 if festivo else 1.0
            ajuste *= 0.9 if clima == "lluvioso" else 1.1 if clima == "soleado" else 1
            predicciones.append({
                "fecha": fecha,
                "plato": plato,
                "dia_semana": dia_semana,
                "clima": clima,
                "festivo": festivo,
                "unidades": int(demanda_base * ajuste + np.random.randint(-2, 2))
            })

    df_pred = pd.DataFrame(predicciones)

    fig = px.bar(df_pred, x="fecha", y="unidades", color="plato",
                 title="Demanda Estimada por Plato",
                 labels={"fecha": "Fecha", "unidades": "Unidades estimadas"})
    st.plotly_chart(fig, use_container_width=True)

# === GESTIÓN DE INVENTARIO ===
elif seccion == "Inventario":
    st.header(":package: Gestión de Inventario")

    # Estado del stock
    def estado_stock(row):
        if row["stock_actual"] <= row["stock_minimo"]:
            return "Bajo"
        elif row["fecha_caducidad"] <= pd.Timestamp.today() + timedelta(days=2):
            return "Pronto a caducar"
        else:
            return "Ok"

    stock["estado"] = stock.apply(estado_stock, axis=1)
    color_estado = {"Bajo": "#ff4d4d", "Pronto a caducar": "#ffa500", "Ok": "#70db70"}

    st.dataframe(stock.style.applymap(lambda v: f"background-color: {color_estado.get(v, '')}; color: white" if v in color_estado else "", subset=["estado"]))

    resumen = stock["estado"].value_counts().reset_index()
    fig = px.pie(resumen, names="index", values="estado", title="Estado del Inventario")
    st.plotly_chart(fig, use_container_width=True)

# === MENÚ DEL DÍA ===
elif seccion == "Recomendación de Menú":
    st.header(":shallow_pan_of_food: Menú Diario Recomendado")

    hoy = pd.Timestamp.today()
    dias_semana = [hoy + timedelta(days=i) for i in range(7) if (hoy + timedelta(days=i)).weekday() < 5]

    menu = {}
    for fecha in dias_semana:
        disponibles = []
        for plato in ingredientes["plato"].unique():
            ingredientes_plato = ingredientes[ingredientes["plato"] == plato]
            suficiente = True
            for _, row in ingredientes_plato.iterrows():
                stock_disp = stock[stock["ingrediente"] == row["ingrediente"]]["stock_actual"].sum()
                if stock_disp < row["cantidad_por_plato"] * 5:  # Para 5 raciones
                    suficiente = False
            if suficiente:
                disponibles.append(plato)

        np.random.shuffle(disponibles)
        menu[fecha.strftime("%A")] = {
            "Primer plato": disponibles[0] if len(disponibles) > 0 else "No disponible",
            "Segundo plato": disponibles[1] if len(disponibles) > 1 else "No disponible",
            "Postre": disponibles[2] if len(disponibles) > 2 else "No disponible"
        }

    st.table(pd.DataFrame(menu).T)

# === PLANIFICACIÓN DE PERSONAL ===
elif seccion == "Planificación de Personal":
    st.header(":busts_in_silhouette: Recomendación de Personal")

    resumen = df_pred.groupby("fecha")["unidades"].sum().reset_index()
    resumen["cocineros"] = (resumen["unidades"] / 20).apply(np.ceil).astype(int)
    resumen["camareros"] = (resumen["unidades"] / 30).apply(np.ceil).astype(int)
    resumen["fecha"] = pd.to_datetime(resumen["fecha"])
    resumen["dia"] = resumen["fecha"].dt.strftime("%A")

    st.dataframe(resumen[["fecha", "dia", "cocineros", "camareros"]])
    fig = px.bar(resumen, x="fecha", y=["cocineros", "camareros"], barmode="group",
                 title="Recomendación de Personal")
    st.plotly_chart(fig, use_container_width=True)

