
import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import date

# ======================= CONFIGURACIÓN =======================
st.set_page_config(page_title="Gestión de Estudiantes", layout="wide")

# ======================= CONEXIÓN A MONGODB =======================
# Reemplaza con tus credenciales reales
USUARIO = "MISACAST"
CONTRASEÑA = "CADAN09"
CLUSTER = "estudiantes.ddelcua.mongodb.net"
BD = "ESTUDIANTES"
COL = "ALUMNOS"

uri = f"mongodb+srv://{USUARIO}:{CONTRASEÑA}@{CLUSTER}/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client[BD]
collection = db[COL]

# ======================= FUNCIÓN LOGIN =======================
def login(usuario, contrasena):
    if usuario == "admin" and contrasena == "1234":
        return True
    elif usuario == "invitado" and contrasena == "0000":
        return True
    else:
        return False

# ======================= SESIÓN DE USUARIO =======================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""

if not st.session_state.autenticado:
    st.sidebar.title("🔒 Iniciar sesión")
    usuario = st.sidebar.text_input("Usuario")
    contrasena = st.sidebar.text_input("Contraseña", type="password")

    if st.sidebar.button("Entrar"):
        if login(usuario, contrasena):
            st.session_state.autenticado = True
            st.session_state.usuario = usuario
            st.success(f"Bienvenido, {usuario}")
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

# ======================= FUNCIÓNES PRINCIPALES =======================
def mostrar_datos():
    datos = list(collection.find())
    if not datos:
        st.warning("No hay datos en la base.")
    else:
        df = pd.DataFrame(datos)
        st.dataframe(df)

def buscar_estudiante(busqueda):
    query = {
        "$or": [
            {"NOMBRE": {"$regex": busqueda, "$options": "i"}},
            {"NUM. CONTROL": {"$regex": busqueda, "$options": "i"}}
        ]
    }
    resultados = list(collection.find(query))
    return resultados

def actualizar_estudiante(id_estudiante, nuevos_datos):
    collection.update_one({"_id": id_estudiante}, {"$set": nuevos_datos})

# ======================= INTERFAZ PRINCIPAL =======================
st.sidebar.title(f"👤 Usuario: {st.session_state.usuario}")
menu = st.sidebar.radio("Menú", ["Mostrar", "Agregar", "Buscar / Editar"])

st.title("🎓 Sistema de Gestión de Estudiantes")

# ---------- MOSTRAR ----------
if menu == "Mostrar":
    mostrar_datos()

# ---------- AGREGAR ----------
elif menu == "Agregar":
    st.subheader("Agregar nuevo estudiante")
    with st.form("form_agregar"):
        num_control = st.text_input("Número de control")
        nombre = st.text_input("Nombre completo")
        carrera = st.text_input("Carrera")
        semestre = st.number_input("Semestre", min_value=1, max_value=12, step=1)
        fecha_dictamen = st.date_input(
            "Fecha de dictamen",
            value=date.today(),
            min_value=date(1900, 1, 1),
            max_value=date(2030, 12, 31)
        )
        tema = st.text_input("Tema")

        enviado = st.form_submit_button("Agregar estudiante")
        if enviado:
            nuevo = {
                "NUM. CONTROL": num_control,
                "NOMBRE": nombre,
                "CARRERA": carrera,
                "SEMESTRE": semestre,
                "FECHA DICTAMEN": str(fecha_dictamen),
                "TEMA": tema
            }
            collection.insert_one(nuevo)
            st.success("✅ Estudiante agregado correctamente.")

# ---------- BUSCAR Y EDITAR ----------
elif menu == "Buscar / Editar":
    st.subheader("Buscar estudiante para editar datos")
    busqueda = st.text_input("Buscar por nombre o número de control")

    if busqueda:
        resultados = buscar_estudiante(busqueda)
        if not resultados:
            st.warning("No se encontraron coincidencias.")
        else:
            for fila in resultados:
                with st.expander(f"Editar: {fila.get('NOMBRE', 'Sin nombre')}"):
                    with st.form(f"form_{fila['_id']}"):
                        num_control = st.text_input("Número de control", value=fila.get("NUM. CONTROL", ""))
                        nombre = st.text_input("Nombre completo", value=fila.get("NOMBRE", ""))
                        carrera = st.text_input("Carrera", value=fila.get("CARRERA", ""))
                        semestre = st.number_input(
                            "Semestre", min_value=1, max_value=12, step=1,
                            value=int(fila.get("SEMESTRE", 1))
                        )

                        fecha_valor = fila.get("FECHA DICTAMEN", "2000-01-01")
                        fecha_dictamen = st.date_input(
                            "Fecha dictamen",
                            value=pd.to_datetime(fecha_valor, errors="coerce").date()
                            if pd.notna(pd.to_datetime(fecha_valor, errors="coerce"))
                            else date(2000, 1, 1),
                            min_value=date(1900, 1, 1),
                            max_value=date(2030, 12, 31)
                        )
                        tema = st.text_input("Tema", value=fila.get("TEMA", ""))

                        actualizar = st.form_submit_button("💾 Actualizar")
                        if actualizar:
                            nuevos_datos = {
                                "NUM. CONTROL": num_control,
                                "NOMBRE": nombre,
                                "CARRERA": carrera,
                                "SEMESTRE": semestre,
                                "FECHA DICTAMEN": str(fecha_dictamen),
                                "TEMA": tema
                            }
                            actualizar_estudiante(fila["_id"], nuevos_datos)
                            st.success("✅ Datos actualizados correctamente.")

