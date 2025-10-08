# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
from pymongo import MongoClient

# ======================= CONFIGURACIÓN STREAMLIT =======================
st.set_page_config(page_title="Sistema de Estudiantes", page_icon="🎓", layout="wide")

# ======================= USUARIOS (login simple) =======================
USERS = {
    "admin": "1234",
    "misa": "CADAN09"
}

# ======================= SESIÓN =======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# ======================= LOGIN =======================
if not st.session_state.logged_in:
    st.title("🔐 Inicio de Sesión")
    usuario_input = st.text_input("Usuario")
    password_input = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if usuario_input in USERS and password_input == USERS[usuario_input]:
            st.session_state.logged_in = True
            st.session_state.usuario = usuario_input  # Guardamos usuario en sesión
            st.success("✅ Acceso concedido")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")

else:
    # ======================= CONEXIÓN A MONGODB =======================
    client = MongoClient(
        "mongodb+srv://MISACAST:CADAN09@estudiantes.ddelcua.mongodb.net/?retryWrites=true&w=majority&appName=ESTUDIANTES",
        connect=True,
        serverSelectionTimeoutMS=3000
    )
    db = client["ARCHIVOS-RESIDENCIAS"]

    # ======================= VARIABLES =======================
    carreras = ["II", "ISC"]

    # ======================= SIDEBAR MENÚ =======================
    st.sidebar.title(f"Usuario: {st.session_state.usuario}")
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.usuario = ""
        st.rerun()

    menu = st.sidebar.radio("Selecciona una opción:", [
        "🏠 Inicio",
        "🔍 Búsqueda universal",
        "📖 Ver estudiantes",
        "➕ Agregar estudiante"
    ])

    # ======================= 1. INTERFAZ INICIO ------------------
    if menu == "🏠 Inicio":
        st.title("🏠 Bienvenido al Sistema de Estudiantes")
        total_estudiantes = sum([db[c].count_documents({}) for c in carreras])
        st.markdown(f"- Total de estudiantes en todas las carreras: **{total_estudiantes}**")
        st.markdown("- Usa el menú lateral para agregar, buscar o consultar estudiantes.")
        for c in carreras:
            count = db[c].count_documents({})
            st.markdown(f"  - Carrera {c}: {count} estudiantes")

    # ======================= 2. BÚSQUEDA UNIVERSAL SIMPLIFICADA =======================
    elif menu == "🔍 Búsqueda universal":
        st.subheader("🔍 Buscar por Número de Control o Nombre(s)")
        busqueda = st.text_input("Escribe número de control o nombre(s):")

        if busqueda:
            resultados = []
            for carrera in carreras:
                coleccion = db[carrera]
                # Búsqueda solo por NUM. CONTROL o NOMBRE (S)
                query = {
                    "$or": [
                        {"NUM.CONTROL": {"$regex": busqueda.strip(), "$options": "i"}},
                        {"NOMBRE (S)": {"$regex": busqueda.strip(), "$options": "i"}}
                    ]
                }
                resultados.extend(list(coleccion.find(query, {"_id": 0})))

            if resultados:
                df = pd.DataFrame(resultados)
                # Crear columna NOMBRE_COMPLETO si no existe
                if "NOMBRE_COMPLETO" not in df.columns:
                    df["NOMBRE_COMPLETO"] = (
                        df["NOMBRE (S)"].fillna("") + " " +
                        df["A. PAT"].fillna("") + " " +
                        df["A. MAT"].fillna("")
                    )
                st.success(f"Se encontraron {len(resultados)} coincidencias")
                # Mostrar tabla interactiva y ordenable
                st.dataframe(df)
            else:
                st.info("No se encontraron coincidencias.")

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
                if nombre and num_control:
                    nombre_completo = f"{nombre} {apellido_pat} {apellido_mat}".strip()
                    coleccion.insert_one({
                        "PERIODO": periodo,
                        "C": c,
                        "NUM. CONTROL": num_control.strip(),
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
                    st.warning("⚠️ Debes llenar al menos nombre y número de control.")
