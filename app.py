# app.py - FileMate AI (versión con memoria de carpeta sincronizada)
import streamlit as st
import os
import speech_recognition as sr
from agent import process_command, current_working_directory, set_current_directory
from tools import get_file_structure, list_files, convert_pdf_to_word_cloudconvert, rename_file, rename_folder, convert_image_format, search_files
from dotenv import load_dotenv
from voice_handler import speak_response

# ----------------- CARGA DE VARIABLES -----------------
load_dotenv()
WORKING_DIR = os.getenv('WORKING_DIRECTORY', 'files')  # Carpeta por defecto
os.makedirs(WORKING_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)  # Carpeta para audios TTS

# ----------------- MEMORIA DE CARPETA ACTUAL (SINCRONIZADA) -----------------
if "current_folder" not in st.session_state:
    st.session_state.current_folder = WORKING_DIR

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

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.header("⚙️ Opciones del Asistente")
    st.subheader("🔊 Configuración de Voz")
    modo_voz = st.radio(
        "Modo de respuesta:",
        ["Solo texto", "Voz y texto"],
        index=0,
        help="El asistente hablará con naturalidad incorporada."
    )

    st.markdown("---")
    
    # Mostrar directorio actual
    st.subheader("📍 Directorio Actual")
    current_dir = current_working_directory
    st.code(current_dir, language="text")
    
    # Botones para cambio rápido de directorio
    st.subheader("🚀 Cambio Rápido")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Documentos"):
            docs_path = os.path.expanduser("~/Documents")
            if os.path.exists(docs_path):
                set_current_directory(docs_path)
                st.rerun()
    
        if st.button("🖼️ Imágenes"):
            pics_path = os.path.expanduser("~/Pictures")
            if os.path.exists(pics_path):
                set_current_directory(pics_path)
                st.rerun()
    
    with col2:
        if st.button("⬇️ Descargas"):
            dl_path = os.path.expanduser("~/Downloads")
            if os.path.exists(dl_path):
                set_current_directory(dl_path)
                st.rerun()
    
        if st.button("🏠 Proyecto"):
            set_current_directory(WORKING_DIR)
            st.rerun()

    st.markdown("---")
    st.subheader("ℹ️ Instrucciones")
    st.markdown("""
    **Habla con el asistente como si fuera una persona.**
    
    🔄 **Memoria de contexto**: El asistente ahora recuerda en qué carpeta estás trabajando.
    
    Ejemplos:
    - "Enlistame los archivos de Documentos"
    - "Ahora crea la carpeta 'Proyecto2024'" ← se creará en Documentos
    - "Renombra el archivo 'old.txt' a 'nuevo.txt'"
    """)

    st.markdown("---")
    st.subheader("📁 Vista Rápida")

    if st.button("🔄 Refrescar vista de archivos"):
        if 'file_structure' in st.session_state:
            del st.session_state['file_structure']
        st.rerun()

    def display_files_sidebar(directory, max_items=5):
        """Muestra una vista simplificada para el sidebar"""
        if not os.path.exists(directory):
            st.warning(f"La carpeta no existe.")
            return
        
        try:
            items = os.listdir(directory)[:max_items]
            for item in items:
                path = os.path.join(directory, item)
                if os.path.isdir(path):
                    st.text(f"📁 {item}")
                else:
                    st.text(f"📄 {item}")
            
            if len(os.listdir(directory)) > max_items:
                st.text(f"... y {len(os.listdir(directory)) - max_items} más")
        except Exception:
            st.text("Error al leer carpeta")

    if st.button("👀 Ver archivos actuales"):
        with st.expander("Archivos en directorio actual"):
            display_files_sidebar(current_working_directory)

    st.markdown("---")
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
if 'file_structure' not in st.session_state:
    st.session_state.file_structure = None

# ----------------- PANTALLA INICIAL -----------------
if not st.session_state.messages:
    st.markdown("¡Hola! Soy FileMate, tu asistente de archivos personal con **memoria de contexto**. Ahora recuerdo en qué carpeta estamos trabajando entre comandos.")
    st.info("Para empezar, intenta preguntarme algo como:")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.info("`Enlistame los archivos de Documentos`")
    with col2:
        st.info("`Ahora crea la carpeta 'MiProyecto'`")
    
    st.success("🔄 **Nuevo**: Tengo memoria de carpeta. Si listas archivos de Documentos y luego pides crear una carpeta, la crearé en Documentos, no en la carpeta por defecto.")

