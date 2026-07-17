import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# Configuración de la interfaz
st.set_page_config(page_title="Registro de Huéspedes", page_icon="🏨", layout="wide")

# Conexión Segura a la Base de Datos Local
conn = sqlite3.connect("registro_hotel.db", check_same_thread=False)
cursor = conn.cursor()

# Creación de tablas base
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    correo TEXT PRIMARY KEY,
    contrasena TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS huespedes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habitacion TEXT,
    hora TEXT,
    dia TEXT,
    mes TEXT,
    nombres TEXT,
    documento TEXT,
    procedencia TEXT,
    tarifa REAL,
    estado_pago TEXT
)
""")
conn.commit()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Crear usuario administrador inicial por defecto
def iniciar_admin():
    correo_admin = "admin@hotel.com"
    pass_hash = hash_password("1234")
    try:
        cursor.execute("INSERT INTO usuarios (correo, contrasena) VALUES (?, ?)", (correo_admin, pass_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

iniciar_admin()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# --- PANTALLA DE INICIO DE SESIÓN ---
if not st.session_state["autenticado"]:
    st.title("🏨 Control de Acceso - Registro de Huéspedes")
    
    col1, _ = st.columns([1, 2])
    with col1:
        with st.form("login_form"):
            st.subheader("Iniciar Sesión")
            correo = st.text_input("Correo Electrónico")
            contrasena = st.text_input("Contraseña", type="password")
            boton_login = st.form_submit_button("Ingresar")
            
            if boton_login:
                cursor.execute("SELECT contrasena FROM usuarios WHERE correo = ?", (correo,))
                resultado = cursor.fetchone()
                if resultado and resultado[0] == hash_password(contrasena):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario"] = correo
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos")
else:
    # --- SISTEMA INTERNO ---
    st.sidebar.title("Navegación")
    st.sidebar.write(f"👤 Usuario: **{st.session_state['usuario']}**")
    opcion = st.sidebar.radio("Ir a:", ["Registrar Huésped", "Ver Historial y Reportes"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

    if opcion == "Registrar Huésped":
        st.title("📝 Formulario de Registro de Huéspedes")
        
        with st.form("registro_huesped"):
            col1, col2, col3 = st.columns(3)
            with col1:
                habitacion = st.text_input("Número de Habitación")
                hora = st.text_input("Hora de Ingreso", value=datetime.now().strftime("%H:%M"))
                dia = st.text_input("Día", value=datetime.now().strftime("%d"))
                mes = st.text_input("Mes (Número)", value=datetime.now().strftime("%m"))
            
            with col2:
                nombres = st.text_input("Nombres y Apellidos Completos")
                documento = st.text_input("Documento de Identidad")
                procedencia = st.text_input("Lugar de Nacimiento")
            
            with col3:
                tarifa = st.number_input("Tarifa / Precio (S/)", min_value=0.0, step=10.0)
                estado_pago = st.selectbox("Estado del Pago", ["Pagado", "Pendiente"])
            
            enviar = st.form_submit_button("Guardar Registro")
            
            if enviar:
                if habitacion and nombres:
                    cursor.execute("""
                        INSERT INTO huespedes (habitacion, hora, dia, mes, nombres, documento, procedencia, tarifa, estado_pago)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (habitacion, hora, dia, mes, nombres, documento, procedencia, tarifa, estado_pago))
                    conn.commit()
                    st.success(f"¡Huésped {nombres} registrado con éxito!")
                else:
                    st.warning("Por favor complete los campos obligatorios (Habitación y Nombres).")

    elif opcion == "Ver Historial y Reportes":
        st.title("📊 Base de Datos de Huéspedes")
        
        df = pd.read_sql_query("SELECT * FROM huespedes", conn)
        
        if not df.empty:
            buscar_hab = st.text_input("🔍 Filtrar por Habitación")
            if buscar_hab:
                df = df[df['habitacion'].str.contains(buscar_hab, case=False, na=False)]
                
            st.dataframe(df, use_container_width=True)
            
            total_ingresos = df[df['estado_pago'] == 'Pagado']['tarifa'].sum()
            por_cobrar = df[df['estado_pago'] == 'Pendiente']['tarifa'].sum()
            
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Total Recaudado (Pagado)", f"S/ {total_ingresos:,.2f}")
            col_m2.metric("Total por Cobrar (Pendiente)", f"S/ {por_cobrar:,.2f}")
        else:
            st.info("Aún no hay huéspedes registrados.")
