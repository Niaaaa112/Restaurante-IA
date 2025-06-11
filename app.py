import streamlit as st
import pandas as pd
import numpy as np
import datetime
import calendar
import requests
from io import BytesIO
from babel.dates import format_date

# Configuración de la página
st.set_page_config(page_title="Restaurante IA", layout="wide")
st.title("🍽️ Panel Inteligente para Restaurantes")

# Cargar datos desde GitHub
url_excel = "https://github.com/Niaaaa112/Restaurante-IA/raw/refs/heads/main/datos_restaurante_completo.xlsx"
response = requests.get(url_excel)
excel_file = BytesIO(response.content)

ventas = pd.read_excel(excel_file, sheet_name="ventas")
ingredientes = pd.read_excel(excel_file, sheet_name="ingredientes")
stock = pd.read_excel(excel_file, sheet_name="stock")
festivos = pd.read_excel(excel_file, sheet_name="festivos")
clima = pd.read_excel(excel_file, sheet_name="clima")

stock['fecha_caducidad'] = pd.to_datetime(stock['fecha_caducidad'])
futuro = pd.date_range(datetime.date.today(), periods=7)

# Sidebar para navegación
seccion = st.sidebar.radio("Selecciona una sección:", [
    "📈 Predicción de Demanda",
    "📦 Gestión de Inventario",
    "🍽️ Recomendación de Menú",
    "👨‍🍳 Planificación de Personal",
])

# -------- PREDICCIÓN DE DEMANDA --------
if seccion == "📈 Predicción de Demanda":
    st.header("📈 Predicción de Demanda por Plato")
    dias_opciones = st.radio("Ver predicción para:", [7, 14, 30], horizontal=True)

    prediccion = []
    for fecha in pd.date_range(datetime.date.today(), periods=dias_opciones):
        dia = fecha.strftime("%A")
        clima_dia = clima.loc[clima['fecha'] == fecha.date(), 'clima'].values
        clima_factor = 1.2 if clima_dia == 'soleado' else 1.0
        festivo = fecha.date() in pd.to_datetime(festivos['fecha']).dt.date.values
        festivo_factor = 1.3 if festivo else 1.0

        for plato in ventas['plato'].unique():
            base = ventas[ventas['plato'] == plato]['unidades'].mean()
            estimado = int(base * clima_factor * festivo_factor + np.random.normal(0, 2))
            prediccion.append({"Fecha": fecha, "Plato": plato, "Unidades Estimadas": max(0, estimado)})

    df_pred = pd.DataFrame(prediccion)
    st.dataframe(df_pred, use_container_width=True)

    st.bar_chart(df_pred.pivot_table(index="Fecha", columns="Plato", values="Unidades Estimadas", aggfunc="sum"))

# -------- GESTIÓN DE INVENTARIO --------
elif seccion == "📦 Gestión de Inventario":
    st.header("📦 Gestión de Inventario")

    def estado(stock_act, stock_min):
        if stock_act < stock_min:
            return "🔴 Bajo"
        elif stock_act < stock_min * 1.5:
            return "🟠 Medio"
        else:
            return "🟢 Óptimo"

    stock['estado'] = stock.apply(lambda row: estado(row['stock_actual'], row['stock_minimo']), axis=1)
    caducan_pronto = stock[stock['fecha_caducidad'] <= datetime.datetime.today() + datetime.timedelta(days=3)]

    st.subheader("📊 Estado de Ingredientes")
    st.dataframe(stock[['ingrediente', 'stock_actual', 'stock_minimo', 'estado']], use_container_width=True)

    st.subheader("⚠️ Ingredientes que caducan pronto")
    st.dataframe(caducan_pronto[['ingrediente', 'fecha_caducidad']], use_container_width=True)

# -------- RECOMENDACIÓN DE MENÚ --------
elif seccion == "🍽️ Recomendación de Menú":
    st.header("🍽️ Recomendación de Menú Semanal")

    dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes"]
    menu = {}

    disponibles = ingredientes.merge(stock, on="ingrediente")

    for i, dia in enumerate(dias_semana):
        fecha = datetime.date.today() + datetime.timedelta(days=(i - datetime.date.today().weekday()))
        if fecha.weekday() >= 5:
            continue

        menu_dia = {"Primer Plato": None, "Segundo Plato": None, "Postre": None}
        platos_disponibles = disponibles.groupby("plato").filter(lambda x: all(x['stock_actual'] >= x['cantidad_por_plato'])).drop_duplicates('plato')['plato'].tolist()

        np.random.shuffle(platos_disponibles)
        tipos = ventas.drop_duplicates('plato').set_index('plato')['tipo_plato']

        for plato in platos_disponibles:
            tipo = tipos.get(plato, "otro")
            if tipo == "primero" and not menu_dia["Primer Plato"]:
                menu_dia["Primer Plato"] = plato
            elif tipo == "segundo" and not menu_dia["Segundo Plato"]:
                menu_dia["Segundo Plato"] = plato
            elif tipo == "postre" and not menu_dia["Postre"]:
                menu_dia["Postre"] = plato
            if all(menu_dia.values()):
                break

        menu[dia.capitalize()] = menu_dia

    st.write(menu)

# -------- PLANIFICACIÓN DE PERSONAL --------
elif seccion == "👨‍🍳 Planificación de Personal":
    st.header("👨‍🍳 Planificación de Personal")
    st.write("Número recomendado según demanda estimada")

    resumen = []
    for fecha in futuro:
        festivo = fecha.date() in pd.to_datetime(festivos['fecha']).dt.date.values
        base = 40 if festivo or fecha.weekday() >= 5 else 25
        clima_dia = clima.loc[clima['fecha'] == fecha.date(), 'clima'].values
        clima_factor = 1.2 if clima_dia == 'soleado' else 1.0
        clientes_esperados = int(base * clima_factor + np.random.normal(0, 3))

        cocineros = max(1, clientes_esperados // 15)
        camareros = max(1, clientes_esperados // 10)

        resumen.append({
            "Día": format_date(fecha, format='full', locale='es_ES').capitalize(),
            "Clientes esperados": clientes_esperados,
            "Cocineros": cocineros,
            "Camareros": camareros
        })

    df_personal = pd.DataFrame(resumen)
    st.dataframe(df_personal, use_container_width=True)
    st.bar_chart(df_personal.set_index("Día")[['Cocineros', 'Camareros']])


