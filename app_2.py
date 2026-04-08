import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- CONFIGURACIÓN ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- FUNCIÓN PARA CARGAR UN MANUAL ESPECÍFICO ---
def leer_documento(nombre_archivo):
    texto = ""
    ruta = os.path.join("manuales", nombre_archivo)
    try:
        # Si es PDF
        if nombre_archivo.lower().endswith(".pdf"):
            reader = PdfReader(ruta)
            for page in reader.pages:
                texto += page.extract_text() + "\n"
        
        # Si es TXT (con manejo de errores de codificación)
        elif nombre_archivo.lower().endswith(".txt"):
            try:
                # Intento 1: Estándar moderno (UTF-8)
                with open(ruta, "r", encoding="utf-8") as f:
                    texto = f.read()
            except UnicodeDecodeError:
                # Intento 2: Estándar de Windows/Latinoamérica (Latin-1)
                with open(ruta, "r", encoding="latin-1") as f:
                    texto = f.read()
                    
    except Exception as e:
        st.error(f"Error al leer {nombre_archivo}: {e}")
    return texto

# --- INTERFAZ Y SELECCIÓN DE MANUAL ---
st.title("🤖 TecniTutor IA")
    # 1. Obtener lista de archivos en la carpeta
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Buscamos tanto .pdf como .txt
    archivos = [f for f in os.listdir("manuales") if f.endswith((".pdf", ".txt"))] if os.path.exists("manuales") else []
    
    if archivos:
        manual_sel = st.selectbox("Selecciona el manual técnico:", archivos)
        if st.button("Cargar Manual en Memoria"):
            st.session_state['contexto'] = leer_documento(manual_sel)
            st.success(f"✅ {manual_sel} cargado correctamente.")
    else:
        st.warning("⚠️ Sube archivos .pdf o .txt a la carpeta /manuales.")

# Inicializar historial si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- LÓGICA DEL CHAT CON HISTORIAL ACORTADO ---
if prompt := st.chat_input("¿Cuál es tu duda técnica?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        contexto = st.session_state.get('contexto_maestro', "No hay manual seleccionado.")
        
        instrucciones = f"Eres TecniTutor IA. Usa este manual: {contexto}. Reglas: Seguridad LOTO y usa andamiaje."
        
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=instrucciones
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
