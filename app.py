import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="App Restaurante IA")

# Cargar datos desde un único Excel con múltiples hojas
excel_file = "datos_restaurante_completo.xlsx"
ventas = pd.read_excel(excel_file, sheet_name="ventas")
ingredientes = pd.read_excel(excel_file, sheet_name="ingredientes")
stock = pd.read_excel(excel_file, sheet_name="stock")

# Procesamiento básico
ventas['fecha'] = pd.to_datetime(ventas['fecha'])
stock['fecha_caducidad'] = pd.to_datetime(stock['fecha_caducidad'])

# Estilos colores stock
def estado_stock(row):
    if row['stock_actual'] < row['stock_minimo']:
        return 'Bajo'
    elif row['fecha_caducidad'] <= datetime.today() + timedelta(days=2):
        return 'Caducando'
    else:
        return 'OK'

stock['estado'] = stock.apply(estado_stock, axis=1)

# Función para estimar demanda por plato
@st.cache_data

def predecir_demanda():
    demanda = ventas.groupby(['fecha', 'plato']).agg({"unidades": "sum", "clima": "first", "dia_festivo": "first"}).reset_index()
    demanda['ajuste'] = np.where(demanda['clima'] == 'soleado', 1.2,
                          np.where(demanda['clima'] == 'lluvioso', 0.8,
                          np.where(demanda['dia_festivo'] == 'Sí', 1.3, 1.0)))
    demanda['unidades_ajustadas'] = (demanda['unidades'] * demanda['ajuste']).round().astype(int)
    return demanda

demanda_pred = predecir_demanda()

# Pestañas
menu = st.sidebar.radio("Ir a:", ["Dashboard", "Predicción de Demanda", "Gestión de Inventario", "Menú Semanal", "Planificación de Personal"])

# --- Dashboard
if menu == "Dashboard":
    st.title("📊 Dashboard Resumen")
    col1, col2 = st.columns(2)

    with col1:
        total_platos = demanda_pred['unidades_ajustadas'].sum()
        st.metric("Total Platos Estimados (30 días)", total_platos)

        criticos = stock[stock['estado'] != 'OK'].shape[0]
        st.metric("Ingredientes Críticos", criticos)

    with col2:
        coste_total = demanda_pred['unidades_ajustadas'].sum() * 1.5
        st.metric("Coste Estimado de Personal (€)", f"{coste_total:.2f}")

    st.subheader("Menú semanal previsto")
    st.info("Revisa la pestaña 'Menú Semanal' para ver el detalle del menú generado automáticamente")

# --- Predicción de Demanda
elif menu == "Predicción de Demanda":
    st.title("📈 Predicción de Demanda por Plato")
    dias = st.slider("¿Cuántos días visualizar?", 7, 30, 14)
    pred_filtrada = demanda_pred[demanda_pred['fecha'] <= datetime.today() + timedelta(days=dias)]

    fig = px.bar(pred_filtrada, x='fecha', y='unidades_ajustadas', color='plato',
                 labels={'unidades_ajustadas': 'Unidades previstas'},
                 title="Demanda estimada por plato")
    st.plotly_chart(fig, use_container_width=True)

# --- Gestión de Inventario
elif menu == "Gestión de Inventario":
    st.title("📦 Gestión de Inventario")
    st.subheader("Estado del Stock")

    estado_counts = stock['estado'].value_counts().reset_index()
    fig = px.pie(estado_counts, names='index', values='estado', title="Estado del inventario")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Ingredientes críticos")
    st.dataframe(stock[stock['estado'] != 'OK'], use_container_width=True)

    st.subheader("Sugerencias de compra")
    sugerencias = stock[stock['stock_actual'] < stock['stock_minimo']]
    st.dataframe(sugerencias[['ingrediente', 'stock_actual', 'stock_minimo']], use_container_width=True)

# --- Menú Semanal
elif menu == "Menú Semanal":
    st.title("🍽 Recomendación de Menú (L-V)")
    semana = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    hoy = datetime.today()

    menu_semanal = {}
    disponibles = ingredientes['plato'].unique().tolist()
    usados = []

    for i in range(5):
        dia = hoy + timedelta(days=i)
        nombre_dia = dia.strftime('%A')
        if nombre_dia not in semana:
            continue

        menu_dia = {"entrante": None, "principal": None, "postre": None}

        for tipo in ["entrante", "principal", "postre"]:
            candidatos = ventas[(ventas['tipo_plato'] == tipo) & (~ventas['plato'].isin(usados))]['plato'].unique()
            for candidato in candidatos:
                ingredientes_plato = ingredientes[ingredientes['plato'] == candidato]
                ok = True
                for _, row in ingredientes_plato.iterrows():
                    ing = row['ingrediente']
                    cant = row['cantidad_por_plato']
                    stock_disp = stock[stock['ingrediente'] == ing]
                    if stock_disp.empty or stock_disp.iloc[0]['stock_actual'] < cant:
                        ok = False
                        break
                if ok:
                    menu_dia[tipo] = candidato
                    usados.append(candidato)
                    break

        menu_semanal[nombre_dia] = menu_dia

    for dia, platos in menu_semanal.items():
        st.subheader(dia)
        if all(v is None for v in platos.values()):
            st.warning("No disponible")
        else:
            st.write(f"🥗 Entrante: {platos['entrante']}")
            st.write(f"🍛 Principal: {platos['principal']}")
            st.write(f"🍮 Postre: {platos['postre']}")

# --- Planificación de Personal
elif menu == "Planificación de Personal":
    st.title("👥 Planificación de Personal")
    pred_por_dia = demanda_pred.groupby('fecha').agg({'unidades_ajustadas': 'sum'}).reset_index()
    pred_por_dia['cocineros'] = (pred_por_dia['unidades_ajustadas'] / 20).clip(lower=1).round().astype(int)
    pred_por_dia['camareros'] = (pred_por_dia['unidades_ajustadas'] / 30).clip(lower=1).round().astype(int)
    pred_por_dia['dia'] = pred_por_dia['fecha'].dt.strftime('%A')

    fig = px.line(pred_por_dia, x='fecha', y='unidades_ajustadas', title="Demanda Total Estimada", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Resumen de personal sugerido")
    def icono(n):
        if n >= 3:
            return '🟢'
        elif n == 2:
            return '🟡'
        else:
            return '🔴'

    pred_por_dia['icono_cocina'] = pred_por_dia['cocineros'].apply(icono)
    pred_por_dia['icono_sala'] = pred_por_dia['camareros'].apply(icono)

    resumen = pred_por_dia[['fecha', 'dia', 'cocineros', 'icono_cocina', 'camareros', 'icono_sala']]
    resumen['dia'] = resumen['fecha'].dt.strftime('%A')
    resumen['dia'] = resumen['dia'].map({
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    })

    st.dataframe(resumen, use_container_width=True)

