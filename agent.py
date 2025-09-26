# agent.py - Agente extendido con memoria de contexto de carpeta (CORREGIDO)
import os
import grpc
import mangle_pb2
import mangle_pb2_grpc
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from tts import TTS
from tools import (
    rename_file, rename_folder, convert_image_format, search_files, 
    convert_pdf_to_word_cloudconvert, convert_pdf_to_word_local, 
    create_folder, delete_file, delete_folder, move_file, move_folder, 
    create_backup, convert_word_to_pdf, read_file_content, search_in_file, 
    create_zip_archive, extract_zip_archive, move_files_batch, rename_files_batch, system_manager,
    list_files,
    convert_images_batch,
    # FUNCIONES MANGLE BÁSICAS:
    consultar_base_de_conocimiento, agregar_contacto, 
    cargar_todos_los_contactos_desde_archivo, cargar_conocimiento_desde_archivo,
    inicializar_base_conocimiento_completa, limpiar_base_de_conocimiento,
    buscar_contactos_por_proyecto, buscar_contactos_prioritarios, 
    listar_todos_los_proyectos,
    # NUEVAS FUNCIONES DE MÉTRICAS:
    agregar_metricas_proyecto, asignar_horas_persona_proyecto,
    registrar_progreso_proyecto, calcular_metricas_proyecto,
    detectar_proyectos_en_riesgo, calcular_carga_trabajo_equipo,
    generar_dashboard_metricas, buscar_proyectos_por_estado,
    buscar_equipo_proyecto,
    # NUEVAS FUNCIONES DE ARCHIVOS DE TEXTO:
    create_text_file, edit_text_file, append_to_text_file, insert_text_at_line,
    replace_text_in_file, get_file_info
)
from schemas import ContactoInput

# Importar dashboard del sistema (asegúrate de que existe)
try:
    from system_dashboard import get_system_dashboard_response
except ImportError:
    def get_system_dashboard_response():
        return "Dashboard del sistema no disponible - falta instalar dependencias."

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

def set_current_directory(new_directory: str):
    """Establece un nuevo directorio de trabajo absoluto"""
    global current_working_directory

    # Convertir a ruta absoluta, relativa al directorio actual
    if not os.path.isabs(new_directory):
        new_directory = os.path.abspath(os.path.join(current_working_directory, new_directory))
    
    # Crear la carpeta si no existe
    os.makedirs(new_directory, exist_ok=True)

    current_working_directory = new_directory
    return f"Directorio de trabajo cambiado a: {current_working_directory}"

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

def create_text_file_with_context(params):
    """Crea un archivo de texto en el directorio actual"""
    global current_working_directory
    parts = params.split("|", 1)
    file_name = parts[0]
    content = parts[1] if len(parts) > 1 else ""
    return create_text_file(file_name, content, current_working_directory)

def edit_text_file_with_context(params):
    """Edita un archivo de texto en el directorio actual"""
    global current_working_directory
    parts = params.split("|")
    if len(parts) < 2:
        return {"success": False, "message": "Formato incorrecto. Usar: archivo|contenido|modo"}
    
    file_name = parts[0]
    content = parts[1]
    mode = parts[2] if len(parts) > 2 else "overwrite"
    return edit_text_file(file_name, content, mode, current_working_directory)

def append_to_text_file_with_context(params):
    """Agrega contenido al final de un archivo en el directorio actual"""
    global current_working_directory
    parts = params.split("|", 1)
    if len(parts) < 2:
        return {"success": False, "message": "Formato incorrecto. Usar: archivo|contenido"}
    return append_to_text_file(parts[0], parts[1], current_working_directory)

def replace_text_in_file_with_context(params):
    """Busca y reemplaza texto en un archivo del directorio actual"""
    global current_working_directory
    parts = params.split("|")
    if len(parts) < 3:
        return {"success": False, "message": "Formato incorrecto. Usar: archivo|texto_buscar|texto_reemplazar"}
    return replace_text_in_file(parts[0], parts[1], parts[2], current_working_directory)

def get_file_info_with_context(file_name):
    """Obtiene información de un archivo en el directorio actual"""
    global current_working_directory
    return get_file_info(file_name, current_working_directory)

