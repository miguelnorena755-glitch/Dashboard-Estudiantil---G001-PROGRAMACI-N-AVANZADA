# app.py
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt

# =====================
# CONFIGURACIÓN GENERAL
# =====================
st.set_page_config(page_title="Dashboard Estudiantil", layout="wide")

st.title("Dashboard Estudiantil - G001 PROGRAMACIÓN AVANZADA")
st.subheader("Hecho por: ALEX DANIEL, MIGUEL ANGEL, JHOAN SEBASTIÁN, JULIAN, FRAY DURNEY")
st.subheader("https://docs.google.com/spreadsheets/d/1x2-9xFM30Nfg9aX0gcsGp8pOgQsoRqmcAjY474oP6JU/edit?gid=0#gid=0")
st.subheader("Datos de estudiantes")

# =====================
# CARGA DE DATOS DESDE GOOGLE SHEETS
# =====================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1x2-9xFM30Nfg9aX0gcsGp8pOgQsoRqmcAjY474oP6JU/export?format=csv"

try:
    df = pd.read_csv(SHEET_CSV_URL)
    st.caption("Fuente de datos: Google Sheets (vínculo compartido)")
except Exception as e:
    st.error(f"No se pudieron cargar los datos desde Google Sheets.\nDetalle: {e}")
    st.stop()

