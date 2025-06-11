import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import warnings

# Configuración inicial
warnings.filterwarnings('ignore')
pd.set_option('display.float_format', '{:.2f}'.format)

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(page_title="Gestión Restaurante IA", layout="wide")

# CSS simplificado sin llaves problemáticas
st.write('''
<style>
[data-testid="stSidebar"] > div:first-child { background-color: #f5f5f5; }
.block-container { padding: 2rem; }
.stMetric { border: 1px solid #f0f2f6; border-radius: 10px; padding: 15px; }
.stMetric label { font-size: 1rem; color: #636363; }
.stMetric h1 { color: #000; }
.stAlert { border-radius: 10px; }
</style>
''', unsafe_allow_html=True)
# ========== CARGA Y PREPARACIÓN DE DATOS ==========
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data():
    file_path = "datos_restaurante_completo.xlsx"
    data = {
        "ventas": pd.read_excel(file_path, sheet_name="ventas"),
        "ingredientes": pd.read_excel(file_path, sheet_name="ingredientes"),
        "stock": pd.read_excel(file_path, sheet_name="stock")
    }
    
    # Procesamiento de datos
    data["ventas"]["fecha"] = pd.to_datetime(data["ventas"]["fecha"])
    data["stock"]["fecha_caducidad"] = pd.to_datetime(data["stock"]["fecha_caducidad"])
    
    # Calcular días hasta caducidad
    data["stock"]["dias_caducidad"] = (data["stock"]["fecha_caducidad"] - pd.to_datetime('today')).dt.days
    
    return data

data = load_data()
df_ventas, df_ingredientes, df_stock = data["ventas"], data["ingredientes"], data["stock"]

