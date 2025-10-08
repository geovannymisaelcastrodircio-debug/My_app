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

# ======================= USUARIOS =======================
USUARIOS = {
    "admin": "1234",
    "geovanny": "abcd"
}

# ======================= LOGIN =======================
if "login" not in st.session_state:
    st.session_state.login = False

def login(usuario, contrasena):
    if usuario in USUARIOS and USUARIOS[usuario] == contrasena:
        st.session_state.login = True
        st.session_state.usuario = usuario
        return True
    else:
        st.error("Usuario o contraseña incorrectos")
        return False

if not st.session_state.login:
    st.title("🔒 Login")
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        login(usuario_input, contrasena_input)
    st.stop()

# ======================= CONEXIÓN A MONGO =======================
client = MongoClient("mongodb+srv://MISACAST:CADAN09@estudiantes.ddelcua.mongodb.net/?retryWrites=true&w=majority&appName=ESTUDIANTES")
db = client["ESTUDIANTES"]
collection = db["estudiantes"]

# ======================= FUNCIONES =======================
def buscar_estudiantes(nombre=None, numero_control=None, tema=None):
    query = []
    if nombre:
        query.append({"NOMBRE": {"$regex": nombre.strip(), "$options": "i"}})
    if numero_control:
        query.append({"NUM. CONTROL": {"$regex": str(numero_control).strip(), "$options": "i"}})
    if tema:
        query.append({"TEMA": {"$regex": tema.strip(), "$options": "i"}})
    if not query:
        return []
    final_query = query[0] if len(query) == 1 else {"$and": query}
    return list(collection.find(final_query, {"_id": 0}))

def agregar_estudiante(datos):
    if datos.get("NUM. CONTROL") and datos.get("NOMBRE") and datos.get("TEMA"):
        datos["NUM. CONTROL"] = str(datos["NUM. CONTROL"]).strip()
        collection.insert_one(datos)
        return True
    return False

def mostrar_todos():
    return list(collection.find({}, {"_id": 0}))

# ======================= MENÚ LATERAL =======================
st.sidebar.title(f"Usuario: {st.session_state.usuario}")
menu = st.sidebar.radio("Navegación", ["Inicio", "Agregar estudiante", "Buscar estudiante", "Mostrar todos"])

# ======================= SECCIONES =======================
# ----- INICIO -----
if menu == "Inicio":
    st.title("🏠 Bienvenido al Sistema de Estudiantes")
    total = collection.count_documents({})
    st.markdown(f"- Total de estudiantes en la base: **{total}**")
    st.markdown("Usa el menú lateral para agregar, buscar o mostrar estudiantes.")

# ----- AGREGAR ESTUDIANTE -----
elif menu == "Agregar estudiante":
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

# ----- BUSCAR ESTUDIANTE -----
elif menu == "Buscar estudiante":
    st.header("🔍 Buscar estudiante")
    nombre_input = st.text_input("Nombre (opcional)", key="buscar_nombre")
    numero_control_input = st.text_input("Número de control (opcional)", key="buscar_num")
    tema_input = st.text_input("Tema (opcional)", key="buscar_tema")
    if st.button("Buscar"):
        resultados = buscar_estudiantes(nombre=nombre_input, numero_control=numero_control_input, tema=tema_input)
        if resultados:
            df = pd.DataFrame(resultados)
            st.success(f"Se encontraron {len(resultados)} resultado(s):")
            st.dataframe(df)
        else:
            st.warning("No se encontraron resultados.")

# ----- MOSTRAR TODOS -----
elif menu == "Mostrar todos":
    st.header("📋 Todos los estudiantes")
    todos = mostrar_todos()
    if todos:
        df_todos = pd.DataFrame(todos)
        st.success(f"Se encontraron {len(todos)} estudiantes en la base de datos:")
        st.dataframe(df_todos)
    else:
        st.warning("La base de datos está vacía.")
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

# ======================= USUARIOS =======================
USUARIOS = {
    "admin": "1234",
    "geovanny": "abcd"
}

# ======================= LOGIN =======================
if "login" not in st.session_state:
    st.session_state.login = False

def login(usuario, contrasena):
    if usuario in USUARIOS and USUARIOS[usuario] == contrasena:
        st.session_state.login = True
        st.session_state.usuario = usuario
        return True
    else:
        st.error("Usuario o contraseña incorrectos")
        return False

if not st.session_state.login:
    st.title("🔒 Login")
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        login(usuario_input, contrasena_input)
    st.stop()

# ======================= CONEXIÓN A MONGO =======================
client = MongoClient("mongodb+srv://MISACAST:CADAN09@estudiantes.ddelcua.mongodb.net/?retryWrites=true&w=majority&appName=ESTUDIANTES")
db = client["ESTUDIANTES"]
collection = db["estudiantes"]

# ======================= FUNCIONES =======================
def buscar_estudiantes(nombre=None, numero_control=None, tema=None):
    query = []
    if nombre:
        query.append({"NOMBRE": {"$regex": nombre.strip(), "$options": "i"}})
    if numero_control:
        query.append({"NUM. CONTROL": {"$regex": str(numero_control).strip(), "$options": "i"}})
    if tema:
        query.append({"TEMA": {"$regex": tema.strip(), "$options": "i"}})
    if not query:
        return []
    final_query = query[0] if len(query) == 1 else {"$and": query}
    return list(collection.find(final_query, {"_id": 0}))

def agregar_estudiante(datos):
    if datos.get("NUM. CONTROL") and datos.get("NOMBRE") and datos.get("TEMA"):
        datos["NUM. CONTROL"] = str(datos["NUM. CONTROL"]).strip()
        collection.insert_one(datos)
        return True
    return False

def mostrar_todos():
    return list(collection.find({}, {"_id": 0}))

# ======================= MENÚ LATERAL =======================
st.sidebar.title(f"Usuario: {st.session_state.usuario}")
menu = st.sidebar.radio("Navegación", ["Inicio", "Agregar estudiante", "Buscar estudiante", "Mostrar todos"])

# ======================= SECCIONES =======================
# ----- INICIO -----
if menu == "Inicio":
    st.title("🏠 Bienvenido al Sistema de Estudiantes")
    total = collection.count_documents({})
    st.markdown(f"- Total de estudiantes en la base: **{total}**")
    st.markdown("Usa el menú lateral para agregar, buscar o mostrar estudiantes.")

# ----- AGREGAR ESTUDIANTE -----
elif menu == "Agregar estudiante":
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

# ----- BUSCAR ESTUDIANTE -----
elif menu == "Buscar estudiante":
    st.header("🔍 Buscar estudiante")
    nombre_input = st.text_input("Nombre (opcional)", key="buscar_nombre")
    numero_control_input = st.text_input("Número de control (opcional)", key="buscar_num")
    tema_input = st.text_input("Tema (opcional)", key="buscar_tema")
    if st.button("Buscar"):
        resultados = buscar_estudiantes(nombre=nombre_input, numero_control=numero_control_input, tema=tema_input)
        if resultados:
            df = pd.DataFrame(resultados)
            st.success(f"Se encontraron {len(resultados)} resultado(s):")
            st.dataframe(df)
        else:
            st.warning("No se encontraron resultados.")

# ----- MOSTRAR TODOS -----
elif menu == "Mostrar todos":
    st.header("📋 Todos los estudiantes")
    todos = mostrar_todos()
    if todos:
        df_todos = pd.DataFrame(todos)
        st.success(f"Se encontraron {len(todos)} estudiantes en la base de datos:")
        st.dataframe(df_todos)
    else:
        st.warning("La base de datos está vacía.")
