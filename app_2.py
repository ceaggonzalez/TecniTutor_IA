import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- 1. CONFIGURACIÓN DE SEGURIDAD (Se lee de los Secrets de Streamlit) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 2. FUNCIÓN DE LECTURA DE BIBLIOTECA (La "Base de Datos" de GitHub) ---
def cargar_biblioteca_pdf():
    texto_total = ""
    carpeta = "manuales" # Nombre de la carpeta en tu repositorio
    
    if os.path.exists(carpeta):
        archivos = [f for f in os.listdir(carpeta) if f.endswith(".pdf")]
        for archivo in archivos:
            ruta = os.path.join(carpeta, archivo)
            try:
                reader = PdfReader(ruta)
                for page in reader.pages:
                    texto_total += page.extract_text() + "\n"
            except Exception as e:
                st.error(f"Error leyendo {archivo}: {e}")
    return texto_total

# --- 3. INICIALIZACIÓN DE ESTADO (Solo ocurre una vez al cargar) ---
if 'contexto_maestro' not in st.session_state:
    st.session_state['contexto_maestro'] = cargar_biblioteca_pdf()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. DISEÑO DE LA INTERFAZ ---
st.title("🤖 TecniTutor IA")
st.caption("Asistente técnico basado en manuales oficiales del taller.")

# Barra lateral informativa
with st.sidebar:
    st.header("📚 Biblioteca")
    archivos = [f for f in os.listdir("manuales") if f.endswith(".pdf")] if os.path.exists("manuales") else []
    if archivos:
        for a in archivos:
            st.write(f"✅ {a}")
    else:
        st.warning("No hay PDFs en la carpeta /manuales")

# --- 5. LÓGICA DEL CHAT ---
# Definir instrucciones del sistema con el contexto persistente
instrucciones_base = f"""
Eres TecniTutor IA. Tu fuente de verdad es:
{st.session_state['contexto_maestro']}

REGLAS:
1. Seguridad LOTO/EPP primero.
2. No des respuestas directas, usa el andamiaje (preguntas guía).
3. Si el dato no está en el manual, aclara que es conocimiento general.
"""

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada del alumno
if prompt := st.chat_input("¿Qué duda técnica tienes?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            system_instruction=instrucciones_base
        )
        chat = model.start_chat(history=[
            {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]
        ])
        #response = chat.send_message(prompt)
        #st.markdown(response.text)
        #st.session_state.messages.append({"role": "assistant", "content": response.text})
        # Busca la línea 82 y cámbiala por esto:
        try:
            response = chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"⚠️ Error de conexión con Google: {e}")
            st.info("Prueba esperar un minuto o revisa que los PDFs no sean demasiado pesados.")
