
# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
from pymongo import MongoClient

# ======================= CONFIGURACIÓN STREAMLIT =======================
st.set_page_config(page_title="Sistema de Estudiantes", page_icon="🎓", layout="wide")

# ======================= USUARIOS (login simple en el mismo archivo) =======================
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
    # ======================= CONEXIÓN A MONGODB =======================
    try:
        client = MongoClient(
            "mongodb+srv://MISACAST:CADAN09@estudiantes.ddelcua.mongodb.net/?retryWrites=true&w=majority",
            connect=True,
            serverSelectionTimeoutMS=3000
        )
        db = client["ARCHIVOS-RESIDENCIAS"]
        carreras = ["II", "ISC"]
    except Exception as e:
        st.error(f"❌ Error al conectar con MongoDB: {e}")
        st.stop()

    # ======================= SIDEBAR MENÚ =======================
    st.sidebar.title("📌 Menú de Navegación")
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.rerun()

    menu = st.sidebar.radio("Selecciona una opción:", [
        "🔍 Búsqueda universal",
        "📖 Ver estudiantes",
        "➕ Agregar estudiante",
        "🗑 Eliminar estudiante"
    ])

    # ======================= FUNCIÓN DE BÚSQUEDA UNIVERSAL =======================
    def buscar_dato(busqueda, db, carreras):
        resultados = []
        for carrera in carreras:
            coleccion = db[carrera]
            query = {
                "$or": [
                    {"NOMBRE (S)": {"$regex": busqueda, "$options": "i"}},
                    {"A. PAT": {"$regex": busqueda, "$options": "i"}},
                    {"A. MAT": {"$regex": busqueda, "$options": "i"}},
                    {"NUM. CONTROL": {"$regex": busqueda, "$options": "i"}},
                    {"TEMA": {"$regex": busqueda, "$options": "i"}},
                    {"A. INTERNO": {"$regex": busqueda, "$options": "i"}},
                    {"A. EXTERNO": {"$regex": busqueda, "$options": "i"}},
                    {"REVISOR": {"$regex": busqueda, "$options": "i"}},
                ]
            }
            resultados.extend(list(coleccion.find(query, {"_id": 0})))
        return resultados

    # ======================= 1. BÚSQUEDA UNIVERSAL =======================
    if menu == "🔍 Búsqueda universal":
        st.subheader("🔍 Buscar en toda la base de datos")
        busqueda = st.text_input("Escribe nombre, número de control o tema:")

        if busqueda:
            resultados = buscar_dato(busqueda, db, carreras)
            if resultados:
                st.dataframe(pd.DataFrame(resultados))
            else:
                st.info("No se encontraron coincidencias.")

    # ======================= 2. VER ESTUDIANTES =======================
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

    # ======================= 3. AGREGAR ESTUDIANTE =======================
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
                        "NUM. CONTROL": num_control,
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

    # ======================= 4. ELIMINAR ESTUDIANTE =======================
    elif menu == "🗑 Eliminar estudiante":
        st.subheader("🗑 Eliminar estudiante")
        carrera = st.selectbox("Selecciona carrera:", carreras)
        coleccion = db[carrera]

        numero_eliminar = st.text_input("Número de control a eliminar")
        periodo = st.text_input("Periodo del estudiante")
        if st.button("Eliminar"):
            if numero_eliminar and periodo:
                result = coleccion.delete_one({"NUM. CONTROL": numero_eliminar, "PERIODO": periodo})
                if result.deleted_count > 0:
                    st.success(f"✅ Estudiante con número {numero_eliminar} eliminado.")
                    st.rerun()
                else:
                    st.error("❌ No se encontró estudiante con ese número y periodo.")

