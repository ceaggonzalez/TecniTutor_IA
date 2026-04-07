import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- CONFIGURACIÓN ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- FUNCIÓN PARA CARGAR UN MANUAL ESPECÍFICO ---
def leer_pdf_individual(nombre_archivo):
    texto = ""
    ruta = os.path.join("manuales", nombre_archivo)
    try:
        reader = PdfReader(ruta)
        for page in reader.pages:
            texto += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Error al leer {nombre_archivo}: {e}")
    return texto

# --- INTERFAZ Y SELECCIÓN DE MANUAL ---
st.title("🤖 TecniTutor IA")

with st.sidebar:
    st.header("📂 Configuración")
    
    # 1. Obtener lista de archivos en la carpeta
    archivos = [f for f in os.listdir("manuales") if f.endswith(".pdf")] if os.path.exists("manuales") else []
    
    if archivos:
        # 2. Selector de manual (Esto ahorra miles de tokens)
        manual_seleccionado = st.selectbox("Selecciona el manual de hoy:", archivos)
        
        # Cargamos el contenido solo del seleccionado
        if st.sidebar.button("Cargar Manual"):
            st.session_state['contexto_maestro'] = leer_pdf_individual(manual_seleccionado)
            st.success(f"Manual {manual_seleccionado} cargado.")
    else:
        st.warning("No hay manuales en la carpeta /manuales")

# Inicializar historial si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- LÓGICA DEL CHAT CON HISTORIAL ACORTADO ---
if prompt := st.chat_input("¿Cuál es tu duda técnica?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # En lugar de cargar el manual siempre, dale un resumen o pídele que sea breve
        resumen_manual = st.session_state.get('contexto_maestro', "")[:5000] # Solo los primeros 5000 caracteres

        instrucciones_base = f"""
        Eres TecniTutor IA. 
        REGLAS: 
        1. Responde de forma muy breve (máximo 3 oraciones).
        2. Usa este fragmento del manual: {resumen_manual}
        """
        model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=instrucciones_base
    )

        # --- RECORTE DE HISTORIAL (ESTRATEGIA LEAN) ---
        # Solo tomamos los últimos 6 mensajes para no saturar la memoria de tokens
        mensajes_recientes = st.session_state.messages[-6:]
        
        history_google = []
        for m in mensajes_recientes[:-1]: # Excluimos el último porque se envía en send_message
            role_google = "model" if m["role"] == "assistant" else "user"
            history_google.append({"role": role_google, "parts": [m["content"]]})
        
        try:
            chat = model.start_chat(history=history_google)
            response = chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {e}")
