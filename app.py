# app.py - FileMate AI (versión final y funcional)
import streamlit as st
import os
import speech_recognition as sr
from agent import process_command
from tools import convert_pdf_to_word_cloudconvert, rename_file, rename_folder, convert_image_format, list_files, search_files
from dotenv import load_dotenv

from voice_handler import speak_response

# ----------------- CARGA DE VARIABLES -----------------
load_dotenv()
WORKING_DIR = os.getenv('WORKING_DIRECTORY', 'files')
os.makedirs(WORKING_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True) # Asegurarse de que la carpeta 'static' existe

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

# ----------------- CONFIGURACIÓN DEL SIDEBAR -----------------
with st.sidebar:
    st.header("⚙️ Opciones del Asistente")

    with st.container():
        st.subheader("🔊 Configuración de Voz")
        modo_voz = st.radio(
            "Modo de respuesta:",
            ["Solo texto", "Voz y texto"],
            index=0,
            help="El asistente hablará con naturalidad incorporada."
        )

    st.markdown("---")

    with st.container():
        st.subheader("ℹ️ Instrucciones")
        st.markdown("""
        **Habla con el asistente como si fuera una persona.**
        Ejemplos:
        - "Hola, ¿podés ayudarme a encontrar todos los archivos PDF?"
        - "Necesito renombrar el archivo 'boleta.pdf' a 'factura.pdf'"
        - "Convertí la imagen 'foto.jpg' a PNG"
        """)

    st.markdown("---")

    with st.container():
        st.subheader("📁 Archivos de Trabajo")
        if st.button("Mostrar archivos en el sistema"):
            files = list_files(WORKING_DIR)
            if files:
                st.write("**Archivos disponibles:**")
                for file in files:
                    st.write(f"- `{file}`")
            else:
                st.info("No hay archivos en el directorio.")

    st.markdown("---")

    with st.container():
        st.subheader("🧹 Control de Sesión")
        if st.button("Limpiar chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()

# ----------------- ESTADOS -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
# Se remueve la línea de transcriber porque se hará directo
# if "transcriber" not in st.session_state:
#    st.session_state.transcriber = Transcriber()

# ----------------- PANTALLA INICIAL -----------------
if not st.session_state.messages:
    st.markdown("""
        ¡Hola! Soy FileMate, tu asistente de archivos personal. Estoy aquí para ayudarte a gestionar, buscar y organizar tus archivos de forma fácil y conversacional.
    """)
    st.info("Para empezar, intenta preguntarme algo como:")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.info("`¿Qué archivos hay en la carpeta?`")
    with col2:
        st.info("`Crea una nueva carpeta llamada 'vacaciones'`")

# ----------------- HISTORIAL DEL CHAT -----------------
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio_path" in message:
            with st.expander("▶️ Escuchar audio"):
                st.audio(message["audio_path"], format="audio/mp3", autoplay=True)

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
                    result = speak_response(response["message"])
                    audio_path = result["file_path"]
                    st.session_state.messages.append({"role": "assistant", "content": response["message"], "audio_path": audio_path, "avatar": "🗂️"})
                except Exception as e:
                    st.warning(f"Error al generar audio: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": response["message"], "avatar": "🗂️"})
            else:
                st.session_state.messages.append({"role": "assistant", "content": response["message"], "avatar": "🗂️"})
        else:
            st.error(response["message"])
            st.session_state.messages.append({"role": "assistant", "content": response["message"], "avatar": "🗂️"})
    st.rerun()

# ----------------- INPUT DEL USUARIO -----------------
st.markdown("---")
# Botón para grabar audio
if st.button("🎤 Grabar por voz"):
    r = sr.Recognizer()
    try:
        with st.spinner("🤖 ¡Escuchando! Por favor, habla ahora..."):
            with sr.Microphone() as source:
                audio = r.listen(source, phrase_time_limit=10)
        
        st.success("✅ Grabación finalizada. Transcribiendo...")
        
        with st.spinner("✨ Transcribiendo tu mensaje..."):
            text = r.recognize_google(audio, language="es-ES")
            st.text_input("Mensaje transcrito:", value=text)
            
            # Pasa el texto a la IA
            process_prompt(text, modo_voz)

    except sr.WaitTimeoutError:
        st.error("Se agotó el tiempo de espera. No se detectó ninguna voz.")
    except sr.UnknownValueError:
        st.error("No pude entender el audio. Por favor, habla más claro.")
    except sr.RequestError as e:
        st.error(f"Error de servicio de reconocimiento de voz: {e}")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")

if prompt := st.chat_input("Escribe tu consulta..."):
    process_prompt(prompt, modo_voz)
