import streamlit as st
import google.generativeai as genai

# 1. Configuración de la API (Cámbialo por tu API Key de Google AI Studio)
genai.configure(api_key="TU_API_KEY_AQUÍ")

# 2. Configuración de la Interfaz
st.set_page_config(page_title="TecniTutor IA", page_icon="🛠️")
st.title("🛠️ TecniTutor IA: Asistente de Mantenimiento")
st.caption("Tu tutor experto en seguridad y cálculos industriales.")

# 3. Instrucciones del Sistema (Tu "Cerebro")
SYSTEM_PROMPT = """
Eres TecniTutor IA. Tu rol es ser un tutor de mantenimiento industrial.
REGLAS:
1. No des respuestas directas a cálculos.
2. Exige siempre el protocolo LOTO antes de cualquier paso técnico.
3. Usa un lenguaje claro y motivador.
"""

# 4. Inicializar el modelo y el historial
if "messages" not in st.session_state:
    st.session_state.messages = []

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash", # O la versión que estés usando
    system_instruction=SYSTEM_PROMPT
)

# 5. Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Lógica del Chat
if prompt := st.chat_input("¿En qué puedo ayudarte hoy en el taller?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Enviar historial completo para mantener el contexto
        chat = model.start_chat(history=[
            {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]
        ])
        response = chat.send_message(prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})