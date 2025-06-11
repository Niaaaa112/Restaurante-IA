# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import locale
from babel.dates import format_date
import numpy as np

# Cargar datos desde GitHub
data_url = "https://github.com/Niaaaa112/Restaurante-IA/raw/refs/heads/main/datos_restaurante_completo.xlsx"

excel_file = pd.ExcelFile(data_url)
ventas = pd.read_excel(excel_file, sheet_name="ventas")
ingredientes = pd.read_excel(excel_file, sheet_name="ingredientes")
stock = pd.read_excel(excel_file, sheet_name="stock")

# Configurar idioma español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

# Procesar datos
ventas['fecha'] = pd.to_datetime(ventas['fecha'])
stock['fecha_caducidad'] = pd.to_datetime(stock['fecha_caducidad'])

st.set_page_config(page_title="Restaurante IA", layout="wide")

# Sidebar
st.sidebar.title("🍽️ Panel de Control")
seccion = st.sidebar.radio("Navegar a:", ["📈 Predicción de Demanda", "📦 Inventario", "📋 Menú del Día", "👨‍🍳 Personal"])

# --- PREDICCIÓN DE DEMANDA --- #
if seccion == "📈 Predicción de Demanda":
    st.title("📈 Predicción de Demanda")

    dias_prediccion = st.selectbox("Selecciona días para predecir:", [7, 14, 30])
    fecha_inicio = ventas['fecha'].max() + timedelta(days=1)
    fechas_futuras = [fecha_inicio + timedelta(days=i) for i in range(dias_prediccion)]

    # Predicción simple basada en promedio histórico
    predicciones = []
    for fecha in fechas_futuras:
        dia = fecha.strftime('%A')
        clima = np.random.choice(['soleado', 'lluvioso', 'nublado'])
        festivo = int(np.random.rand() > 0.85)
        for plato in ventas['plato'].unique():
            base = ventas[ventas['plato'] == plato]['unidades'].mean()
            ajuste_clima = 1.2 if clima == 'soleado' else 0.8
            ajuste_festivo = 1.3 if festivo else 1
            unidades = int(base * ajuste_clima * ajuste_festivo)
            predicciones.append({
                'fecha': fecha,
                'dia_semana': format_date(fecha, 'EEEE', locale='es'),
                'clima': clima,
                'dia_festivo': festivo,
                'plato': plato,
                'unidades': unidades
            })

    df_pred = pd.DataFrame(predicciones)
    resumen = df_pred.groupby(['fecha', 'plato'])['unidades'].sum().reset_index()

    st.markdown("#### Demanda estimada por plato")
    fig = px.bar(resumen, x="fecha", y="unidades", color="plato", title="Demanda por día y plato")
    st.plotly_chart(fig, use_container_width=True)

# --- INVENTARIO --- #
elif seccion == "📦 Inventario":
    st.title("📦 Gestión de Inventario")

    stock = stock.copy()
    stock['estado'] = stock.apply(
        lambda row: '🟢 OK' if row['stock_actual'] > row['stock_minimo'] else '🔴 Bajo', axis=1)

    st.dataframe(stock.style.applymap(
        lambda val: 'background-color: #ffcccc' if 'Bajo' in str(val) else 'background-color: #ccffcc',
        subset=['estado']), use_container_width=True)

    resumen_estado = stock['estado'].value_counts().reset_index()
    resumen_estado.columns = ['estado', 'cantidad']

    fig = px.pie(resumen_estado, names='estado', values='cantidad', title="Estado del Inventario")
    st.plotly_chart(fig, use_container_width=True)

# --- MENÚ DEL DÍA --- #
elif seccion == "📋 Menú del Día":
    st.title("📋 Recomendación de Menú (Lunes a Viernes)")

    dias_semana = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes']
    platos = ventas['plato'].unique()
    tipos = ventas[['plato', 'tipo_plato']].drop_duplicates().set_index('plato')['tipo_plato'].to_dict()

    menu_recomendado = {}
    usados = set()

    for dia in dias_semana:
        disponibles = ingredientes.copy()
        disponibles = disponibles.merge(stock, on="ingrediente")

        candidatos = disponibles[disponibles['stock_actual'] > disponibles['cantidad_por_plato'] * 5]
        platos_disponibles = candidatos['plato'].unique()
        primeros = [p for p in platos_disponibles if tipos.get(p) == 'primero' and p not in usados]
        segundos = [p for p in platos_disponibles if tipos.get(p) == 'segundo' and p not in usados]
        postres = [p for p in platos_disponibles if tipos.get(p) == 'postre' and p not in usados]

        if primeros and segundos and postres:
            menu_recomendado[dia] = {
                '🥗 Primer Plato': np.random.choice(primeros),
                '🍖 Segundo Plato': np.random.choice(segundos),
                '🍰 Postre': np.random.choice(postres)
            }
            usados.update(menu_recomendado[dia].values())
        else:
            menu_recomendado[dia] = '⚠️ No disponible'

    for dia, menu in menu_recomendado.items():
        st.subheader(dia.capitalize())
        if isinstance(menu, dict):
            for tipo, plato in menu.items():
                st.markdown(f"- **{tipo}**: {plato}")
        else:
            st.warning(menu)

# --- PERSONAL --- #
elif seccion == "👨‍🍳 Personal":
    st.title("👨‍🍳 Planificación de Personal")

    resumen = df_pred.groupby(df_pred['fecha'].dt.date)['unidades'].sum().reset_index()
    resumen.columns = ['fecha', 'total_unidades']
    resumen['cocineros'] = resumen['total_unidades'].apply(lambda x: max(1, x // 40))
    resumen['camareros'] = resumen['total_unidades'].apply(lambda x: max(1, x // 50))
    resumen['dia'] = pd.to_datetime(resumen['fecha']).dt.strftime('%A')

    st.markdown("#### Recomendación por Día")
    st.dataframe(resumen[['dia', 'fecha', 'cocineros', 'camareros']])

    fig = px.bar(resumen, x="fecha", y=["cocineros", "camareros"], barmode="group",
                 title="Número recomendado de empleados")
    st.plotly_chart(fig, use_container_width=True)

