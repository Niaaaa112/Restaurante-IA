import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import warnings

# Configuración inicial
warnings.filterwarnings('ignore')
pd.set_option('display.float_format', '{:.2f}'.format)

# ========== CONFIGURACIÓN GENERAL ==========
st.set_page_config(
    page_title="RestaurantPro IA",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS simplificado y seguro
st.write('''
<style>
[data-testid="stSidebar"] {
    background: #f5f5f5 !important;
}
.metric-card {
    background: white;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}
.stDataFrame {
    border-radius: 10px;
}
.critical { color: #d62728; }
.warning { color: #ff7f0e; }
.success { color: #2ca02c; }
</style>
''', unsafe_allow_html=True)

# ========== CARGA DE DATOS ==========
@st.cache_data
def load_data():
    try:
        df_ventas = pd.read_excel("datos_restaurante_completo.xlsx", sheet_name="ventas")
        df_stock = pd.read_excel("datos_restaurante_completo.xlsx", sheet_name="stock")
        
        df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])
        df_stock["fecha_caducidad"] = pd.to_datetime(df_stock["fecha_caducidad"])
        df_stock["dias_caducidad"] = (df_stock["fecha_caducidad"] - pd.to_datetime('today')).dt.days
        
        return df_ventas, df_stock
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_ventas, df_stock = load_data()

# ========== FUNCIONES UTILITARIAS ==========
def metric_card(title, value, delta=None):
    delta_html = f"<span class='{'critical' if delta and '-' in str(delta) else 'success'}>{delta}</span>" if delta else ""
    st.markdown(f"""
        <div class="metric-card">
            <h3>{title}</h3>
            <h2>{value}</h2>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)

def predict_demand(df, days=7, sensitivity=0.8):
    """Predicción corregida sin errores de paréntesis"""
    predictions = []
    base = df.groupby("plato")["unidades"].mean().reset_index()
    
    for i in range(days):
        fecha = datetime.now().date() + timedelta(days=i)
        for _, row in base.iterrows():
            adjustment = 1 + (np.random.normal(0, 0.15) * sensitivity)
            prediction = int(row["unidades"] * adjustment)
            predictions.append({
                "fecha": fecha,
                "plato": row["plato"],
                "prediccion": prediction
            })
    return pd.DataFrame(predictions)

def planificar_personal(df_pred):
    if df_pred.empty:
        return pd.DataFrame()
    resumen = df_pred.groupby("fecha")["prediccion"].sum().reset_index()
    resumen["cocineros"] = resumen["prediccion"].apply(lambda x: max(1, x // 40))
    resumen["camareros"] = resumen["prediccion"].apply(lambda x: max(1, x // 30))
    return resumen

# ========== BARRA LATERAL ==========
with st.sidebar:
    st.title("🍽️ RestaurantPro")
    menu = st.radio(
        "Menú Principal",
        ["📊 Dashboard", "📈 Predicción", "📦 Inventario", "👨‍🍳 Personal"]
    )
    st.markdown("---")
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ========== CONTENIDO PRINCIPAL ==========
if menu == "📊 Dashboard":
    st.title("Panel de Control")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ventas_totales = df_ventas["unidades"].sum()
        metric_card("Ventas Totales", f"{ventas_totales:,} uds")
    
    with col2:
        bajo_stock = len(df_stock[df_stock["stock_actual"] < df_stock["stock_minimo"]])
        metric_card("Ingredientes Bajos", bajo_stock)
    
    with col3:
        por_caducar = len(df_stock[df_stock["dias_caducidad"] < 3])
        metric_card("Por Caducar", por_caducar)
    
    st.subheader("Top 5 Platos")
    top_platos = df_ventas.groupby("plato")["unidades"].sum().nlargest(5)
    fig = px.bar(top_platos, orientation='h')
    st.plotly_chart(fig, use_container_width=True)

elif menu == "📈 Predicción":
    st.title("Predicción de Demanda")
    dias = st.slider("Días a predecir:", 3, 14, 7)
    
    if st.button("Generar Predicción"):
        df_pred = predict_demand(df_ventas, dias)
        fig = px.line(df_pred, x="fecha", y="prediccion", color="plato")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Planificación de Personal")
        personal = planificar_personal(df_pred)
        st.dataframe(personal)

elif menu == "📦 Inventario":
    st.title("Gestión de Inventario")
    
    df_stock["estado"] = np.where(
        df_stock["stock_actual"] < df_stock["stock_minimo"], "🟥 Crítico",
        np.where(df_stock["dias_caducidad"] < 3, "🟨 Por caducar", "🟩 OK")
    )
    
    st.dataframe(
        df_stock[["ingrediente", "stock_actual", "stock_minimo", "dias_caducidad", "estado"]],
        column_config={
            "dias_caducidad": st.column_config.NumberColumn("Días hasta caducidad")
        }
    )

elif menu == "👨‍🍳 Personal":
    st.title("Planificación de Personal")
    st.info("Esta sección se genera automáticamente desde la Predicción de Demanda")
    st.write("Por favor genera primero una predicción en la pestaña correspondiente")
