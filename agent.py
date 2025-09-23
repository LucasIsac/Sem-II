# agent.py - Agente extendido con memoria de contexto de carpeta
import os
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from tts import TTS

# Importar las herramientas modificadas
from tools import (
    rename_file, rename_folder, convert_image_format, search_files,
    convert_pdf_to_word_cloudconvert, convert_pdf_to_word_local, 
    create_folder, delete_file, delete_folder, move_file, move_folder, 
    create_backup, convert_word_to_pdf, system_manager, list_files
)

# Importar dashboard del sistema
from system_dashboard import get_system_dashboard_response

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "tu_api_key_de_google_gemini_aqui":
    raise ValueError("Por favor configura tu API key de Gemini en el archivo .env")

# Variable global para mantener el contexto de carpeta actual
current_working_directory = os.path.join(os.getcwd(), "files")  # Carpeta por defecto

def get_current_directory():
    """Obtiene el directorio de trabajo actual"""
    global current_working_directory
    return current_working_directory

def set_current_directory(new_directory):
    """Establece un nuevo directorio de trabajo"""
    global current_working_directory
    current_working_directory = new_directory
    return f"Directorio de trabajo cambiado a: {new_directory}"

def list_files_with_context(directory_param=None):
    """Lista archivos manteniendo el contexto de directorio actual"""
    global current_working_directory
    
    if directory_param:
        # Si se especifica un directorio, actualizamos el contexto
        if directory_param.lower() in ["documentos", "documents"]:
            new_dir = os.path.expanduser("~/Documents")
        elif directory_param.lower() in ["descargas", "downloads"]:
            new_dir = os.path.expanduser("~/Downloads")
        elif directory_param.lower() in ["escritorio", "desktop"]:
            new_dir = os.path.expanduser("~/Desktop")
        elif directory_param.lower() in ["imagenes", "pictures"]:
            new_dir = os.path.expanduser("~/Pictures")
        else:
            new_dir = directory_param
            
        if os.path.exists(new_dir):
            current_working_directory = new_dir
        
        return list_files(new_dir)
    else:
        return list_files(current_working_directory)

def create_folder_with_context(folder_name):
    """Crea una carpeta en el directorio actual"""
    global current_working_directory
    return create_folder(folder_name, current_working_directory)

def delete_file_with_context(file_name):
    """Elimina un archivo del directorio actual"""
    global current_working_directory
    return delete_file(file_name, current_working_directory)

def delete_folder_with_context(folder_name):
    """Elimina una carpeta del directorio actual"""
    global current_working_directory
    return delete_folder(folder_name, current_working_directory)

def rename_file_with_context(params):
    """Renombra un archivo en el directorio actual"""
    global current_working_directory
    parts = params.split("|")
    if len(parts) == 2:
        return rename_file(parts[0], parts[1], current_working_directory)
    return {"success": False, "message": "Formato incorrecto. Usar: nombre_actual|nombre_nuevo"}

def rename_folder_with_context(params):
    """Renombra una carpeta en el directorio actual"""
    global current_working_directory
    parts = params.split("|")
    if len(parts) == 2:
        return rename_folder(parts[0], parts[1], current_working_directory)
    return {"success": False, "message": "Formato incorrecto. Usar: nombre_actual|nombre_nuevo"}

def move_file_with_context(params):
    """Mueve un archivo manteniendo contexto"""
    global current_working_directory
    parts = params.split("|")
    if len(parts) == 2:
        return move_file(parts[0], parts[1], current_working_directory)
    return {"success": False, "message": "Formato incorrecto. Usar: archivo|destino"}

def move_folder_with_context(params):
    """Mueve una carpeta manteniendo contexto"""
    global current_working_directory
    parts = params.split("|")
    if len(parts) == 2:
        return move_folder(parts[0], parts[1], current_working_directory)
    return {"success": False, "message": "Formato incorrecto. Usar: carpeta|destino"}