# ========== FUNCIONES UTILITARIAS ==========
def metric_card(title, value, delta=None, delta_color="normal"):
    """Crea una tarjeta de métrica visualmente atractiva"""
    delta_html = f"<span style='color:{delta_color}'>{delta}</span>" if delta else ""
    st.markdown(f"""
        <div class="metric-card">
            <h3>{title}</h3>
            <h2>{value}</h2>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)

def style_inventory(row):
    """Estilo condicional para el inventario"""
    if row["stock_actual"] < row["stock_minimo"]:
        return ['background-color: #ffdddd'] * len(row)
    elif row["dias_caducidad"] < 3:
        return ['background-color: #fff3cd'] * len(row)
    return [''] * len(row)

def predict_demand(df, days=7, sensitivity=0.8):
    """Predicción mejorada con estacionalidad semanal"""
    day_of_week = datetime.now().weekday()
    base = df.groupby(["plato", "dia_semana"])["unidades"].mean().reset_index()
    
    predictions = []
    for i in range(days):
        target_day = (day_of_week + i) % 7
        day_data = base[base["dia_semana"] == target_day]
        
        for _, row in day_data.iterrows():
            # Ajuste por sensibilidad (0-1)
            prediction = int(row["unidades"] * (1 + (np.random.normal(0, 0.15) * sensitivity))
            predictions.append({
                "fecha": (datetime.now() + timedelta(days=i)).date(),
                "plato": row["plato"],
                "prediccion": prediction,
                "dia_semana": target_day
            })
    return pd.DataFrame(predictions)

def generate_menu(df_platos, df_stock, consider_stock=True):
    """Generación de menú considerando disponibilidad de ingredientes"""
    # Implementación mejorada (omitiendo por brevedad)
    pass

# ========== BARRA LATERAL ==========
with st.sidebar:
    st.title("🍽️ RestaurantPro")
    st.markdown("---")
    
    selected = st.radio(
        "Menú Principal",
        options=[
            "📊 Dashboard",
            "📈 Predicción Demanda",
            "📦 Gestión Inventario",
            "🍽️ Menú Semanal",
            "👨‍🍳 Planificación Personal",
            "🛒 Sugerencias Compra",
            "⚙️ Configuración"
        ]
    )
    
    st.markdown("---")
    st.markdown("**Filtros Globales**")
    time_range = st.select_slider(
        "Rango de análisis:",
        options=["7 días", "15 días", "30 días", "60 días"]
    )
    
    st.markdown("---")
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ========== DASHBOARD PRINCIPAL ==========
if selected == "📊 Dashboard":
    st.title("📊 Panel de Control")
    
    # Fila de métricas clave
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_sales = df_ventas["unidades"].sum()
        metric_card("Ventas Totales", f"{total_sales:,} uds")
    
    with col2:
        avg_sales = df_ventas["unidades"].mean()
        metric_card("Promedio Diario", f"{avg_sales:,.1f} uds/día")
    
    with col3:
        low_stock = len(df_stock[df_stock["stock_actual"] < df_stock["stock_minimo"]])
        metric_card("Ingredientes Bajos", low_stock, delta_color="critical")
    
    with col4:
        expiring_soon = len(df_stock[df_stock["dias_caducidad"] < 3])
        metric_card("Próximos a Caducar", expiring_soon, delta_color="warning")
    
    # Gráficos principales
    tab1, tab2, tab3 = st.tabs(["Ventas", "Inventario", "Tendencias"])
    
    with tab1:
        st.subheader("Top 5 Platos Más Vendidos")
        top_platos = df_ventas.groupby("plato")["unidades"].sum().nlargest(5).reset_index()
        fig = px.bar(top_platos, x="plato", y="unidades", color="plato")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Estado del Inventario")
        fig = px.treemap(df_stock, path=["estado"], values="stock_actual")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Tendencias de Ventas")
        ventas_diarias = df_ventas.groupby("fecha")["unidades"].sum().reset_index()
        fig = px.line(ventas_diarias, x="fecha", y="unidades")
        st.plotly_chart(fig, use_container_width=True)

# ========== PREDICCIÓN DE DEMANDA ==========
elif selected == "📈 Predicción Demanda":
    st.title("📈 Predicción de Demanda")
    
    col1, col2 = st.columns(2)
    with col1:
        days_to_predict = st.slider("Días a predecir:", 3, 14, 7)
    with col2:
        sensitivity = st.slider("Sensibilidad:", 0.1, 1.0, 0.8, step=0.1)
    
    df_pred = predict_demand(df_ventas, days_to_predict, sensitivity)
    
    # Visualización interactiva
    view_option = st.radio("Visualización:", ["Por Plato", "Agregado"])
    
    if view_option == "Por Plato":
        fig = px.bar(df_pred, x="fecha", y="prediccion", color="plato", 
                    title="Demanda Predicha por Plato")
    else:
        agg_pred = df_pred.groupby("fecha")["prediccion"].sum().reset_index()
        fig = px.line(agg_pred, x="fecha", y="prediccion", markers=True,
                      title="Demanda Total Predicha")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detalle numérico
    with st.expander("Ver datos detallados"):
        st.dataframe(df_pred.pivot_table(index="fecha", columns="plato", 
                                       values="prediccion", aggfunc="sum"))

# ========== GESTIÓN DE INVENTARIO ==========
elif selected == "📦 Gestión Inventario":
    st.title("📦 Gestión de Inventario")
    
    # Filtros interactivos
    col1, col2 = st.columns(2)
    with col1:
        show_only = st.multiselect(
            "Mostrar:",
            options=["Bajo stock", "Próximos a caducar", "Todo"],
            default=["Bajo stock"]
        )
    
    with col2:
        sort_by = st.selectbox(
            "Ordenar por:",
            options=["Nombre", "Stock actual", "Días hasta caducidad"]
        )
    
    # Aplicar filtros
    df_display = df_stock.copy()
    if "Bajo stock" in show_only and "Todo" not in show_only:
        df_display = df_display[df_display["stock_actual"] < df_display["stock_minimo"]]
    
    if "Próximos a caducar" in show_only and "Todo" not in show_only:
        df_display = df_display[df_display["dias_caducidad"] < 5]
    
    # Ordenar
    if sort_by == "Stock actual":
        df_display = df_display.sort_values("stock_actual")
    elif sort_by == "Días hasta caducidad":
        df_display = df_display.sort_values("dias_caducidad")
    else:
        df_display = df_display.sort_values("ingrediente")
    
    # Mostrar tabla con estilo
    st.dataframe(
        df_display.style.apply(style_inventory, axis=1),
        use_container_width=True
    )
    
    # Gráficos complementarios
    tab1, tab2 = st.tabs(["Distribución", "Histórico"])
    with tab1:
        fig = px.pie(df_stock, names="ingrediente", values="stock_actual")
        st.plotly_chart(fig, use_container_width=True)

# ========== (Resto de secciones implementadas de forma similar) ==========

# Nota: Las otras secciones (Menú Semanal, Planificación Personal, etc.) 
# se implementarían con el mismo nivel de detalle y mejoras visuales