# Definir las herramientas disponibles con contexto
tools = [
    # ===== HERRAMIENTAS DE CONTEXTO DE CARPETA =====
    Tool(
        name="get_current_directory",
        func=lambda x: get_current_directory(),
        description="Muestra el directorio de trabajo actual. Sin parámetros."
    ),
    Tool(
        name="set_current_directory", 
        func=set_current_directory,
        description="Cambia el directorio de trabajo actual. Parámetro: nueva_ruta"
    ),
    
    # ===== HERRAMIENTAS DE ARCHIVOS CON CONTEXTO =====
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
    
    # ===== HERRAMIENTAS DE CONVERSIÓN Y PROCESAMIENTO =====
    Tool(
        name="convert_image_format",
        func=lambda x: convert_image_format(*x.split("|")),
        description="Convierte una imagen a otro formato. Formato: ruta_imagen|nuevo_formato"
    ),
    Tool(
        name="convert_pdf_to_word_cloudconvert",
        func=lambda x: convert_pdf_to_word_cloudconvert(x),
        description="Convierte un PDF a Word usando CloudConvert. Parámetro: ruta del PDF."
    ),
    Tool(
        name="convert_pdf_to_word_local",
        func=lambda x: convert_pdf_to_word_local(x),
        description="Convierte un PDF a Word localmente. Úsalo como alternativa si la conversión con CloudConvert falla."
    ),
    Tool(
        name="convert_word_to_pdf",
        func=lambda x: convert_word_to_pdf(x),
        description="Convierte un archivo de Word (.docx) a PDF. Parámetro: ruta del archivo Word."
    ),
    Tool(
        name="convert_images_batch",
        func=lambda x: convert_images_batch(*x.split("|")),
        description="Convierte múltiples imágenes a otro formato. Formato: 'imagen1,imagen2,...|nuevo_formato'."
    ),
    
    # ===== HERRAMIENTAS DE BÚSQUEDA =====
    Tool(
        name="search_files",
        func=search_files,
        description="Busca archivos en la carpeta actual. Parámetro: patrón de búsqueda"
    ),
    Tool(
        name="search_files_smart",
        func=lambda x: system_manager.search_files_smart(*x.split("|") if "|" in x else (x, None)),
        description="Busca archivos en todo el sistema. Formato: patrón|ruta_opcional."
    ),
    Tool(
        name="search_in_file",
        func=lambda x: search_in_file(x.split("|")[1], x.split("|")[0]),
        description="Busca palabras o frases dentro de un archivo. Formato: palabra|archivo."
    ),
    
    # ===== HERRAMIENTAS DE ARCHIVOS Y COMPRESIÓN =====
    Tool(
        name="read_file_content",
        func=read_file_content,
        description="Lee y obtiene el contenido de un archivo. Funciona con texto, código, PDFs o Word."
    ),
    Tool(
        name="create_backup",
        func=lambda x: create_backup(x),
        description="Crea un backup de un archivo o carpeta. Parámetro: nombre del archivo o carpeta."
    ),
    Tool(
        name="create_zip_archive",
        func=lambda x: create_zip_archive(*x.split("|")),
        description="Comprime archivos o carpetas en un ZIP. Formato: archivos_a_comprimir|nombre_zip"
    ),
    Tool(
        name="extract_zip_archive",
        func=lambda x: extract_zip_archive(*x.split("|")),
        description="Descomprime un archivo ZIP. Formato: archivo_zip|carpeta_destino"
    ),
    
    # ===== HERRAMIENTAS BATCH =====
    Tool(
        name="move_files_batch",
        func=lambda x: move_files_batch(*x.split("|")),
        description="Mueve múltiples archivos a una carpeta. Formato: 'archivo1,archivo2,...|carpeta_destino'."
    ),
    Tool(
        name="rename_files_batch",
        func=lambda x: rename_files_batch(*x.split("|")),
        description="Renombra múltiples archivos siguiendo un patrón. Formato: 'archivo1,archivo2,...|nuevo_nombre_base'."
    ),
    
    # ===== HERRAMIENTAS DEL SISTEMA =====
    Tool(
        name="get_system_resources",
        func=lambda x: system_manager.get_system_resources(),
        description="Obtiene información básica sobre el uso de CPU, memoria y disco del sistema. No requiere parámetros."
    ),
    Tool(
        name="show_system_dashboard", 
        func=lambda x: get_system_dashboard_response(),
        description="Muestra un dashboard completo con gráficos y recomendaciones del sistema. Usar cuando el usuario pida ver el estado detallado de recursos."
    ),
    Tool(
        name="open_program",
        func=lambda x: system_manager.open_program(x),
        description="Abre un programa en el sistema operativo. Parámetro: nombre_del_programa."
    ),
    Tool(
        name="get_running_processes",
        func=lambda x: system_manager.get_running_processes(),
        description="Muestra la lista de procesos en ejecución ordenados por uso de memoria. Sin parámetros."
    ),
    
    # ===== HERRAMIENTAS MANGLE - CONTACTOS =====
    Tool(
        name="consultar_base_de_conocimiento",
        func=consultar_base_de_conocimiento,
        description="Realiza consultas a la base de conocimiento Mangle. Entrada: consulta Mangle válida."
    ),
    Tool(
        name="agregar_contacto",
        func=agregar_contacto,
        description="Agrega un nuevo contacto. Formato: 'nombre, puesto, email, proyecto[, archivo_opcional]'"
    ),
    Tool(
        name="cargar_todos_los_contactos_desde_archivo",
        func=cargar_todos_los_contactos_desde_archivo,
        description="Carga TODOS los contactos desde archivo a la base de conocimiento. Entrada opcional: nombre del archivo."
    ),
    Tool(
        name="cargar_conocimiento_desde_archivo",
        func=cargar_conocimiento_desde_archivo,
        description="Carga reglas base desde un archivo .mgl. Entrada: ruta al archivo .mgl"
    ),
    Tool(
        name="inicializar_base_conocimiento_completa",
        func=lambda _: inicializar_base_conocimiento_completa(),
        description="Inicializa completamente la base de conocimiento Mangle (reglas + contactos). No requiere parámetros."
    ),
    Tool(
        name="limpiar_base_de_conocimiento",
        func=lambda _: limpiar_base_de_conocimiento(),
        description="Limpia completamente la base de conocimiento. No requiere parámetros. ¡CUIDADO! Operación irreversible."
    ),
    Tool(
        name="buscar_contactos_por_proyecto",
        func=buscar_contactos_por_proyecto,
        description="Busca todos los contactos que trabajan en un proyecto específico. Entrada: nombre del proyecto"
    ),
    Tool(
        name="buscar_contactos_prioritarios", 
        func=lambda x: buscar_contactos_prioritarios(),
        description="Encuentra contactos prioritarios basado en reglas de negocio. No requiere entrada."
    ),
    Tool(
        name="listar_todos_los_proyectos",
        func=lambda x: listar_todos_los_proyectos(),
        description="Lista todos los proyectos únicos en la base de conocimiento. No requiere entrada."
    ),
    
    # ===== HERRAMIENTAS MANGLE - MÉTRICAS Y GESTIÓN DE PROYECTOS =====
    Tool(
        name="agregar_metricas_proyecto",
        func=agregar_metricas_proyecto,
        description="Configura métricas de proyecto. Formato: 'proyecto, estado, fecha_inicio, fecha_fin, presupuesto, prioridad, horas_estimadas'"
    ),
    Tool(
        name="asignar_horas_persona_proyecto",
        func=asignar_horas_persona_proyecto,
        description="Asigna persona a proyecto con métricas. Formato: 'persona, proyecto, horas_semanales, porcentaje_dedicacion, rol_en_proyecto'"
    ),
    Tool(
        name="registrar_progreso_proyecto",
        func=registrar_progreso_proyecto,
        description="Actualiza progreso de proyecto. Formato: 'proyecto, porcentaje_completado, horas_trabajadas[, fecha_reporte]'"
    ),
    Tool(
        name="calcular_metricas_proyecto",
        func=calcular_metricas_proyecto,
        description="Genera reporte completo de métricas para un proyecto específico. Entrada: nombre del proyecto"
    ),
    Tool(
        name="generar_dashboard_metricas",
        func=lambda x: generar_dashboard_metricas(),
        description="Genera dashboard completo con métricas del equipo y proyectos. No requiere entrada."
    ),
    Tool(
        name="detectar_proyectos_en_riesgo",
        func=lambda x: detectar_proyectos_en_riesgo(),
        description="Identifica proyectos en riesgo basado en progreso y fechas. No requiere entrada."
    ),
    Tool(
        name="buscar_proyectos_por_estado",
        func=buscar_proyectos_por_estado,
        description="Busca proyectos por estado específico. Entrada: estado (ej: 'activo', 'completado', 'pausado')"
    ),
    Tool(
        name="buscar_equipo_proyecto",
        func=buscar_equipo_proyecto,
        description="Muestra equipo asignado a un proyecto específico. Entrada: nombre del proyecto"
    ),
    Tool(
        name="create_text_file",
        func=lambda x: create_text_file(*x.split("|", 1)),
        description="Crea un archivo de texto. Formato: nombre_archivo|contenido (contenido opcional)"
    ),
    Tool(
        name="edit_text_file",
        func=lambda x: edit_text_file(*x.split("|")),
        description="Edita un archivo de texto. Formato: nombre_archivo|contenido|modo (modo: overwrite/append/prepend)"
    ),
    Tool(
        name="append_to_text_file",
        func=lambda x: append_to_text_file(*x.split("|", 1)),
        description="Agrega contenido al final de un archivo de texto. Formato: nombre_archivo|contenido"
    ),
    Tool(
        name="insert_text_at_line",
        func=lambda x: insert_text_at_line(x.split("|")[0], int(x.split("|")[1]), x.split("|")[2]),
        description="Inserta texto en una línea específica. Formato: nombre_archivo|número_línea|contenido"
    ),
    Tool(
        name="replace_text_in_file",
        func=lambda x: replace_text_in_file(*x.split("|")),
        description="Busca y reemplaza texto en un archivo. Formato: nombre_archivo|texto_buscar|texto_reemplazar"
    ),
    Tool(
        name="get_file_info",
        func=lambda x: get_file_info(x),
        description="Obtiene información detallada de un archivo (tamaño, líneas, palabras, etc.). Parámetro: nombre_archivo"
    ),
    Tool(
        name="create_text_file",
        func=create_text_file_with_context,
        description="Crea un archivo de texto en el directorio actual. Formato: nombre_archivo|contenido (contenido opcional)"
    ),
    Tool(
        name="edit_text_file",
        func=edit_text_file_with_context,
        description="Edita un archivo de texto en el directorio actual. Formato: nombre_archivo|contenido|modo (modo: overwrite/append/prepend)"
    ),
    Tool(
        name="append_to_text_file",
        func=append_to_text_file_with_context,
        description="Agrega contenido al final de un archivo de texto en el directorio actual. Formato: nombre_archivo|contenido"
    ),
    Tool(
        name="replace_text_in_file",
        func=replace_text_in_file_with_context,
        description="Busca y reemplaza texto en un archivo del directorio actual. Formato: nombre_archivo|texto_buscar|texto_reemplazar"
    ),
    Tool(
        name="get_file_info",
        func=get_file_info_with_context,
        description="Obtiene información detallada de un archivo en el directorio actual. Parámetro: nombre_archivo"
    ),
]