# Definir las herramientas disponibles con contexto
tools = [
    # Herramientas de archivos y carpetas CON CONTEXTO
    Tool(
        name="get_current_directory",
        func=get_current_directory,
        description="Muestra el directorio de trabajo actual. Sin parámetros."
    ),
    Tool(
        name="set_current_directory", 
        func=set_current_directory,
        description="Cambia el directorio de trabajo actual. Parámetro: nueva_ruta"
    ),
    Tool(
        name="list_files",
        func=list_files_with_context,
        description="Lista archivos y carpetas. Si se especifica una carpeta (documentos, descargas, etc.), cambia el contexto a esa carpeta."
    ),
    Tool(
        name="create_folder",
        func=create_folder_with_context,
        description="Crea una nueva carpeta en el directorio actual. Parámetro: nombre de la carpeta."
    ),
    Tool(
        name="delete_file",
        func=delete_file_with_context,
        description="Elimina un archivo del directorio actual. Parámetro: nombre del archivo."
    ),
    Tool(
        name="delete_folder",
        func=delete_folder_with_context,
        description="Elimina una carpeta del directorio actual. Parámetro: nombre de la carpeta."
    ),
    Tool(
        name="rename_file",
        func=rename_file_with_context,
        description="Renombra un archivo en el directorio actual. Formato: nombre_actual|nombre_nuevo"
    ),
    Tool(
        name="rename_folder",
        func=rename_folder_with_context,
        description="Renombra una carpeta en el directorio actual. Formato: nombre_actual|nombre_nuevo"
    ),
    Tool(
        name="move_file",
        func=move_file_with_context,
        description="Mueve un archivo desde el directorio actual. Formato: archivo|carpeta_destino"
    ),
    Tool(
        name="move_folder",
        func=move_folder_with_context,
        description="Mueve una carpeta desde el directorio actual. Formato: carpeta|carpeta_destino"
    ),
    
    # Herramientas que no requieren contexto específico
    Tool(
        name="convert_image_format",
        func=lambda x: convert_image_format(*x.split("|")),
        description="Convierte una imagen a otro formato. Formato: ruta_imagen|nuevo_formato"
    ),
    Tool(
        name="search_files",
        func=search_files,
        description="Busca archivos en la carpeta actual. Parámetro: patrón de búsqueda"
    ),
    Tool(
        name="convert_pdf_to_word_cloudconvert",
        func=lambda x: convert_pdf_to_word_cloudconvert(x),
        description="Convierte un PDF a Word usando CloudConvert. Parámetro: ruta del PDF."
    ),
    Tool(
        name="convert_pdf_to_word_local",
        func=lambda x: convert_pdf_to_word_local(x),
        description="Convierte un PDF a Word localmente. Parámetro: ruta del PDF."
    ),
    Tool(
        name="create_backup",
        func=create_backup,
        description="Crea un backup de un archivo o carpeta. Parámetro: ruta del archivo o carpeta."
    ),
    Tool(
        name="convert_word_to_pdf",
        func=convert_word_to_pdf,
        description="Convierte un archivo de Word (.docx) a PDF. Parámetro: ruta del archivo Word."
    ),
    Tool(
        name="get_system_resources",
        func=lambda x: system_manager.get_system_resources(),
        description="Obtiene información básica sobre el uso de CPU, memoria y disco del sistema. No requiere parámetros."
    ),
    Tool(
        name="show_system_dashboard", 
        func=lambda x: get_system_dashboard_response(),
        description="Muestra un dashboard completo con gráficos y recomendaciones del sistema. Usar cuando el usuario pida ver el estado detallado de recursos, rendimiento o dashboard del sistema."
    ),
    Tool(
        name="open_program",
        func=system_manager.open_program,
        description="Abre un programa en el sistema operativo. Parámetro: nombre_del_programa."
    ),
    Tool(
        name="search_files_smart",
        func=lambda x: system_manager.search_files_smart(*x.split("|") if "|" in x else (x, None)),
        description="Busca archivos en todo el sistema. Formato: patrón|ruta_opcional."
    ),
    Tool(
        name="get_running_processes",
        func=system_manager.get_running_processes,
        description="Muestra la lista de procesos en ejecución ordenados por uso de memoria. Sin parámetros."
    )
]

def initialize_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=512
    )

