# app.py (v2 mejorada)
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="IA para Restaurantes", layout="wide")

# Sidebar
st.sidebar.title("📊 Panel de Control")
page = st.sidebar.radio("Ir a:", ["Predicción", "Inventario", "Menú del Día", "Personal"])

uploaded_file = st.sidebar.file_uploader("📁 Subir archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer las hojas
    ventas = pd.read_excel(uploaded_file, sheet_name="ventas")
    ingredientes = pd.read_excel(uploaded_file, sheet_name="ingredientes")
    stock = pd.read_excel(uploaded_file, sheet_name="stock")

    # --- PREDICCIÓN ---
    if page == "Predicción":
        st.title("🔮 Predicción de Demanda")

        dias_futuros = st.selectbox("Selecciona rango de predicción:", [7, 14, 30])
        hoy = datetime.today()
        fechas = [hoy + timedelta(days=i) for i in range(dias_futuros)]
        dias_semana = [f.strftime("%A") for f in fechas]

        media_ventas = ventas.groupby("dia_semana")["unidades"].mean()
        predicciones = [media_ventas.get(dia, media_ventas.mean()) for dia in dias_semana]

        df_pred = pd.DataFrame({"Fecha": fechas, "Demanda Estimada": predicciones})
        fig = px.line(df_pred, x="Fecha", y="Demanda Estimada", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    # --- INVENTARIO ---
    elif page == "Inventario":
        st.title("📦 Gestión de Inventario")

        stock["estado"] = "✅ OK"
        stock.loc[stock["stock_actual"] < stock["stock_minimo"], "estado"] = "🔴 Bajo Stock"
        stock.loc[stock["fecha_caducidad"] < datetime.today() + timedelta(days=3), "estado"] = "🟠 Próximo a Caducar"

        st.dataframe(stock.sort_values("estado"))

        alertas = stock[stock["estado"] != "✅ OK"]
        if not alertas.empty:
            st.warning("⚠️ Ingredientes con incidencias:")
            st.dataframe(alertas)
        else:
            st.success("Todo en orden ✅")

    # --- MENÚ DEL DÍA ---
    elif page == "Menú del Día":
        st.title("📋 Recomendación de Menú Diario")

        # Platos disponibles con stock suficiente
        disponibles = []
        for plato in ingredientes["plato"].unique():
            sub = ingredientes[ingredientes["plato"] == plato]
            suficiente = True
            for _, row in sub.iterrows():
                ing = row["ingrediente"]
                cantidad = row["cantidad_por_plato"]
                stock_actual = stock.loc[stock["ingrediente"] == ing, "stock_actual"].values
                if len(stock_actual) == 0 or stock_actual[0] < cantidad:
                    suficiente = False
                    break
            if suficiente:
                disponibles.append(plato)

        # Ordenar por caducidad de ingredientes involucrados
        menu = []
        for plato in disponibles:
            caducidades = []
            for ing in ingredientes[ingredientes["plato"] == plato]["ingrediente"]:
                cad = stock.loc[stock["ingrediente"] == ing, "fecha_caducidad"].values
                if len(cad):
                    caducidades.append(cad[0])
            fecha_min = min(caducidades) if caducidades else datetime.max
            menu.append((plato, fecha_min))

        menu_ordenado = sorted(menu, key=lambda x: x[1])[:3]
        st.markdown("### Menú sugerido para hoy:")
        for plato, fecha in menu_ordenado:
            st.markdown(f"- **{plato}** (usar antes del {pd.to_datetime(fecha).date()})")

    # --- PERSONAL ---
    elif page == "Personal":
        st.title("👨‍🍳 Planificación de Personal")

        dias = 7
        hoy = datetime.today()
        fechas = [hoy + timedelta(days=i) for i in range(dias)]
        dias_semana = [f.strftime("%A") for f in fechas]

        media_ventas = ventas.groupby("dia_semana")["unidades"].mean()
        predicciones = [media_ventas.get(dia, media_ventas.mean()) for dia in dias_semana]

        df_staff = pd.DataFrame({
            "Fecha": fechas,
            "Demanda Estimada": predicciones,
        })
        df_staff["Cocineros"] = (df_staff["Demanda Estimada"] / 30).apply(lambda x: max(1, round(x)))
        df_staff["Camareros"] = (df_staff["Demanda Estimada"] / 25).apply(lambda x: max(1, round(x)))

        st.dataframe(df_staff)

else:
    st.warning("📌 Por favor, sube el archivo Excel con los datos del mes.")