# ----------------- HISTORIAL DEL CHAT -----------------
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio_path" in message:
            with st.expander("▶️ Escuchar audio"):
                st.audio(message["audio_path"], format="audio/mp3", autoplay=True)

# ----------------- FUNCIÓN PARA OBTENER ESTRUCTURA DE ARCHIVOS (CON CACHÉ) -----------------
def get_cached_file_structure():
    if st.session_state.file_structure is None:
        with st.spinner("Actualizando vista de archivos..."):
            st.session_state.file_structure = get_file_structure(WORKING_DIR)
    return st.session_state.file_structure

# ----------------- FUNCIÓN PARA PROCESAR EL PROMPT -----------------
def process_prompt(prompt, modo_voz):
    """Procesa el prompt del usuario con memoria de carpeta sincronizada"""
    global current_working_directory
    
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "😃"})
    with st.chat_message("user", avatar="😃"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🗂️"):
        with st.spinner("🚀 Procesando tu solicitud..."):
            # Obtener la estructura de archivos (usando el caché)
            file_structure = get_cached_file_structure()
            
            # CORRECCIÓN: Usar solo los argumentos que acepta process_command
            # Opción 1: Si process_command acepta 3 argumentos
            try:
                response = process_command(prompt, st.session_state.chat_history, file_structure)
            except TypeError:
                # Opción 2: Si process_command acepta solo 2 argumentos
                try:
                    response = process_command(prompt, st.session_state.chat_history)
                except TypeError:
                    # Opción 3: Si process_command acepta solo 1 argumento
                    response = process_command(prompt)

        if response.get("files_changed", False):
            st.session_state.file_structure = None # Invalidar caché

        # Sincronizar directorio de trabajo si cambió
        if "current_directory" in response:
            st.session_state.current_folder = response["current_directory"]

        # Invalidar caché si hubo cambios
        if response.get("files_changed", False):
            st.session_state.file_structure = None

        if response["success"]:
            st.markdown(response["message"])
            
            # Agregar a historial de chat para memoria
            st.session_state.chat_history.append({
                "type": "human",
                "content": prompt
            })
            st.session_state.chat_history.append({
                "type": "assistant", 
                "content": response["message"]
            })
            
            if modo_voz == "Voz y texto":
                try:
                    result = speak_response(response["message"])
                    audio_path = result["file_path"]
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response["message"], 
                        "audio_path": audio_path, 
                        "avatar": "🗂️"
                    })
                except Exception as e:
                    st.warning(f"Error al generar audio: {e}")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response["message"], 
                        "avatar": "🗂️"
                    })
            else:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response["message"], 
                    "avatar": "🗂️"
                })
        else:
            st.error(response["message"])
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response["message"], 
                "avatar": "🗂️"
            })
    
    st.rerun()

# ----------------- INPUT DEL USUARIO -----------------
st.markdown("---")

# Mostrar directorio actual en el input
current_display = current_working_directory.replace(os.path.expanduser("~"), "~")
st.caption(f"📍 Trabajando en: `{current_display}`")

# Botón para grabar audio
if st.button("🎤 Grabar por voz"):
    r = sr.Recognizer()
    try:
        with st.spinner("🤖 ¡Escuchando! Por favor, habla ahora..."):
            with sr.Microphone() as source:
                # Ajustar para ruido ambiental
                r.adjust_for_ambient_noise(source, duration=1)
                # Escuchar con timeout más largo
                audio = r.listen(source, phrase_time_limit=15, timeout=5)
        
        st.success("✅ Grabación finalizada. Transcribiendo...")
        
        with st.spinner("✨ Transcribiendo tu mensaje..."):
            # Intentar con español primero, luego inglés como fallback
            try:
                text = r.recognize_google(audio, language="es-ES")
            except:
                try:
                    text = r.recognize_google(audio, language="en-US")
                except:
                    text = r.recognize_google(audio)
            
            st.success(f"📝 Transcripción: {text}")
            # Procesar automáticamente la transcripción
            process_prompt(text, modo_voz)
            
    except sr.WaitTimeoutError:
        st.error("⏱️ Se agotó el tiempo de espera. No se detectó ninguna voz.")
    except sr.UnknownValueError:
        st.error("🔇 No pude entender el audio. Por favor, habla más claro y cerca del micrófono.")
    except sr.RequestError as e:
        st.error(f"🌐 Error de servicio de reconocimiento de voz: {e}")
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error inesperado: {e}")

if prompt := st.chat_input("Escribe tu consulta..."):
    process_prompt(prompt, modo_voz)