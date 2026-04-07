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
# --- LÓGICA DEL CHAT CORREGIDA ---

if prompt := st.chat_input("¿Qué duda técnica tienes?"):
    # 1. Mostrar y guardar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta de la IA
    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash", 
                system_instruction=instrucciones_base
            )
            
            # --- CORRECCIÓN DE ROLES AQUÍ ---
            # Google solo acepta 'user' y 'model'. 
            # Traducimos 'assistant' a 'model' para el historial.
            history_google = []
            for m in st.session_state.messages[:-1]:
                role_google = "model" if m["role"] == "assistant" else "user"
                history_google.append({"role": role_google, "parts": [m["content"]]})
            
            chat = model.start_chat(history=history_google)
            
            response = chat.send_message(prompt)
            st.markdown(response.text)
            
            # Guardamos como 'assistant' para que Streamlit muestre el icono correcto
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"⚠️ Error de conexión: {e}")
