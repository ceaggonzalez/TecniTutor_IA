import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os
import datetime

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
        
        instrucciones = f"""
            Eres "TecniTutor IA", un tutor especializado en Mantenimiento Industrial. 
            Tu objetivo es guiar a estudiantes de 15 a 18 años.

            1. Usa este manual adjunto para responder: {contexto}
            2. Usa analogías sencillas (Ej: Voltaje = Presión de agua).
            3. Antes de cualquier instrucción, PREGUNTA si aplicaron LOTO.
            4. Si ignoran la seguridad, DETÉN la explicación y enfatiza el riesgo.
            """
        
        model = genai.GenerativeModel(
            model_name="gemini-3-flash-preview",
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

#----Boton de Finalizado de sesion----
if st.sidebar.button("Terminar Consulta"):
    st.balloons()
    st.success("¡Práctica finalizada! No olvides descargar tu archivo de evidencia y completar el formato de validación.")

# Generar el texto del historial
chat_history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])

st.sidebar.download_button(
    label="📥 Descargar Evidencia (Trazabilidad)",
    data=chat_history_text,
    file_name=f"practica_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
    mime="text/plain"
)
