import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from babel.dates import format_date

# Configuración de página
st.set_page_config(page_title="Restaurante IA", layout="wide")

# Estilo
st.markdown("""
    <style>
    .main {background-color: #f5f5f5;}
    .css-1v0mbdj, .css-ffhzg2 {background-color: #ffffff; border-radius: 10px; padding: 1rem;}
    </style>
""", unsafe_allow_html=True)

# Sidebar (menú lateral)
st.sidebar.title("🍽️ Restaurante IA")
opcion = st.sidebar.radio("Selecciona una sección:", ["📈 Predicción de Demanda", "📦 Inventario", "📋 Menú del Día", "👨‍🍳 Planificación de Personal"])

# Cargar datos desde GitHub
excel_file = "https://github.com/Niaaaa112/Restaurante-IA/raw/refs/heads/main/datos_restaurante_completo.xlsx"
df_ventas = pd.read_excel(excel_file, sheet_name="ventas")
df_ingredientes = pd.read_excel(excel_file, sheet_name="ingredientes")
df_stock = pd.read_excel(excel_file, sheet_name="stock")

# Preprocesamiento
df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'])
df_stock['fecha_caducidad'] = pd.to_datetime(df_stock['fecha_caducidad'])

hoy = pd.Timestamp.today().normalize()
df_futuro = pd.DataFrame({
    'fecha': [hoy + timedelta(days=i) for i in range(7)],
})
df_futuro['dia_semana'] = df_futuro['fecha'].dt.day_name()
df_futuro['clima'] = 'soleado'
df_futuro['dia_festivo'] = df_futuro['fecha'].isin(df_ventas[df_ventas['dia_festivo'] == True]['fecha'].unique())

# Predicción de demanda (simulada)
demanda_promedio = df_ventas.groupby('plato')['unidades'].mean()
predicciones = []
for _, row in df_futuro.iterrows():
    for plato, media in demanda_promedio.items():
        factor_festivo = 1.5 if row['dia_festivo'] else 1
        factor_clima = 1.2 if row['clima'] == 'soleado' else 1
        pred = int(media * factor_festivo * factor_clima)
        predicciones.append({
            'fecha': row['fecha'],
            'plato': plato,
            'unidades': pred
        })
df_pred = pd.DataFrame(predicciones)

# INVENTARIO
estado_inventario = []
for _, row in df_stock.iterrows():
    if row['stock_actual'] < row['stock_minimo']:
        estado = 'Bajo'
    elif row['fecha_caducidad'] < hoy + timedelta(days=3):
        estado = 'Próxima caducidad'
    else:
        estado = 'Correcto'
    estado_inventario.append({
        'ingrediente': row['ingrediente'],
        'estado': estado
    })
df_estado = pd.DataFrame(estado_inventario)

# MENÚ
tipos = df_ventas['tipo_plato'].unique()
menu_dias = {}
for i in range(5):  # lunes a viernes
    fecha = hoy + timedelta(days=i)
    platos_disponibles = df_pred[df_pred['fecha'] == fecha]['plato'].tolist()
    platos_disponibles = list(set(platos_disponibles))
    menu = {
        tipo: next((pl for pl in platos_disponibles if df_ventas[df_ventas['plato'] == pl]['tipo_plato'].iloc[0] == tipo), "No disponible")
        for tipo in ['primer plato', 'segundo plato', 'postre']
    }
    menu_dias[fecha] = menu

# PERSONAL
resumen = df_pred.groupby("fecha")["unidades"].sum().reset_index()
resumen["cocineros"] = (resumen["unidades"] / 20).apply(np.ceil).astype(int)
resumen["camareros"] = (resumen["unidades"] / 30).apply(np.ceil).astype(int)

# MOSTRAR SECCIONES
if opcion == "📈 Predicción de Demanda":
    st.title("📈 Predicción de Demanda")
    dias = st.slider("Selecciona cuántos días ver:", 1, 7, 5)
    fig = px.bar(df_pred[df_pred['fecha'] <= hoy + timedelta(days=dias - 1)],
                 x="fecha", y="unidades", color="plato",
                 title="Demanda estimada por plato")
    st.plotly_chart(fig, use_container_width=True)

elif opcion == "📦 Inventario":
    st.title("📦 Estado del Inventario")
    colores = {'Correcto': 'lightgreen', 'Bajo': 'tomato', 'Próxima caducidad': 'orange'}
    df_estado['color'] = df_estado['estado'].map(colores)
    st.dataframe(df_estado[['ingrediente', 'estado']], use_container_width=True)
    fig_inv = px.histogram(df_estado, x='estado', color='estado',
                           color_discrete_map=colores, title="Resumen del Inventario")
    st.plotly_chart(fig_inv, use_container_width=True)

elif opcion == "📋 Menú del Día":
    st.title("📋 Menú recomendado")
    for fecha, platos in menu_dias.items():
        nombre_dia = format_date(fecha, format='EEEE', locale='es_ES')
        st.subheader(f"{nombre_dia.capitalize()} - {fecha.strftime('%d/%m/%Y')}")
        for tipo, plato in platos.items():
            st.markdown(f"**{tipo.capitalize()}**: {plato}")

elif opcion == "👨‍🍳 Planificación de Personal":
    st.title("👨‍🍳 Planificación de Personal")
    for _, row in resumen.iterrows():
        fecha_txt = format_date(row['fecha'], format='full', locale='es_ES')
        st.markdown(f"### 📅 {fecha_txt}")
        st.markdown(f"👨‍🍳 Cocineros necesarios: **{row['cocineros']}**")
        st.markdown(f"🧑‍💼 Camareros necesarios: **{row['camareros']}**")