def initialize_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=512
    )

def process_command(command: str, chat_history: list = None, modo_voz: str = "Voz y texto"):
    """
    Procesa un comando de lenguaje natural con EVA Files manteniendo contexto de carpeta
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

        # Prompt del sistema unificado
        system_prompt = f"""Eres EVA Files, un asistente integral de gestión de archivos, sistema y proyectos. Tu función es interpretar las instrucciones del usuario y ejecutar las herramientas correspondientes.

        ** IMPORTANTE: Cuando ejecutes herramientas debes seguir SIEMPRE este formato ReAct: **
        Thought: explica tu razonamiento
        Action: elige UNA herramienta
        Action Input: parámetros de la herramienta
        Observation: resultado de la herramienta
        Final Answer: tu respuesta final al usuario

        ** REGLA CRÍTICA DE RESPUESTA: **
        - Si la `Observation` ya contiene una respuesta completa y bien formateada (como un dashboard o un reporte), tu `Final Answer` DEBE contener ÚNICAMENTE el texto de la `Observation`, sin añadir frases como "Aquí tienes el dashboard..." ni ningún otro texto introductorio. Simplemente copia el resultado.
        - Responde siempre en español de manera natural pero SIN formato especial (listas, emojis) a menos que la herramienta ya lo devuelva así.
        - No escribas nada fuera del formato ReAct.

        **CONTEXTO ACTUAL:**
        - Directorio de trabajo actual: {current_working_directory}
        - IMPORTANTE: Mantén siempre el contexto del directorio actual entre comandos

        **GESTIÓN DE DIRECTORIO DE TRABAJO:**
        - Cuando el usuario mencione "documentos", "descargas", "escritorio", etc., usa `list_files` con ese parámetro para cambiar el contexto
        - Una vez que cambies a un directorio, TODAS las operaciones posteriores (crear, eliminar, renombrar) se realizan en ese directorio
        - Usa `get_current_directory` para verificar dónde estás trabajando
        - Si necesitas cambiar explícitamente de directorio, usa `set_current_directory`

        **PARA MANEJAR ARCHIVOS:**
        - SIEMPRE trabaja en el directorio actual a menos que el usuario especifique otro
        - Si el usuario no proporciona una ruta completa, asume que se refiere a archivos en el directorio actual
        - Para búsquedas globales usa `search_files_smart`, para búsquedas locales usa `search_files`
        - Cuando crees carpetas o archivos, hazlo en el directorio actual

        **EDICIÓN DE ARCHIVOS DE TEXTO:**
        - Para crear archivos de texto usa `create_text_file`
        - Para editar completamente un archivo usa `edit_text_file` con modo "overwrite"
        - Para agregar contenido al final usa `append_to_text_file` o `edit_text_file` con modo "append"
        - Para agregar al inicio usa `edit_text_file` con modo "prepend"
        - Para insertar en línea específica usa `insert_text_at_line`
        - Para buscar y reemplazar texto usa `replace_text_in_file`
        - Para información del archivo usa `get_file_info`

        **MEMORIA DE CONTEXTO:**
        - Recuerda siempre en qué directorio estás trabajando
        - Si el usuario dice "ahora crea la carpeta X", créala en el directorio donde estuviste trabajando anteriormente
        - No vuelvas al directorio por defecto a menos que el usuario lo pida explícitamente

        **MONITOREO DEL SISTEMA:**
        - Para información detallada de recursos usa `show_system_dashboard`
        - Para consultas simples sobre recursos usa `get_system_resources`
        - Ejemplos: "cómo están los recursos", "muestra el dashboard", "estado del sistema"

        **GESTIÓN DE PROYECTOS MANGLE:**
        - Para contactos usa herramientas como `agregar_contacto`, `buscar_contactos_por_proyecto`
        - Para métricas usa `agregar_metricas_proyecto`, `calcular_metricas_proyecto`, `generar_dashboard_metricas`
        - Para proyectos usa `buscar_proyectos_por_estado`, `detectar_proyectos_en_riesgo`

        **CAPACIDADES PRINCIPALES:**
        - Gestión completa de archivos y carpetas con memoria de contexto
        - Creación y edición avanzada de archivos de texto
        - Conversión de documentos e imágenes
        - Monitoreo y control del sistema operativo
        - Gestión de proyectos y contactos con Mangle
        - Métricas y dashboard de proyectos
        - Operaciones en lote (batch)

        Responde siempre en español de manera natural pero SIN formato especial
        Siempre menciona en qué directorio estás trabajando cuando sea relevante."""

        agent_executor = initialize_agent(
            tools,
            llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            agent_kwargs={
                "system_message": system_prompt
            }
        )

        result = agent_executor.invoke({"input": command})
        respuesta = str(result["output"])

        # Determinar si la respuesta es un mensaje de éxito o de error
        is_success = not respuesta.lower().startswith(("error", "no pude", "no se pudo", "oops"))

        # Determinar si la operación modificó el sistema de archivos
        modifying_tools = [
            "rename_file", "rename_folder", "convert_pdf_to_word_cloudconvert", 
            "convert_image_format", "convert_pdf_to_word_local", "create_folder", 
            "delete_file", "delete_folder", "move_file", "move_folder", 
            "create_backup", "convert_word_to_pdf", "create_zip_archive", 
            "extract_zip_archive", "move_files_batch", "rename_files_batch", 
            "convert_images_batch"
        ]
        
        # Agregar información del directorio actual a la respuesta si es relevante
        if any(keyword in command.lower() for keyword in ["crear", "eliminar", "renombrar", "mover", "carpeta", "archivo"]):
            respuesta += f"\n\n📁 *Directorio actual: {current_working_directory}*"
    
        # Extraer la herramienta utilizada si está disponible
        tool_used = ""
        try:
            if "intermediate_steps" in result and result["intermediate_steps"]:
                tool_used = result["intermediate_steps"][0][0].tool
        except:
            pass

        files_changed = is_success and tool_used in modifying_tools

        audio_path = None
        if modo_voz == "Voz y texto" and is_success:
            try:
                tts = TTS()
                audio_path = tts.process(respuesta)
            except Exception as e:
                print(f"Error al generar audio TTS: {e}")
        
        return {
            "success": is_success,
            "message": respuesta,
            "memory": memory.load_memory_variables({}),
            "audio_path": audio_path,
            "current_directory": current_working_directory,
            "files_changed": files_changed
        }

    except Exception as e:
        error_message = f"Oops, ocurrió un error al procesar tu comando. Error: {str(e)}. ¿Podrías intentarlo de otra manera?"
        return {"success": False, "message": error_message, "files_changed": False}
