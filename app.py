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

```
if st.button("Ingresar"):
    if usuario in USERS and password == USERS[usuario]:
        st.session_state.logged_in = True
        st.success("✅ Acceso concedido")
        st.rerun()
    else:
        st.error("❌ Usuario o contraseña incorrectos")
```

else:
# ======================= CONEXIÓN A MONGODB =======================
try:
client = MongoClient(
"mongodb+srv://MISACAST:CADAN09@estudiantes.ddelcua.mongodb.net/?retryWrites=true&w=majority&appName=ESTUDIANTES",
connect=True,
serverSelectionTimeoutMS=3000
)
db = client["ARCHIVOS-RESIDENCIAS"]
except Exception as e:
st.error(f"No se pudo conectar a MongoDB: {e}")
st.stop()

```
# ======================= VARIABLES =======================
carreras = ["II", "ISC"]

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

# ======================= Función de búsqueda robusta =======================
def universal_search(term, carreras, db):
    term = str(term).strip()
    if not term:
        return []

    resultados = []
    is_number = term.isdigit()
    regex_expr = {"$regex": term, "$options": "i"}

    for carrera in carreras:
        coleccion = db[carrera]
        ors = [
            {"NOMBRE (S)": regex_expr},
            {"A. PAT": regex_expr},
            {"A. MAT": regex_expr},
            {"NOMBRE_COMPLETO": regex_expr},
            {"TEMA": regex_expr},
            {"A. INTERNO": regex_expr},
            {"A. EXTERNO": regex_expr},
            {"REVISOR": regex_expr},
        ]

        # Manejo para NUM. CONTROL: puede estar guardado como string o como número.
        # Añadimos ambas opciones (string regex y búsqueda exacta numérica si aplica).
        ors.append({"NUM. CONTROL": regex_expr})
        if is_number:
            try:
                ors.append({"NUM. CONTROL": int(term)})
            except ValueError:
                pass

        query = {"$or": ors}
        try:
            docs = list(coleccion.find(query, {"_id": 0}))
        except Exception:
            docs = []

        # Añadimos el nombre de la carrera al documento para saber de dónde viene.
        for d in docs:
            d["_carrera"] = carrera
        resultados.extend(docs)

    # Quitar duplicados por (NUM. CONTROL, carrera) conservando el primer registro
    seen = set()
    unique = []
    for r in resultados:
        key = (r.get("NUM. CONTROL"), r.get("_carrera"))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique

# ======================= 1. BÚSQUEDA UNIVERSAL =======================
if menu == "🔍 Búsqueda universal":
    st.subheader("🔍 Buscar en toda la base de datos")
    busqueda = st.text_input("Escribe nombre, número de control o tema:")
    buscar_btn = st.button("Buscar")

    # opcion para debug: ver un ejemplo de documento (ayuda a validar nombres de campos)
    if st.checkbox("Mostrar ejemplo de documento (para verificar nombres de campos)"):
        try:
            ejemplo = db[carreras[0]].find_one({}, {"_id": 0})
            if ejemplo:
                st.json(ejemplo)
            else:
                st.info("No hay documentos en la colección de ejemplo.")
        except Exception as e:
            st.error(f"Error al obtener ejemplo: {e}")

    if buscar_btn:
        if not busqueda:
            st.warning("Escribe el término de búsqueda antes de presionar Buscar.")
        else:
            resultados = universal_search(busqueda, carreras, db)
            if resultados:
                df = pd.DataFrame(resultados)

                # Reordenar columnas si existen, mostrando primero lo importante
                preferidas = ["NOMBRE_COMPLETO", "NOMBRE (S)", "A. PAT", "A. MAT", "NUM. CONTROL", "_carrera"]
                cols = [c for c in preferidas if c in df.columns] + [c for c in df.columns if c not in preferidas]
                df = df[cols]
                st.dataframe(df)
            else:
                st.info("No se encontraron coincidencias.")

# ======================= 2. VER ESTUDIANTES =======================
elif menu == "📖 Ver estudiantes":
    st.subheader("📖 Consultar estudiantes por carrera y periodo")

    carrera = st.selectbox("Selecciona carrera:", carreras)
    if carrera:
        coleccion = db[carrera]
        periodos = coleccion.distinct("PERIODO") or []

        if periodos:
            periodo = st.selectbox("Selecciona periodo:", periodos)
            if periodo:
                df_periodo = pd.DataFrame(list(coleccion.find({"PERIODO": periodo}, {"_id": 0})))

                if not df_periodo.empty:
                    df_periodo["NOMBRE_COMPLETO"] = (
                        df_periodo.get("NOMBRE (S)", pd.Series()).fillna("") + " " +
                        df_periodo.get("A. PAT", pd.Series()).fillna("") + " " +
                        df_periodo.get("A. MAT", pd.Series()).fillna("")
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
    periodos = coleccion.distinct("PERIODO") or []

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
```
