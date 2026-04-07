import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader
import os

# --- 1. CONFIGURACIÓN DEL CLIENTE (Nueva Librería) ---
try:
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error("Configura tu API Key en los Secrets de Streamlit.")
    st.stop()

# --- 2. FUNCIONES TÉCNICAS ---
def leer_pdf(nombre_archivo):
    texto = ""
    ruta = os.path.join("manuales", nombre_archivo)
    try:
        reader = PdfReader(ruta)
        for page in reader.pages:
            texto += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Error al leer {nombre_archivo}: {e}")
    return texto

# --- 3. INTERFAZ Y BARRA LATERAL ---
st.set_page_config(page_title="TecniTutor IA", page_icon="🤖")
st.title("🤖 TecniTutor IA")

with st.sidebar:
    st.header("⚙️ Configuración")
    archivos = [f for f in os.listdir("manuales") if f.endswith(".pdf")] if os.path.exists("manuales") else []
    
    if archivos:
        manual_sel = st.selectbox("Selecciona el manual técnico:", archivos)
        if st.button("Cargar Manual en Memoria"):
            st.session_state['contexto'] = leer_pdf(manual_sel)
            st.success(f"✅ {manual_sel} cargado.")
    else:
        st.warning("⚠️ Sube PDFs a la carpeta /manuales en GitHub.")

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. LÓGICA DE RESPUESTA (ADN DE AI STUDIO) ---
if prompt := st.chat_input("¿Qué duda técnica tienes?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Recuperamos el manual (si existe)
        manual_data = st.session_state.get('contexto', "No hay manual cargado.")
        
        # Configuramos la instrucción del sistema exacta de tu Get Code
        config_ia = types.GenerateContentConfig(
            system_instruction=f"""
            Eres "TecniTutor IA", un tutor especializado en Mantenimiento Industrial. 
            Tu objetivo es guiar a estudiantes de 15 a 18 años.

            1. Usa este manual adjunto para responder: {manual_data}
            2. Usa analogías sencillas (Ej: Voltaje = Presión de agua).
            3. Antes de cualquier instrucción, PREGUNTA si aplicaron LOTO.
            4. Si ignoran la seguridad, DETÉN la explicación y enfatiza el riesgo.
            """,
            temperature=0.7,
            max_output_tokens=500
        )

        try:
            # Enviamos el historial acortado (últimos 6 mensajes) para ahorrar tokens
            historial_reciente = []
            for m in st.session_state.messages[-6:-1]:
                role_val = "model" if m["role"] == "assistant" else "user"
                historial_reciente.append(types.Content(role=role_val, parts=[types.Part.from_text(text=m["content"])]))

            response = client.models.generate_content(
                model="gemini-2.0-flash-lite", # El modelo rápido que elegiste
                contents=historial_reciente + [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                config=config_ia
            )
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Error de conexión: {e}")
