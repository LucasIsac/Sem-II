# app.py - Archivo principal de la aplicación Streamlit
import streamlit as st
import os
from agent import process_command
from tools import convert_pdf_to_word, rename_file, rename_folder, convert_image_format, list_files, search_files
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener directorio de trabajo desde .env
WORKING_DIR = os.getenv('WORKING_DIRECTORY', 'files')

# Configuración de la página
st.set_page_config(
    page_title="FileMate AI - Asistente de Archivos",
    page_icon="🗂️",
    layout="centered"
)

# Asegurar que el directorio de trabajo existe
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

# Título y descripción
st.title("🗂️ FileMate AI")
st.markdown(f"""
Asistente inteligente para manipular archivos y carpetas mediante comandos de voz o texto.
Usa la IA de Gemma para entender tus intenciones y realizar acciones en tu sistema de archivos.

**Directorio de trabajo:** `{WORKING_DIR}`
""")

# Sidebar con información
with st.sidebar:
    st.header("ℹ️ Instrucciones")
    st.markdown("""
    1. **Sube archivos** si necesitas trabajar con ellos
    2. **Escribe o habla** lo que quieres hacer
    3. **Ejemplos de comandos**:
       - "Renombra el archivo.txt como documento.txt"
       - "Convierte el PDF a Word"
       - "Cambia el nombre de la carpeta 'proyectos' a 'mis_proyectos'"
       - "Convierte la imagen a PNG"
    """)
    
    st.header("📁 Archivos de Trabajo")
    st.write(f"Directorio: `{WORKING_DIR}`")
    
    # Mostrar archivos en el directorio de trabajo
    if st.button("Mostrar archivos"):
        files = list_files(WORKING_DIR)
        st.write("Archivos disponibles:")
        for file in files[:10]:  # Mostrar solo los primeros 10
            st.write(f"- {file}")
        if len(files) > 10:
            st.write(f"... y {len(files) - 10} más")

# Sección de carga de archivos
st.subheader("📤 Subir archivos")
uploaded_files = st.file_uploader(
    "Sube archivos para trabajar con ellos", 
    accept_multiple_files=True,
    help="Puedes subir múltiples archivos a la vez"
)

# Guardar archivos subidos
if uploaded_files:
    for uploaded_file in uploaded_files:
        with open(os.path.join(WORKING_DIR, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Archivo '{uploaded_file.name}' subido correctamente")

# Sección de entrada de comandos
st.subheader("🎯 ¿Qué quieres hacer?")
user_command = st.text_input(
    "Escribe tu comando:",
    placeholder="Ej: Renombra el archivo.txt como documento.txt"
)

# Procesar comando cuando se ingresa
if user_command:
    st.info(f"Procesando: '{user_command}'")
    
    try:
        with st.spinner("Analizando tu solicitud con IA..."):
            result = process_command(user_command)
        
        if result["success"]:
            st.success("✅ ¡Comando ejecutado correctamente!")
            st.write("**Resultado:**", result["message"])
            
            # Mostrar cambios si es relevante
            if "new_file" in result:
                st.download_button(
                    label="Descargar archivo resultante",
                    data=open(result["new_file"], "rb").read(),
                    file_name=os.path.basename(result["new_file"])
                )
        else:
            st.error("❌ No pude procesar tu solicitud")
            st.write("**Error:**", result["message"])
            st.write("**Sugerencia:** Intenta ser más específico con tu petición")
            
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        st.write("Por favor, intenta con otro comando o verifica los archivos necesarios")

# Mostrar archivos actualizados
if st.button("Actualizar lista de archivos"):
    files = list_files(WORKING_DIR)
    st.write(f"**Archivos en `{WORKING_DIR}`:**")
    for file in files:
        st.write(f"- {file}")

# Pie de página
st.markdown("---")
st.markdown("### 💡 Consejos")
st.markdown("""
- Asegúrate de que los archivos mencionados existan en el directorio
- Para conversiones, sube primero el archivo original
- Sé específico con los nombres de archivos y extensiones
""")
