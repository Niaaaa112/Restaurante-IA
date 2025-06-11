import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from babel.dates import format_date
import random

st.set_page_config(page_title="Gestión Restaurante IA", layout="wide")
st.markdown("""
    <style>
    /* Estilo global */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
    }
    .title {
        font-size: 32px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Cargar datos
@st.cache_data
def cargar_datos():
    excel = pd.ExcelFile("datos_restaurante_actualizado.xlsx")
    ventas = pd.read_excel(excel, sheet_name="ventas")
    ingredientes = pd.read_excel(excel, sheet_name="ingredientes")
    stock = pd.read_excel(excel, sheet_name="stock")
    return ventas, ingredientes, stock

ventas, ingredientes, stock = cargar_datos()

# Sidebar de navegación
st.sidebar.title("Menú")
opcion = st.sidebar.radio("Ir a:", ["📊 Dashboard", "📈 Predicción de demanda", "📦 Inventario", "📅 Menú del día", "👨‍🍳 Planificación de personal"])

# ---------- 1. DASHBOARD ----------
if opcion == "📊 Dashboard":
    st.title("📊 Resumen General")
    col1, col2, col3 = st.columns(3)
    col1.metric("Platos Vendidos (últimos 7 días)", int(ventas.tail(7)['unidades'].sum()))
    col2.metric("Ingresos Totales (€)", f"{ventas['precio'].mul(ventas['unidades']).sum():,.2f}")
    col3.metric("Ingredientes en Bajo Stock", int((stock['stock_actual'] < stock['stock_minimo']).sum()))

    st.markdown("### Estado del Inventario")
    stock['estado'] = np.where(stock['stock_actual'] < stock['stock_minimo'], 'Bajo', 'OK')
    resumen = stock['estado'].value_counts().reset_index()
    fig = px.bar(resumen, x='index', y='estado', color='index', title='Resumen del Inventario', 
                 color_discrete_map={'Bajo': 'red', 'OK': 'green'}, labels={'index': 'Estado', 'estado': 'Cantidad'})
    st.plotly_chart(fig, use_container_width=True)

# ---------- 2. PREDICCIÓN DE DEMANDA ----------
elif opcion == "📈 Predicción de demanda":
    st.title("📈 Predicción de Demanda por Plato")
    dias_futuros = 7
    fecha_hoy = datetime.today()
    fechas = [fecha_hoy + timedelta(days=i) for i in range(dias_futuros)]
    platos = ventas['plato'].unique()

    predicciones = []
    for fecha in fechas:
        for plato in platos:
            base = ventas[ventas['plato'] == plato]['unidades'].mean()
            variacion = random.uniform(0.8, 1.2)
            cantidad = int(base * variacion)
            predicciones.append({"fecha": fecha.date(), "plato": plato, "prediccion": max(cantidad, 0)})

    df_pred = pd.DataFrame(predicciones)
    st.markdown("### Selecciona el número de días a visualizar")
    dias = st.slider("Días", 1, 14, 7)
    fig = px.bar(df_pred[df_pred['fecha'] <= fecha_hoy.date() + timedelta(days=dias)], 
                 x="fecha", y="prediccion", color="plato", title="Predicción de demanda por día y plato")
    st.plotly_chart(fig, use_container_width=True)

# ---------- 3. INVENTARIO ----------
elif opcion == "📦 Inventario":
    st.title("📦 Gestión de Inventario")
    stock['estado'] = np.where(stock['stock_actual'] < stock['stock_minimo'], 'Bajo', 'OK')
    st.dataframe(stock.style.apply(lambda x: ['background-color: red' if v=='Bajo' else 'background-color: lightgreen' for v in x], subset=['estado']))

# ---------- 4. MENÚ DEL DÍA ----------
elif opcion == "📅 Menú del día":
    st.title("📅 Menú Semanal (Lunes a Viernes)")
    dias_semana = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes']
    platos_disponibles = ventas[['plato', 'tipo_plato']].drop_duplicates()
    usados = set()
    menus = []
    for dia in dias_semana:
        dia_menu = {'día': dia}
        for tipo in ['primer', 'segundo', 'postre']:
            candidatos = platos_disponibles[(platos_disponibles['tipo_plato'] == tipo) & (~platos_disponibles['plato'].isin(usados))]
            if not candidatos.empty:
                elegido = candidatos.sample(1).iloc[0]['plato']
                dia_menu[tipo] = elegido
                usados.add(elegido)
            else:
                dia_menu[tipo] = 'No disponible'
        menus.append(dia_menu)
    st.dataframe(pd.DataFrame(menus))

# ---------- 5. PLANIFICACIÓN DE PERSONAL ----------
elif opcion == "👨‍🍳 Planificación de personal":
    st.title("👨‍🍳 Planificación del Personal")
    demanda_dias = df_pred.groupby("fecha")["prediccion"].sum().reset_index()
    demanda_dias['cocineros'] = (demanda_dias['prediccion'] / 50).apply(np.ceil).astype(int)
    demanda_dias['camareros'] = (demanda_dias['prediccion'] / 40).apply(np.ceil).astype(int)
    demanda_dias['día'] = demanda_dias['fecha'].apply(lambda x: format_date(x, 'EEEE', locale='es'))
    st.dataframe(demanda_dias[['fecha', 'día', 'prediccion', 'cocineros', 'camareros']].rename(columns={
        'prediccion': 'Clientes esperados'
    }))

    fig = px.bar(demanda_dias, x='fecha', y=['cocineros', 'camareros'], 
                 title='Necesidad de Personal por Día', barmode='group')
    st.plotly_chart(fig, use_container_width=True)



