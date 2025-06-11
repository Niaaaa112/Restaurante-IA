import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from babel.dates import format_date
from io import BytesIO
import base64

# -------- CONFIGURACION DE PAGINA -------- #
st.set_page_config(page_title="Restaurante Inteligente", layout="wide", initial_sidebar_state="expanded")

# -------- ESTILO -------- #
st.markdown("""
    <style>
    body {font-family: 'Segoe UI', sans-serif;}
    .main {background-color: #f7f7f7; color: #333;}
    .css-1v0mbdj, .css-1d391kg {color: #333;}
    .stSidebar {background-color: #ffffff;}
    h1, h2, h3 {font-weight: 600;}
    .metric {font-size: 20px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# -------- SIDEBAR -------- #
st.sidebar.image("https://img.icons8.com/fluency/96/restaurant.png", width=60)
st.sidebar.title("🍽️ Restaurante IA")
seccion = st.sidebar.radio("Ir a:", ["📊 Dashboard", "🔮 Predicción de Demanda", "📦 Inventario", "📅 Menú del Día", "👨‍🍳 Personal", "🛒 Sugerencias de Compra"])
st.sidebar.markdown("---")
st.sidebar.info("App desarrollada con Streamlit y IA")

# -------- CARGA DE DATOS -------- #
uploaded_file = st.sidebar.file_uploader("📤 Cargar archivo Excel", type=["xlsx"])
if uploaded_file:
    excel = pd.ExcelFile(uploaded_file)
    ventas = pd.read_excel(excel, sheet_name="ventas")
    ingredientes = pd.read_excel(excel, sheet_name="ingredientes")
    stock = pd.read_excel(excel, sheet_name="stock")
else:
    st.warning("Por favor, sube un archivo Excel con los datos.")
    st.stop()

# -------- FUNCIONES -------- #
def predecir_demanda(df):
    dias_futuros = [datetime.now().date() + timedelta(days=i) for i in range(7)]
    predicciones = []
    for dia in dias_futuros:
        clima = df['clima'].mode()[0]
        festivo = False
        dia_semana = dia.strftime('%A')
        for plato in df['plato'].unique():
            base = df[df['plato'] == plato]['unidades'].mean()
            ajuste = np.random.normal(loc=0, scale=base * 0.1)
            unidades = max(0, int(base + ajuste))
            predicciones.append({"fecha": dia, "plato": plato, "prediccion": unidades})
    return pd.DataFrame(predicciones)

# -------- DASHBOARD -------- #
if seccion == "📊 Dashboard":
    st.title("📊 Dashboard Resumen")
    st.subheader("Alertas y KPIs")
    col1, col2, col3 = st.columns(3)
    col1.metric("Platos más vendidos", ventas.groupby("plato")["unidades"].sum().idxmax())
    col2.metric("Día con más ventas", ventas.groupby("fecha")["unidades"].sum().idxmax().strftime("%d-%m-%Y"))
    col3.metric("Ingredientes bajos", stock[stock["stock_actual"] < stock["stock_minimo"]].shape[0])

# -------- PREDICCION -------- #
elif seccion == "🔮 Predicción de Demanda":
    st.title("🔮 Predicción de Demanda")
    df_pred = predecir_demanda(ventas)
    dias = st.radio("Ver predicciones para los próximos:", [7, 14, 30])
    df_pred_extendido = pd.concat([predecir_demanda(ventas) for _ in range(dias // 7)])
    fig = px.bar(df_pred_extendido, x="fecha", y="prediccion", color="plato", title="Predicción de demanda por plato")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_pred_extendido)

# -------- INVENTARIO -------- #
elif seccion == "📦 Inventario":
    st.title("📦 Gestión de Inventario")
    stock["estado"] = stock.apply(lambda row: "🟥 Bajo" if row.stock_actual < row.stock_minimo else ("🟨 Justo" if row.stock_actual < row.stock_minimo * 1.5 else "🟩 Ok"), axis=1)
    resumen = stock["estado"].value_counts().reset_index()
    resumen.columns = ["estado", "cantidad"]
    fig = px.pie(resumen, names="estado", values="cantidad", title="Estado del Inventario", color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(stock)

# -------- MENU DEL DIA -------- #
elif seccion == "📅 Menú del Día":
    st.title("📅 Menú sugerido de lunes a viernes")
    menu = []
    usados = []
    for i in range(5):
        dia = (datetime.now().date() + timedelta(days=i))
        disponibles = ingredientes[~ingredientes["ingrediente"].isin(stock[stock["stock_actual"] < stock["stock_minimo"]]["ingrediente"])]
        platos_disp = disponibles["plato"].unique()
        platos = ventas[ventas["plato"].isin(platos_disp)][["plato", "tipo_plato"]].drop_duplicates()
        try:
            primer = platos[(platos.tipo_plato == "primer") & (~platos.plato.isin(usados))].sample(1).iloc[0]["plato"]
        except:
            primer = "No disponible"
        try:
            segundo = platos[(platos.tipo_plato == "segundo") & (~platos.plato.isin(usados))].sample(1).iloc[0]["plato"]
        except:
            segundo = "No disponible"
        try:
            postre = platos[(platos.tipo_plato == "postre") & (~platos.plato.isin(usados))].sample(1).iloc[0]["plato"]
        except:
            postre = "No disponible"
        usados.extend([primer, segundo, postre])
        menu.append({"dia": format_date(dia, locale="es"), "primer": primer, "segundo": segundo, "postre": postre})
    st.dataframe(pd.DataFrame(menu))

# -------- PERSONAL -------- #
elif seccion == "👨‍🍳 Personal":
    st.title("👨‍🍳 Planificación de Personal")
    df_pred = predecir_demanda(ventas)
    demanda_dias = df_pred.groupby("fecha")["prediccion"].sum().reset_index()
    demanda_dias["cocineros"] = (demanda_dias["prediccion"] / 50).apply(np.ceil)
    demanda_dias["camareros"] = (demanda_dias["prediccion"] / 40).apply(np.ceil)
    st.bar_chart(demanda_dias.set_index("fecha")["prediccion"])
    st.dataframe(demanda_dias)

# -------- COMPRAS -------- #
elif seccion == "🛒 Sugerencias de Compra":
    st.title("🛒 Sugerencias Automáticas de Compra")
    bajo_stock = stock[stock["stock_actual"] < stock["stock_minimo"]]
    bajo_stock["sugerido"] = bajo_stock["stock_minimo"] * 1.5 - bajo_stock["stock_actual"]
    st.dataframe(bajo_stock[["ingrediente", "stock_actual", "stock_minimo", "sugerido"]])
    def descargar_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Compras")
        processed_data = output.getvalue()
        b64 = base64.b64encode(processed_data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="sugerencias_compra.xlsx">📥 Descargar Excel</a>'
        return href
    st.markdown(descargar_excel(bajo_stock), unsafe_allow_html=True)