# =====================
# FUNCIONES AUXILIARES
# =====================
def calcular_edad(fecha_nac):
    if pd.isna(fecha_nac):
        return np.nan
    hoy = pd.Timestamp.today()
    return int((hoy - fecha_nac).days // 365.25)

def clasificar_imc(imc):
    if pd.isna(imc):
        return "Sin datos"
    if imc < 18.5:
        return "Bajo peso"
    elif imc < 25:
        return "Normal"
    elif imc < 30:
        return "Sobrepeso"
    elif imc < 35:
        return "Obesidad I"
    elif imc < 40:
        return "Obesidad II"
    else:
        return "Obesidad III"

def df_to_excel_bytes(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Hoja1")
    buffer.seek(0)
    return buffer

# =====================
# PROCESAMIENTO DE DATOS
# =====================
df.columns = [col.strip() for col in df.columns]

# Fecha de nacimiento → datetime y Edad
if "Fecha_Nacimiento" in df.columns:
    df["Fecha_Nacimiento"] = pd.to_datetime(df["Fecha_Nacimiento"], errors="coerce")
    df["Edad"] = df["Fecha_Nacimiento"].apply(calcular_edad)
else:
    df["Edad"] = np.nan

# Conversión robusta de Estatura y Peso a numérico
# Soporta valores tipo "1,75" o "70,5"
df["Estatura"] = (
    df["Estatura"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)
df["Peso"] = (
    df["Peso"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)

df["Estatura"] = pd.to_numeric(df["Estatura"], errors="coerce")
df["Peso"] = pd.to_numeric(df["Peso"], errors="coerce")

# Estatura a cm (si viene en metros)
df["Estatura_cm"] = df["Estatura"] * 100

# IMC = Peso / (Estatura en metros)^2
est_m = df["Estatura_cm"] / 100
df["IMC"] = df["Peso"] / (est_m ** 2)

df["Clasificación_IMC"] = df["IMC"].apply(clasificar_imc)

# Nombre completo (por si lo necesitas en filtros)
if "Nombre_Estudiante" in df.columns and "Apellido_Estudiante" in df.columns:
    df["Nombre_Completo"] = (
        df["Nombre_Estudiante"].astype(str).str.strip() + " " +
        df["Apellido_Estudiante"].astype(str).str.strip()
    )
else:
    df["Nombre_Completo"] = np.nan


# =====================
# FILTROS MULTISELECT
# =====================
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    nombres_opts = sorted(df["Nombre_Completo"].dropna().unique())
    if len(nombres_opts) > 0:
        nombres_sel = st.multiselect(
            "Nombre del Estudiante",
            nombres_opts,
            default=nombres_opts
        )
    else:
        nombres_sel = None
        st.write("Sin datos de nombres completos")

with col_f2:
    rh_opts = sorted(df["RH"].dropna().unique())
    rh_sel = st.multiselect("Tipo de Sangre (RH)", rh_opts, default=rh_opts)

with col_f3:
    cab_opts = sorted(df["Color_Cabello"].dropna().unique())
    cab_sel = st.multiselect("Color de Cabello", cab_opts, default=cab_opts)

with col_f4:
    bar_opts = sorted(df["Barrio_Residencia"].dropna().unique())
    bar_sel = st.multiselect("Barrio de Residencia", bar_opts, default=bar_opts)

df_filtrado = df.copy()

if nombres_sel is not None:
    df_filtrado = df_filtrado[df_filtrado["Nombre_Completo"].isin(nombres_sel)]

df_filtrado = df_filtrado[
    df_filtrado["RH"].isin(rh_sel) &
    df_filtrado["Color_Cabello"].isin(cab_sel) &
    df_filtrado["Barrio_Residencia"].isin(bar_sel)
]

if df_filtrado.empty:
    st.warning("No hay registros con los filtros seleccionados.")
    st.stop()

# =====================
# SLIDERS: RANGO EDAD Y ESTATURA
# =====================
st.markdown("### Rangos")
s1, s2 = st.columns(2)

with s1:
    edad_min = int(df_filtrado["Edad"].min())
    edad_max = int(df_filtrado["Edad"].max())
    rango_edad = st.slider("Rango de Edad", edad_min, edad_max, (edad_min, edad_max))

with s2:
    est_min = float(df_filtrado["Estatura_cm"].min())
    est_max = float(df_filtrado["Estatura_cm"].max())
    rango_est = st.slider(
        "Rango de Estatura (cm)",
        float(round(est_min, 1)),
        float(round(est_max, 1)),
        (float(round(est_min, 1)), float(round(est_max, 1)))
    )

df_filtrado = df_filtrado[
    (df_filtrado["Edad"] >= rango_edad[0]) &
    (df_filtrado["Edad"] <= rango_edad[1]) &
    (df_filtrado["Estatura_cm"] >= rango_est[0]) &
    (df_filtrado["Estatura_cm"] <= rango_est[1])
]

if df_filtrado.empty:
    st.warning("No hay registros después de aplicar los rangos.")
    st.stop()

st.markdown("---")

# =====================
# INDICADORES (KPIs)
# =====================
st.subheader("Indicadores")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Estudiantes", len(df_filtrado))
k2.metric("Edad Promedio", f"{df_filtrado['Edad'].mean():.1f}")
k3.metric("Estatura Promedio (cm)", f"{df_filtrado['Estatura_cm'].mean():.1f}")
k4.metric("Peso Promedio (kg)", f"{df_filtrado['Peso'].mean():.1f}")
k5.metric("IMC Promedio", f"{df_filtrado['IMC'].mean():.1f}")

st.markdown("---")

# =====================
# GRÁFICOS - FILA 1
# =====================
st.subheader("Gráficos - Fila 1")
g1, g2 = st.columns(2)

with g1:
    st.write("Distribución por Edad")
    edad_counts = df_filtrado["Edad"].value_counts().sort_index()
    st.bar_chart(edad_counts)

with g2:
    st.write("Distribución por Tipo de Sangre (RH)")
    rh_counts = df_filtrado["RH"].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(rh_counts.values, labels=rh_counts.index, autopct="%1.1f%%")
    ax1.axis("equal")
    st.pyplot(fig1)

# =====================
# GRÁFICOS - FILA 2
# =====================
st.subheader("Gráficos - Fila 2")
g3, g4 = st.columns(2)

with g3:
    st.write("Relación Estatura vs Peso (Scatter)")
    fig2, ax2 = plt.subplots()
    ax2.scatter(df_filtrado["Estatura_cm"], df_filtrado["Peso"])
    ax2.set_xlabel("Estatura (cm)")
    ax2.set_ylabel("Peso (kg)")
    st.pyplot(fig2)

with g4:
    st.write("Distribución por Color de Cabello")
    cab_counts = df_filtrado["Color_Cabello"].value_counts()
    st.bar_chart(cab_counts)

# =====================
# GRÁFICOS - FILA 3
# =====================
st.subheader("Gráficos - Fila 3")
g5, g6 = st.columns(2)

with g5:
    st.write("Distribución de Tallas de Zapatos (Línea)")
    talla_counts = df_filtrado["Talla_Zapato"].value_counts().sort_index()
    st.line_chart(talla_counts)

with g6:
    st.write("Top 10 Barrios de Residencia")
    barrio_counts = df_filtrado["Barrio_Residencia"].value_counts().head(10)
    st.bar_chart(barrio_counts)

st.markdown("---")

# =====================
# TOP 5 ESTATURA Y PESO
# =====================
st.subheader("Top 5 Estatura y Peso")

top_est = df_filtrado.sort_values("Estatura_cm", ascending=False).head(5)
top_peso = df_filtrado.sort_values("Peso", ascending=False).head(5)

c1, c2 = st.columns(2)
with c1:
    st.write("Top 5 Mayor Estatura")
    st.dataframe(top_est, use_container_width=True)
    st.download_button(
        "Descargar Top 5 Estatura",
        df_to_excel_bytes(top_est),
        file_name="top5_estatura.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with c2:
    st.write("Top 5 Mayor Peso")
    st.dataframe(top_peso, use_container_width=True)
    st.download_button(
        "Descargar Top 5 Peso",
        df_to_excel_bytes(top_peso),
        file_name="top5_peso.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")

# =====================
# RESUMEN ESTADÍSTICO
# =====================
st.subheader("Resumen estadístico (Estatura, Peso, IMC)")

stats = pd.DataFrame({
    "Estatura (cm)": df_filtrado["Estatura_cm"].describe(),
    "Peso (kg)": df_filtrado["Peso"].describe(),
    "IMC": df_filtrado["IMC"].describe()
})

stats = stats.rename(index={
    "count": "Cantidad de datos",
    "mean": "Promedio",
    "std": "Desviación estándar",
    "min": "Mínimo",
    "25%": "Percentil 25",
    "50%": "Mediana (50%)",
    "75%": "Percentil 75",
    "max": "Máximo"
})

stats = stats.round(2)

st.dataframe(stats, use_container_width=True)