def process_command(command: str, chat_history: list = None, modo_voz: str = "Voz y texto"):
    """
    Procesa un comando de lenguaje natural con FileMate AI manteniendo contexto de carpeta
    """
    global current_working_directory
    
    try:
        llm = initialize_llm()

        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        if chat_history:
            for message in chat_history:
                if message['type'] == 'human':
                    memory.chat_memory.add_user_message(message['content'])
                else:
                    memory.chat_memory.add_ai_message(message['content'])

        # Prompt actualizado con información de contexto
        system_prompt = f"""Eres FileMate AI, un asistente de gestión de archivos y sistema. Tu función es interpretar las instrucciones del usuario y ejecutar las herramientas correspondientes.

**CONTEXTO ACTUAL:**
- Directorio de trabajo actual: {current_working_directory}
- IMPORTANTE: Mantén siempre el contexto del directorio actual entre comandos

**GESTIÓN DE DIRECTORIO DE TRABAJO:**
- Cuando el usuario mencione "documentos", "descargas", "escritorio", etc., usa `list_files` con ese parámetro para cambiar el contexto
- Una vez que cambies a un directorio, TODAS las operaciones posteriores (crear, eliminar, renombrar) se realizan en ese directorio
- Usa `get_current_directory` para verificar dónde estás trabajando
- Si necesitas cambiar explícitamente de directorio, usa `set_current_directory`

**PARA MANEJAR ARCHIVOS (RENOMBRAR, MOVER, BORRAR, ETC.):**
- SIEMPRE trabaja en el directorio actual a menos que el usuario especifique otro
- Si el usuario no proporciona una ruta completa, asume que se refiere a archivos en el directorio actual
- Para búsquedas globales usa `search_files_smart`, para búsquedas locales usa `search_files`
- Cuando crees carpetas o archivos, hazlo en el directorio actual

**MEMORIA DE CONTEXTO:**
- Recuerda siempre en qué directorio estás trabajando
- Si el usuario dice "ahora crea la carpeta X", créala en el directorio donde estuviste trabajando anteriormente
- No vuelvas al directorio por defecto a menos que el usuario lo pida explícitamente

**MONITOREO DEL SISTEMA:**
- Cuando el usuario pida información sobre recursos, rendimiento, estado del sistema, o un "dashboard", usa `show_system_dashboard`
- Para consultas simples sobre recursos usa `get_system_resources`
- Ejemplos de cuándo usar dashboard: "cómo están los recursos", "muestra el dashboard", "estado del sistema", "rendimiento de la PC"

**NUEVAS CAPACIDADES DEL SISTEMA:**
- Dashboard visual de recursos → Usa show_system_dashboard  
- Monitoreo básico de recursos → Usa get_system_resources
- Apertura de programas y aplicaciones → Usa open_program
- Búsqueda en todo el sistema de archivos → Usa search_files_smart
- Gestión de procesos en ejecución → Usa get_running_processes

Responde en español de manera natural y amable. Tu nombre es FileMate AI.
Siempre menciona en qué directorio estás trabajando cuando sea relevante."""

        agent_executor = initialize_agent(
            tools,
            llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            handle_parsing_errors=True,
            agent_kwargs={"system_message": system_prompt}
        )

        result = agent_executor.invoke({"input": command})
        respuesta = str(result["output"])
        
        # Agregar información del directorio actual a la respuesta si es relevante
        if any(keyword in command.lower() for keyword in ["crear", "eliminar", "renombrar", "mover", "carpeta", "archivo"]):
            respuesta += f"\n\n📁 *Directorio actual: {current_working_directory}*"
    
        audio_path = None
        if modo_voz == "Voz y texto":
            tts = TTS()
            audio_path = tts.process(respuesta)
        
        return {
            "success": True,
            "message": respuesta,
            "memory": memory.load_memory_variables({}),
            "audio_path": audio_path,
            "current_directory": current_working_directory  # Para que app.py pueda usar esta info
        }

    except Exception as e:
        error_message = f"Oops, no pude procesarlo. Error: {str(e)}. ¿Podés reformularlo?"
        return {"success": False, "message": error_message}