import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- CONFIGURACIÓN DE API ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- FUNCIÓN PARA LEER LA "BASE DE DATOS" DE GITHUB ---
def cargar_biblioteca_pdf():
    texto_acumulado = ""
    carpeta = "manuales"
    
    # Verificamos si la carpeta existe
    if os.path.exists(carpeta):
        archivos = [f for f in os.listdir(carpeta) if f.endswith(".pdf")]
        if archivos:
            for archivo in archivos:
                ruta_completa = os.path.join(carpeta, archivo)
                reader = PdfReader(ruta_completa)
                for page in reader.pages:
                    texto_acumulado += page.extract_text() + "\n"
            return texto_acumulado
    return "No hay manuales cargados en la biblioteca de GitHub."

# --- INTERFAZ ---
st.set_page_config(page_title="TecniTutor IA - Biblioteca", page_icon="📚")

# Inicializar el contexto si no existe en la sesión
if 'contexto_persitente' not in st.session_state:
    with st.spinner("Cargando manuales técnicos..."):
        st.session_state['contexto_persitente'] = cargar_biblioteca_pdf()

# --- PANEL LATERAL ---
with st.sidebar:
    st.title("📂 Biblioteca")
    st.info(f"Manuales detectados en el sistema.")
    # Listar los archivos para que el alumno sepa qué hay
    archivos_lista = [f for f in os.listdir("manuales") if f.endswith(".pdf")] if os.path.exists("manuales") else []
    for a in archivos_lista:
        st.write(f"📄 {a}")

# --- INSTRUCCIONES DEL SISTEMA ---
instrucciones_ia = f"""
Eres TecniTutor IA. 
TU BASE DE CONOCIMIENTO FIJA ES:
{st.session_state['contexto_persitente']}

REGLAS:
1. Responde basándote en los manuales anteriores.
2. Si la duda no está ahí, menciona: 'Basado en mi conocimiento general...' pero prioriza el manual.
3. Mantén el andamiaje y la seguridad LOTO.
"""

# [Aquí sigue tu lógica de chat estándar...]
