import streamlit as st
import pandas as pd
import numpy as np
import io
import requests
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, timedelta
import calendar
import locale

# Establecer locale en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, '')

st.set_page_config(page_title="Restaurante IA", layout="wide")
st.title("🍽️ Panel Inteligente para Restaurantes")

# --- CARGA DE DATOS DESDE GITHUB ---
url_excel = "https://github.com/Niaaaa112/Restaurante-IA/raw/refs/heads/main/datos_restaurante_completo.xlsx"
response = requests.get(url_excel)
file = io.BytesIO(response.content)

ventas = pd.read_excel(file, sheet_name="ventas")
ingredientes = pd.read_excel(file, sheet_name="ingredientes")
stock = pd.read_excel(file, sheet_name="stock")

# Convertir fechas
stock['fecha_caducidad'] = pd.to_datetime(stock['fecha_caducidad'])

# --- FUNCIONES ---
def predecir_demanda(dias):
    hoy = datetime.today()
    dias_semana = [calendar.day_name[(hoy + timedelta(days=i)).weekday()] for i in range(dias)]
    demanda_predicha = []

    for i in range(dias):
        fecha = hoy + timedelta(days=i)
        dia = fecha.strftime('%A')
        clima = np.random.choice(['soleado', 'lluvioso', 'nublado'])
        festivo = fecha.weekday() in [5, 6] or np.random.rand() < 0.1

        platos = ventas['plato'].unique()
        for plato in platos:
            base = ventas[ventas['plato'] == plato]['unidades'].mean()
            ajuste = 1.3 if festivo else 1.0
            clima_factor = 0.9 if clima == 'lluvioso' else 1.0
            prediccion = int(base * ajuste * clima_factor)
            demanda_predicha.append({
                'fecha': fecha.strftime('%A %d/%m'),
                'plato': plato,
                'unidades': max(0, int(prediccion)),
                'clima': clima,
                'festivo': festivo
            })

    return pd.DataFrame(demanda_predicha)

def clasificar_estado(stock):
    def estado(row):
        if row['stock_actual'] < row['stock_minimo']:
            return 'Bajo'
        elif row['stock_actual'] < row['stock_minimo'] * 1.5:
            return 'Medio'
        else:
            return 'Óptimo'
    stock['estado'] = stock.apply(estado, axis=1)
    return stock

def recomendar_menu(fecha):
    platos_disponibles = ingredientes.groupby('plato').sum().reset_index()
    recomendados = []
    tipos = ['primer plato', 'segundo plato', 'postre']
    platos_filtrados = ventas.groupby(['plato', 'tipo_plato'])['unidades'].mean().reset_index()
    platos_filtrados = platos_filtrados.merge(platos_disponibles, on='plato')

    for tipo in tipos:
        candidatos = platos_filtrados[platos_filtrados['tipo_plato'] == tipo].sort_values(by='unidades', ascending=False)
        for _, fila in candidatos.iterrows():
            ingredientes_plato = ingredientes[ingredientes['plato'] == fila['plato']]
            disponible = True
            for _, ing in ingredientes_plato.iterrows():
                stock_ing = stock[stock['ingrediente'] == ing['ingrediente']]
                if stock_ing.empty or stock_ing['stock_actual'].values[0] < ing['cantidad_por_plato']:
                    disponible = False
                    break
            if disponible:
                recomendados.append((tipo, fila['plato']))
                break

    return recomendados

def planificar_personal(demanda):
    resumen = demanda.groupby('fecha')['unidades'].sum().reset_index()
    resumen['cocineros'] = (resumen['unidades'] / 30).apply(np.ceil).astype(int)
    resumen['camareros'] = (resumen['unidades'] / 40).apply(np.ceil).astype(int)
    return resumen

# --- SECCIONES ---
seccion = st.sidebar.selectbox("Selecciona sección", [
    "📊 Predicción de demanda",
    "📊 Gestión de inventario",
    "🍲 Recomendación de menú",
    "💼 Planificación de personal"
])

# --- DEMANDA ---
if seccion == "📊 Predicción de demanda":
    dias = st.slider("Selecciona días a predecir", 1, 14, 7)
    df_pred = predecir_demanda(dias)
    st.subheader("Demanda estimada por plato")
    fig = px.bar(df_pred, x='fecha', y='unidades', color='plato', barmode='group',
                 title='Predicción de unidades por plato', height=500)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_pred, use_container_width=True)

# --- INVENTARIO ---
elif seccion == "📊 Gestión de inventario":
    st.subheader("Inventario actual de ingredientes")
    stock = clasificar_estado(stock)
    color_map = {'Bajo': '#FF4B4B', 'Medio': '#FFA500', 'Óptimo': '#4CAF50'}
    stock['color'] = stock['estado'].map(color_map)
    styled = stock.style.apply(lambda x: [f'background-color: {color_map.get(v, "")}' for v in x.estado], axis=1)
    st.dataframe(styled, use_container_width=True)

# --- MENÚ DEL DÍA ---
elif seccion == "🍲 Recomendación de menú":
    st.subheader("Recomendación de menú semanal")
    hoy = datetime.today()
    dias_menu = [hoy + timedelta(days=i) for i in range(7) if (hoy + timedelta(days=i)).weekday() < 5]

    for fecha in dias_menu:
        nombre_dia = fecha.strftime('%A')
        recomendados = recomendar_menu(fecha)
        if recomendados:
            st.markdown(f"**{nombre_dia.title()} ({fecha.strftime('%d/%m')}):**")
            for tipo in ['primer plato', 'segundo plato', 'postre']:
                plato = next((p for t, p in recomendados if t == tipo), 'No disponible')
                st.write(f"- {tipo.title()}: {plato}")
        else:
            st.markdown(f"**{nombre_dia.title()} ({fecha.strftime('%d/%m')}):** No disponible")

# --- PERSONAL ---
elif seccion == "💼 Planificación de personal":
    st.subheader("Recomendación de personal")
    df_pred = predecir_demanda(7)
    personal = planificar_personal(df_pred)
    personal['color'] = np.where(personal['unidades'] > 100, 'red', 'green')
    fig = px.bar(personal, x='fecha', y='unidades', color='color',
                 text='unidades', title='Clientes esperados', height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(personal[['fecha', 'unidades', 'cocineros', 'camareros']], use_container_width=True)
