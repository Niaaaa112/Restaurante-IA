import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import locale
import requests
from io import BytesIO
import calendar
import plotly.express as px

# Config locale para dias en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass

st.set_page_config(layout="wide")
st.title("📊 Restaurante IA – Gestión y Predicción Inteligente")

# Cargar Excel desde GitHub
url = "https://github.com/Niaaaa112/Restaurante-IA/raw/refs/heads/main/datos_restaurante_completo.xlsx"
response = requests.get(url)
data = BytesIO(response.content)

ventas = pd.read_excel(data, sheet_name="ventas")
ingredientes = pd.read_excel(data, sheet_name="ingredientes")
stock = pd.read_excel(data, sheet_name="stock")
festivos = pd.read_excel(data, sheet_name="festivos")
clima = pd.read_excel(data, sheet_name="clima")

stock['fecha_caducidad'] = pd.to_datetime(stock['fecha_caducidad'])
clima['fecha'] = pd.to_datetime(clima['fecha'])

st.sidebar.title("Navegación")
seccion = st.sidebar.radio("Ir a sección:", ["📈 Predicción de demanda", "📦 Gestión de inventario", "🍽️ Menú recomendado", "👥 Planificación de personal"])

hoy = datetime.now().date()
proximos_dias = pd.date_range(start=hoy, periods=7).date
festivos_set = set(pd.to_datetime(festivos['fecha']).dt.date)

# Predicción de demanda
if seccion == "📈 Predicción de demanda":
    st.header("📈 Predicción de demanda por plato")
    demanda_pred = []
    for dia in proximos_dias:
        dia_nombre = calendar.day_name[dia.weekday()]
        clima_dia = clima[clima['fecha'].dt.date == dia]
        factor_clima = 1.1 if not clima_dia.empty and clima_dia.iloc[0]['clima'] == 'soleado' else 0.9
        factor_festivo = 1.3 if dia in festivos_set else 1.0
        for plato in ventas['plato'].unique():
            media = ventas[(ventas['plato'] == plato) & (ventas['dia_semana'] == dia_nombre)]['unidades'].mean()
            if np.isnan(media):
                media = ventas[ventas['plato'] == plato]['unidades'].mean()
            unidades = int(media * factor_clima * factor_festivo)
            demanda_pred.append({"fecha": dia, "plato": plato, "unidades": unidades})

    df_demanda = pd.DataFrame(demanda_pred)
    fig = px.bar(df_demanda, x="fecha", y="unidades", color="plato", barmode="group",
                 title="Demanda estimada de platos para los próximos días")
    st.plotly_chart(fig, use_container_width=True)

# Inventario
elif seccion == "📦 Gestión de inventario":
    st.header("📦 Gestión de inventario")
    stock['estado'] = stock.apply(lambda row: '🔴 Bajo' if row['stock_actual'] < row['stock_minimo'] else
                                               ('🟡 Pronto caduca' if row['fecha_caducidad'] <= pd.Timestamp(hoy + timedelta(days=3)) else '🟢 OK'), axis=1)
    color_estado = {'🔴 Bajo': '#ff4d4d', '🟡 Pronto caduca': '#ffd633', '🟢 OK': '#5cd65c'}

    def color_fila(row):
        return [f'background-color: {color_estado[row.estado]}; color: black' for _ in row]

    st.dataframe(stock.style.apply(color_fila, axis=1), use_container_width=True)

# Menú recomendado
elif seccion == "🍽️ Menú recomendado":
    st.header("🍽️ Menú recomendado de lunes a viernes")
    menu_final = {}
    tipos = ['primer plato', 'segundo plato', 'postre']

    platos_disponibles = ventas['plato'].unique()
    ingredientes_por_plato = ingredientes.groupby('plato')

    for i, dia in enumerate(pd.date_range(start=hoy, periods=7)):
        if dia.weekday() >= 5:  # Sábado o domingo
            continue
        dia_menu = {tipo: None for tipo in tipos}
        usados = set()
        for tipo in tipos:
            candidatos = [plato for plato in platos_disponibles if plato not in usados and tipo in plato.lower()]
            np.random.shuffle(candidatos)
            for plato in candidatos:
                necesarios = ingredientes_por_plato.get_group(plato)
                suficiente = True
                for _, ing in necesarios.iterrows():
                    st_row = stock[stock['ingrediente'] == ing['ingrediente']]
                    if st_row.empty or st_row.iloc[0]['stock_actual'] < ing['cantidad_por_plato']:
                        suficiente = False
                        break
                if suficiente:
                    dia_menu[tipo] = plato
                    usados.add(plato)
                    break
        menu_final[dia.strftime('%A %d/%m')] = dia_menu

    st.write("### Menú sugerido")
    st.table(pd.DataFrame(menu_final).T)

# Personal
elif seccion == "👥 Planificación de personal":
    st.header("👥 Planificación de personal para los próximos días")
    resumen = []
    for dia in proximos_dias:
        dia_nombre = calendar.day_name[dia.weekday()]
        total_clientes = ventas[ventas['dia_semana'] == dia_nombre]['unidades'].sum()
        if dia in festivos_set:
            total_clientes *= 1.3
        cocineros = int(np.ceil(total_clientes / 40))
        camareros = int(np.ceil(total_clientes / 25))
        resumen.append({"Día": dia.strftime('%A %d/%m'), "Clientes estimados": int(total_clientes),
                        "👨‍🍳 Cocineros": cocineros, "🧑‍💼 Camareros": camareros})

    st.write("### Recomendación de personal")
    st.dataframe(pd.DataFrame(resumen))

