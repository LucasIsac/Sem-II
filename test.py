# app.py - FileMate AI completo
import streamlit as st
import os
from agent import process_command
from tools import list_files
from dotenv import load_dotenv
from tts import TTS 

# 🔥 IMPORTA la función speak_response desde voice_handler.py
from voice_handler import speak_response

# ----------------- CARGA DE VARIABLES -----------------
load_dotenv()
WORKING_DIR = os.getenv('WORKING_DIRECTORY', 'files')
os.makedirs(WORKING_DIR, exist_ok=True)

# ----------------- ACTIVACIÓN OBLIGATORIA DE VOZ -----------------
if 'voice_activated' not in st.session_state:
    st.session_state.voice_activated = False

if not st.session_state.voice_activated:
    st.set_page_config(page_title="FileMate AI - Activación", page_icon="🗂️", layout="centered")
    st.title("🔊 Activar Voz - FileMate AI")
    st.warning("Para usar el asistente con voz, debes activarla primero:")
    
    if st.button("🎤 ACTIVAR VOZ AUTOMÁTICA", use_container_width=True, type="primary"):
        st.session_state.voice_activated = True
        st.rerun()
    
    st.info("Esto es necesario por las políticas de seguridad de los navegadores.")
    st.stop()

# ----------------- CONFIGURACIÓN DE PÁGINA -----------------
st.set_page_config(page_title="FileMate AI - Chat", page_icon="🗂️", layout="centered")
st.title("🗂️ FileMate AI - Asistente de Archivos")

# ----------------- CONFIGURACIÓN DE VOZ (SIDEBAR) -----------------
st.sidebar.header("🔊 Configuración de Voz")
modo_voz = st.sidebar.radio(
    "Modo de respuesta:",
    ["Solo texto", "Voz y texto"],
    index=1,
    help="El asistente hablará con naturalidad incorporada"
)

volumen = st.sidebar.slider("Volumen", 0.5, 1.0, 0.8, 0.1)

# ----------------- ESTADOS -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ----------------- SIDEBAR EXTRA -----------------
with st.sidebar:
    st.header("ℹ️ Instrucciones")
    st.markdown("""
    **Hablá con el asistente como si fuera una persona.**
    Ejemplos:
    - "Hola, ¿podés ayudarme a encontrar todos los archivos PDF?"
    - "Necesito renombrar el archivo 'boleta.pdf' a 'factura.pdf'"
    - "Convertí la imagen 'foto.jpg' a PNG"
    """)
    st.markdown("---")
    st.header("📁 Archivos de Trabajo")
    if st.button("Mostrar archivos en el sistema"):
        files = list_files(WORKING_DIR)
        if files:
            st.write("**Archivos disponibles:**")
            for file in files:
                st.write(f"- `{file}`")
        else:
            st.info("No hay archivos en el directorio.")

# ----------------- FUNCIÓN PARA PROCESAR EL PROMPT -----------------

def process_prompt(prompt, modo_voz):
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "😃"})
    
    with st.chat_message("user", avatar="😃"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🗂️"):
        with st.spinner("🚀 Procesando tu solicitud..."):
            response = process_command(prompt, st.session_state.chat_history, modo_voz)

        if response["success"]:
            st.markdown(response["message"])
            if modo_voz == "Voz y texto":
                try:
                    # El resultado de speak_response ya es la ruta completa
                    audio_path = speak_response(response["message"])
                    
                    # Verificamos que se generó un archivo
                    if audio_path:
                        # Guardamos el mensaje en el historial con la ruta del archivo
                        st.session_state.messages.append({"role": "assistant", "content": response["message"], "audio_path": audio_path, "avatar": "🗂️"})
                    else:
                        # Manejamos el caso donde no se generó audio
                        st.warning("No se pudo generar el audio de respuesta.")
                        st.session_state.messages.append({"role": "assistant", "content": response["message"], "avatar": "🗂️"})
                        
                except Exception as e:
                    st.warning(f"Error al generar audio: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": response["message"], "avatar": "🗂️"})
            else:
                st.session_state.messages.append({"role": "assistant", "content": response["message"], "avatar": "🗂️"})
        else:
            st.error(response["message"])
            st.session_state.messages.append({"role": "assistant", "content": response["message"], "avatar": "🗂️"})
    st.rerun()

# ----------------- HISTORIAL DEL CHAT (MODIFICADO) -----------------
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio_path" in message:
            # Aquí está el cambio crucial: pasamos la ruta completa a st.audio
            st.audio(message["audio_path"], format="audio/mp3", autoplay=True)

# ----------------- INPUT DEL USUARIO -----------------
if prompt := st.chat_input("Decime qué necesitas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = process_command(prompt, st.session_state.chat_history, modo_voz)

        if response["success"]:
            st.markdown(response["message"])
            st.session_state.messages.append({"role": "assistant", "content": response["message"]})
            
            if modo_voz == "Voz y texto":
                try:
                    result = speak_response(response["message"])
                    audio_path = result["file_path"]
                    
                    st.audio(audio_path, format="audio/mp3", autoplay=True)
                    
                    st.session_state.last_audio = audio_path
                
                except Exception as e:
                    st.warning(f"Error al generar audio: {e}")
        else:
            st.error(response["message"])
            st.session_state.messages.append({"role": "assistant", "content": response["message"]})

# ----------------- BOTONES ADICIONALES -----------------
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🗣️ Háblame"):
        tts = TTS()
        audio_file = tts.process("¡Hola! Soy File Mate AI, tu asistente de sistema. ¿En qué puedo ayudarte hoy?")
        audio_html = f"""
        <audio autoplay controls style="width: 100%; margin: 10px 0;">
            <source src="static/{audio_file}" type="audio/mp3">
        </audio>
        """
        st.components.v1.html(audio_html, height=80)
        st.success("Te acabo de saludar por voz. ¿Me escuchaste?")

with col2:
    if st.button("🕐 ¿Qué hora es?"):
        st.session_state.messages.append({"role": "user", "content": "¿Qué hora es?"})

with col3:
    if st.button("🔊 Probar voz"):
        tts = TTS()
        audio_file = tts.process("¡Hola! Esta es una prueba de la función de voz de File Mate AI.")
        audio_html = f"""
        <audio autoplay controls style="width: 100%; margin: 10px 0;">
            <source src="static/{audio_file}" type="audio/mp3">
        </audio>
        """
        st.components.v1.html(audio_html, height=80)
        st.success("Prueba de voz ejecutada. ¿Se escuchó correctamente?")