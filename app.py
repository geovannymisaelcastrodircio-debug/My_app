# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
from pymongo import MongoClient

# ======================= CONFIGURACIÓN =======================
st.set_page_config(
    page_title="Sistema de Estudiantes",
    page_icon="🎓",
    layout="wide"
)

# ======================= CONEXIÓN A MONGO =======================
client = MongoClient("mongodb+srv://MISACAST:CADAN09@estudiantes.ddelcua.mongodb.net/?retryWrites=true&w=majority&appName=ESTUDIANTES")
db = client["ESTUDIANTES"]
collection = db["estudiantes"]

# ======================= FUNCIÓN DE BÚSQUEDA =======================
def buscar_estudiantes(numero_control=None, tema=None):
    query = {}

    if numero_control and not tema:
        query = {
            "$or": [
                {"NUM. CONTROL": str(numero_control).strip()},
                {"NUM. CONTROL": {"$regex": str(numero_control).strip(), "$options": "i"}}
            ]
        }
    elif tema and not numero_control:
        query = {
            "TEMA": {"$regex": tema.strip(), "$options": "i"}
        }
    elif numero_control and tema:
        query = {
            "$and": [
                {"NUM. CONTROL": {"$regex": str(numero_control).strip(), "$options": "i"}},
                {"TEMA": {"$regex": tema.strip(), "$options": "i"}}
            ]
        }
    else:
        return []

    resultados = list(collection.find(query, {"_id": 0}))
    return resultados

# ======================= FUNCIÓN PARA AGREGAR ESTUDIANTES =======================
def agregar_estudiante(datos):
    if datos.get("NUM. CONTROL") and datos.get("NOMBRE") and datos.get("TEMA"):
        # Convertimos NUM. CONTROL a string para uniformidad
        datos["NUM. CONTROL"] = str(datos["NUM. CONTROL"]).strip()
        collection.insert_one(datos)
        return True
    return False

# ======================= INTERFAZ =======================
st.title("📚 Sistema de Estudiantes")

# ---- SECCIÓN AGREGAR ESTUDIANTE ----
st.header("➕ Agregar nuevo estudiante")
with st.form("form_agregar"):
    nombre = st.text_input("Nombre completo")
    numero_control = st.text_input("Número de control")
    tema = st.text_input("Tema")
    otros = st.text_area("Otros datos (opcional)")
    
    submitted = st.form_submit_button("Agregar estudiante")
    if submitted:
        datos_estudiante = {
            "NOMBRE": nombre.strip(),
            "NUM. CONTROL": numero_control.strip(),
            "TEMA": tema.strip(),
            "OTROS": otros.strip()
        }
        if agregar_estudiante(datos_estudiante):
            st.success(f"Estudiante {nombre} agregado correctamente ✅")
        else:
            st.error("Por favor, completa todos los campos obligatorios (Nombre, Número de control, Tema).")

# ---- SECCIÓN BUSCAR ESTUDIANTES ----
st.header("🔍 Buscar estudiante")
numero_control_input = st.text_input("Número de control (opcional)", key="buscar_num")
tema_input = st.text_input("Tema (opcional)", key="buscar_tema")

if st.button("Buscar"):
    resultados = buscar_estudiantes(numero_control=numero_control_input, tema=tema_input)
    
    if resultados:
        df = pd.DataFrame(resultados)
        st.success(f"Se encontraron {len(resultados)} resultado(s):")
        st.dataframe(df)
    else:
        st.warning("No se encontraron resultados.")

# ---- BOTÓN PARA MOSTRAR TODOS LOS ESTUDIANTES ----
st.header("📋 Todos los estudiantes")
if st.button("Mostrar todos"):
    todos = list(collection.find({}, {"_id": 0}))
    if todos:
        df_todos = pd.DataFrame(todos)
        st.success(f"Se encontraron {len(todos)} estudiantes en la base de datos:")
        st.dataframe(df_todos)
    else:
        st.warning("La base de datos está vacía.")
