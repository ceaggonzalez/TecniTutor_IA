import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# --- CONFIGURACIÓN DE SEGURIDAD (SECRETS) ---
# Intentamos obtener la llave desde los secretos de Streamlit
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("⚠️ No se encontró la configuración 'GOOGLE_API_KEY'.")
    st.stop()

PASS_DOCENTE = st.secrets.get("PASS_DOCENTE", "Tecni2026") # También puedes proteger la contraseña

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="TecniTutor IA - Seguro", page_icon="🛡️")

# [El resto del código de la interfaz y la lógica de PDF se mantiene igual]
# Solo asegúrate de usar 'api_key' configurada arriba.

with st.sidebar:
    st.title("🔐 Panel de Control")
    # Insertar esto después de st.title()
with st.expander("👋 ¡Bienvenido a TecniTutor IA! (Lee esto primero)", expanded=True):
    st.markdown("""
    **¡Hola, futuro técnico!** 🛠️ 
    Soy tu asistente inteligente para las prácticas de mantenimiento. Mi objetivo no es darte la respuesta, sino ayudarte a que **tú mismo** domines la tecnología.

    **Reglas de nuestra sesión de hoy:**
    1. ⚠️ **Seguridad Primero:** Si vamos a trabajar con equipos reales, te preguntaré por tu equipo de protección y el bloqueo de energía (LOTO). Sin seguridad, no hay práctica.
    2. 🔍 **Piensa antes de actuar:** Si tienes un problema de cálculo o falla, te daré pistas y analogías. ¡Tú tienes el control!
    3. 📄 **Base Técnica:** Mis respuestas se basan en el manual oficial que tu docente ha cargado para esta sesión.

    *¿En qué componente o sistema estás trabajando ahora? Cuéntame los detalles.*
    """)
    modo = st.radio("Selecciona tu rol:", ["Estudiante", "Docente"])
    
    contexto_pdf = ""
    
    if modo == "Docente":
        password = st.text_input("Contraseña de acceso:", type="password")
        if password == PASS_DOCENTE:
            st.success("Acceso Docente Autorizado")
            uploaded_file = st.file_uploader("Subir manual técnico (PDF)", type="pdf")
            
            if uploaded_file:
                with st.spinner("Procesando conocimiento técnico..."):
                    reader = PdfReader(uploaded_file)
                    texto = ""
                    for page in reader.pages:
                        texto += page.extract_text() + "\n"
                    st.session_state['contexto_maestro'] = texto
                    st.info("📚 Manual cargado y listo.")
        elif password != "":
            st.error("Contraseña incorrecta")

# --- LÓGICA DE GEMINI ---
contexto_actual = st.session_state.get('contexto_maestro', "No hay manual cargado.")

instrucciones_base = f"""
Eres TecniTutor IA. Fuente de verdad: {contexto_actual}
Reglas: Seguridad LOTO/EPP primero, método socrático (andamiaje).
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=instrucciones_base
)

# ... [Misma lógica de chat que el paso anterior] ...
