# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
from pymongo import MongoClient

# ======================= CONFIGURACIÓN =======================
st.set_page_config(page_title="Sistema de Estudiantes", page_icon="🎓", layout="wide")

# ======================= USUARIOS =======================
USERS = {
    "admin": "1234",
    "misa": "CADAN09"
}

# ======================= SESIÓN =======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Inicio de Sesión")
    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if usuario in USERS and password == USERS[usuario]:
            st.session_state.logged_in = True
            st.success("✅ Acceso concedido")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
else:
    # ======================= CONEXIÓN MONGODB =======================
    client = MongoClient(
        "mongodb+srv://MISACAST:CADAN09@estudiantes.ddelcua.mongodb.net/?retryWrites=true&w=majority&appName=ESTUDIANTES",
        connect=True,
        serverSelectionTimeoutMS=3000
    )
    db = client["ARCHIVOS-RESIDENCIAS"]
    carreras = ["II", "ISC"]

    # ======================= SIDEBAR =======================
    st.sidebar.title(f"Usuario: {usuario}")
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.markdown("### Menú de Navegación")
    menu = st.sidebar.radio("Selecciona opción:", [
        "🔍 Buscar por Nombre",
        "🔍 Buscar por Número de Control",
        "📖 Ver estudiantes",
        "➕ Agregar estudiante"
    ])

    # ======================= 1. BUSCAR POR NOMBRE =======================
    if menu == "🔍 Buscar por Nombre":
        st.subheader("🔍 Buscar estudiantes por Nombre")
        busqueda_nombre = st.text_input("Escribe el nombre del estudiante:")

        if busqueda_nombre:
            resultados = []
            for carrera in carreras:
                coleccion = db[carrera]
                query = {
                    "NOMBRE (S)": {"$regex": busqueda_nombre.strip(), "$options": "i"}
                }
                resultados.extend(list(coleccion.find(query, {"_id": 0})))
            if resultados:
                df = pd.DataFrame(resultados)
                st.dataframe(df)
            else:
                st.info("No se encontraron coincidencias por nombre.")

    # ======================= 2. BUSCAR POR NÚMERO DE CONTROL =======================
    elif menu == "🔍 Buscar por Número de Control":
        st.subheader("🔍 Buscar estudiantes por Número de Control (solo números)")
        busqueda_num = st.text_input("Escribe el número de control:")

        if busqueda_num:
            if not busqueda_num.isdigit():
                st.warning("⚠️ Solo se permiten números en este campo.")
            else:
                resultados = []
                for carrera in carreras:
                    coleccion = db[carrera]
                    query = {"NUM. CONTROL": int(busqueda_num.strip())}
                    resultados.extend(list(coleccion.find(query, {"_id": 0})))
                if resultados:
                    df = pd.DataFrame(resultados)
                    st.dataframe(df)
                else:
                    st.info("No se encontraron coincidencias por número de control.")

    # ======================= 3. VER ESTUDIANTES =======================
    elif menu == "📖 Ver estudiantes":
        st.subheader("📖 Consultar estudiantes por carrera y periodo")
        carrera = st.selectbox("Selecciona carrera:", carreras)
        if carrera:
            coleccion = db[carrera]
            periodos = coleccion.distinct("PERIODO")
            if periodos:
                periodo = st.selectbox("Selecciona periodo:", periodos)
                if periodo:
                    df_periodo = pd.DataFrame(list(coleccion.find({"PERIODO": periodo}, {"_id": 0})))
                    if not df_periodo.empty:
                        df_periodo["NOMBRE_COMPLETO"] = (
                            df_periodo["NOMBRE (S)"].fillna("") + " " +
                            df_periodo["A. PAT"].fillna("") + " " +
                            df_periodo["A. MAT"].fillna("")
                        )
                        estudiante = st.selectbox("Selecciona un estudiante:", df_periodo["NOMBRE_COMPLETO"].tolist())
                        if estudiante:
                            fila = df_periodo[df_periodo["NOMBRE_COMPLETO"] == estudiante].iloc[0]
                            st.json(fila.to_dict())
            else:
                st.warning("⚠️ No hay periodos en esta carrera.")

    # ======================= 4. AGREGAR ESTUDIANTE =======================
    elif menu == "➕ Agregar estudiante":
        st.subheader("➕ Registrar un nuevo estudiante")
        carrera = st.selectbox("Selecciona carrera:", carreras)
        coleccion = db[carrera]
        periodos = coleccion.distinct("PERIODO")

        with st.form("form_agregar"):
            periodo = st.selectbox("Periodo", periodos + ["Otro"])
            if periodo == "Otro":
                periodo = st.text_input("Nuevo periodo")

            c = st.text_input("Carrera (C)")
            num_control = st.text_input("Número de control")
            sexo = st.text_input("Sexo (H/M)")

            apellido_pat = st.text_input("Apellido Paterno")
            apellido_mat = st.text_input("Apellido Materno")
            nombre = st.text_input("Nombre(s)")

            tema = st.text_area("Tema del proyecto")
            asesor_interno = st.text_input("Asesor Interno")
            asesor_externo = st.text_input("Asesor Externo")
            revisor = st.text_input("Revisor")
            observaciones = st.text_area("Observaciones")
            fecha_dictamen = st.date_input("Fecha de dictamen")

            submitted = st.form_submit_button("Agregar estudiante")
            if submitted:
                if nombre and apellido_pat and num_control:
                    nombre_completo = f"{nombre} {apellido_pat} {apellido_mat}".strip()
                    coleccion.insert_one({
                        "PERIODO": periodo,
                        "C": c,
                        "NUM. CONTROL": int(num_control.strip()) if num_control.isdigit() else num_control,
                        "Unnamed: 3": sexo,
                        "A. PAT": apellido_pat,
                        "A. MAT": apellido_mat,
                        "NOMBRE (S)": nombre,
                        "TEMA": tema,
                        "A. INTERNO": asesor_interno,
                        "A. EXTERNO": asesor_externo,
                        "REVISOR": revisor,
                        "OBSERVACIONES": observaciones,
                        "FECHA DICTAMEN": str(fecha_dictamen),
                        "NOMBRE_COMPLETO": nombre_completo
                    })
                    st.success(f"✅ Estudiante '{nombre_completo}' agregado correctamente.")
                    st.rerun()
                else:
                    st.warning("⚠️ Debes llenar al menos nombre, apellido paterno y número de control.")
