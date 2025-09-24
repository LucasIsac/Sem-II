# agent.py
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
    convert_pdf_to_word_cloudconvert, convert_pdf_to_word_local, get_datetime, 
    create_folder, delete_file, delete_folder, move_file, move_folder, 
    create_backup, convert_word_to_pdf, read_file_content, search_in_file, 
    create_zip_archive, extract_zip_archive, move_files_batch, rename_files_batch, 
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
    buscar_equipo_proyecto
)
from schemas import ContactoInput


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "tu_api_key_de_google_gemini_aqui":
    raise ValueError("Por favor configura tu API key de Gemini en el archivo .env")

# Definir las herramientas disponibles

tools = [
    Tool(
        name="rename_file",
        func=lambda x: rename_file(*x.split("|")),
        description="Útil para renombrar archivos. Formato: nombre_actual|nuevo_nombre"
    ),
    Tool(
        name="rename_folder",
        func=lambda x: rename_folder(*x.split("|")),
        description="Útil para renombrar carpetas. Formato: nombre_actual|nuevo_nombre"
    ),
    Tool(
        name="convert_pdf_to_word_cloudconvert",
        func=lambda x: convert_pdf_to_word_cloudconvert(x),
        description="Útil para convertir archivos PDF a formato Word manteniendo formato y imágenes. La entrada debe ser la ruta al archivo PDF."
    ),
    Tool(
        name="convert_image_format",
        func=lambda x: convert_image_format(*x.split("|")),
        description="Útil para convertir una imagen a otro formato (ej. jpg a png). Formato: ruta_de_la_imagen|nuevo_formato"
    ),
    Tool(
        name="search_files",
        func=search_files,
        description="Útil para buscar archivos. Formato: patrón_de_búsqueda"
    ),
    Tool(
        name="get_datetime",
        func=get_datetime,
        description="Útil para obtener la fecha y hora actual."
    ),
    Tool(
        name="convert_pdf_to_word_local",
        func=lambda x: convert_pdf_to_word_local(x),
        description="Convierte un PDF a Word localmente. Úsalo como alternativa si la conversión con CloudConvert falla. La entrada debe ser la ruta al archivo PDF."
    ),
    Tool(
        name="create_folder",
        func=create_folder,
        description="Útil para crear una nueva carpeta. La entrada debe ser el nombre de la carpeta a crear."
    ),
    Tool(
        name="delete_file",
        func=delete_file,
        description="Útil para eliminar un archivo. La entrada debe ser el nombre del archivo a eliminar."
    ),
    Tool(
        name="delete_folder",
        func=delete_folder,
        description="Útil para eliminar una carpeta y todo su contenido. La entrada debe ser el nombre de la carpeta a eliminar."
    ),
    Tool(
        name="move_file",
        func=lambda x: move_file(*x.split("|")),
        description="Mueve un archivo a una carpeta. Formato: 'ruta_origen_completa|ruta_destino'. El origen DEBE ser la ruta completa desde el directorio de trabajo. Ejemplo: si el usuario dice 'mueve mi_archivo.txt que está en la carpeta borradores a la carpeta final', la entrada para la herramienta debe ser 'borradores/mi_archivo.txt|final'."
    ),
    Tool(
        name="move_folder",
        func=lambda x: move_folder(*x.split("|")),
        description="Mueve una carpeta a otra. Formato: 'ruta_origen_completa|ruta_destino'. El origen DEBE ser la ruta completa desde el directorio de trabajo. Ejemplo: si el usuario dice 'mueve la carpeta imagenes que está dentro de prueba a la carpeta de pruebas', la entrada para la herramienta debe ser 'prueba/imagenes|carpeta de pruebas'."
    ),
    Tool(
        name="create_backup",
        func=create_backup,
        description="Útil para crear un backup de un archivo o carpeta. La entrada debe ser el nombre del archivo o carpeta."
    ),
    Tool(
        name="convert_word_to_pdf",
        func=convert_word_to_pdf,
        description="Útil para convertir un archivo de Word (.docx) a PDF. La entrada debe ser el nombre del archivo de Word."
    ),
    Tool(
        name="read_file_content",
        func=read_file_content,
        description="Útil para leer y obtener el contenido de un archivo. Funciona con texto, código, PDFs o Word."
    ),
    Tool(
        name="search_in_file",
        func=lambda x: search_in_file(x.split("|")[1], x.split("|")[0]),
        description="Útil para buscar palabras o frases dentro de un archivo. Formato: palabra|archivo."
    ),
    Tool(
        name="create_zip_archive",
        func=lambda x: create_zip_archive(*x.split("|")),
        description="Útil para comprimir archivos o carpetas en un ZIP. Solo indicá qué querés comprimir y cómo querés llamar al ZIP."
    ),
    Tool(
        name="extract_zip_archive",
        func=lambda x: extract_zip_archive(*x.split("|")),
        description="Útil para descomprimir un archivo ZIP. Indicá el nombre del ZIP y la carpeta donde querés extraerlo."
    ),
    Tool(
        name="move_files_batch",
        func=lambda x: move_files_batch(*x.split("|")),
        description="Útil para mover múltiples archivos a una carpeta. Formato: 'archivo1,archivo2,...|carpeta_destino'."
    ),
    Tool(
        name="rename_files_batch",
        func=lambda x: rename_files_batch(*x.split("|")),
        description="Útil para renombrar múltiples archivos siguiendo un patrón. Formato: 'archivo1,archivo2,...|nuevo_nombre_base'. Los archivos serán renombrados como nuevo_nombre_base_1, nuevo_nombre_base_2, etc."
    ),
    Tool(
        name="convert_images_batch",
        func=lambda x: convert_images_batch(*x.split("|")),
        description="Útil para convertir múltiples imágenes a otro formato. Formato: 'imagen1,imagen2,...|nuevo_formato'."
    ),
    Tool(
        name="consultar_base_de_conocimiento",
        func=consultar_base_de_conocimiento,
        description=(
            "Realiza consultas a la base de conocimiento Mangle. "
            "Útil para preguntas como '¿quién trabaja en Proyecto Alpha?', '¿cuáles son los contactos prioritarios?', etc. "
            "La entrada debe ser una consulta Mangle válida, por ejemplo: 'trabaja_en(Persona, \"Proyecto Alpha\").' "
            "o 'contacto_prioritario(X).'"
        )
    ),
    Tool(
        name="agregar_contacto",
        func=agregar_contacto,
        description=(
            "Agrega un nuevo contacto al archivo de contactos y a la base de conocimiento Mangle usando el esquema unificado. "
            "Esta es la herramienta principal para añadir contactos individuales. "
            "Formato de entrada: 'nombre, puesto, email, proyecto[, archivo_opcional]' "
            "Ejemplo: 'Juan Pérez, Desarrollador, juan.perez@email.com, Proyecto Alpha'"
        )
    ),
    Tool(
        name="cargar_todos_los_contactos_desde_archivo",
        func=cargar_todos_los_contactos_desde_archivo,
        description=(
            "Carga TODOS los contactos desde el archivo de contactos a la base de conocimiento Mangle. "
            "Útil cuando necesitas sincronizar completamente el archivo con la base de datos. "
            "Entrada opcional: nombre del archivo (por defecto 'contactos.txt')"
        )
    ),
    Tool(
        name="cargar_conocimiento_desde_archivo",
        func=cargar_conocimiento_desde_archivo,
        description=(
            "Carga reglas y hechos base desde un archivo .mgl a la base de conocimiento Mangle. "
            "Útil para cargar el esquema inicial, reglas de negocio, etc. "
            "Entrada: ruta al archivo .mgl (ej: 'conocimiento.mangle')"
        )
    ),
    Tool(
        name="inicializar_base_conocimiento_completa",
        func=lambda x: inicializar_base_conocimiento_completa(),  # Ignora el parámetro x
        description=(
            "Inicializa completamente la base de conocimiento Mangle: "
            "1) Carga las reglas base desde conocimiento.mangle "
            "2) Carga todos los contactos desde contactos.txt "
            "Úsalo cuando necesites 'resetear' o 'sincronizar' todo el sistema de conocimiento."
        )
    ),
    Tool(
        name="limpiar_base_de_conocimiento",
        func=limpiar_base_de_conocimiento,
        description=(
            "Limpia completamente la base de conocimiento Mangle (elimina todos los hechos y reglas). "
            "¡CUIDADO! Esta operación es irreversible. Úsala solo cuando el usuario lo pida explícitamente."
        )
    ),
    Tool(
        name="buscar_contactos_por_proyecto",
        func=buscar_contactos_por_proyecto,
        description=(
            "Busca todos los contactos que trabajan en un proyecto específico. "
            "Entrada: nombre del proyecto (ej: 'Proyecto Alpha')"
        )
    ),
    Tool(
    name="buscar_contactos_prioritarios", 
    func=lambda x: buscar_contactos_prioritarios(),  # Ignora el parámetro x
    description=(
        "Encuentra contactos prioritarios basado en las reglas de negocio definidas. "
        "No requiere entrada específica."
        )
    ),
    Tool(
    name="listar_todos_los_proyectos",
    func=lambda x: listar_todos_los_proyectos(),  # Ignora el parámetro x
    description=(
        "Lista todos los proyectos únicos en la base de conocimiento. "
        "No requiere entrada específica."
        )
    ),
     # ===== HERRAMIENTAS DE MÉTRICAS Y GESTIÓN DE PROYECTOS =====
    Tool(
        name="agregar_metricas_proyecto",
        func=agregar_metricas_proyecto,
        description=(
            "Configura métricas completas de un proyecto (fechas, presupuesto, prioridad, etc.). "
            "Formato: 'proyecto, estado, fecha_inicio, fecha_fin, presupuesto, prioridad, horas_estimadas' "
            "Ejemplo: 'Proyecto Gamma, activo, 2025-01-15, 2025-06-30, 75000, alta, 500'"
        )
    ),
    Tool(
        name="asignar_horas_persona_proyecto",
        func=asignar_horas_persona_proyecto,
        description=(
            "Asigna una persona a un proyecto con métricas de tiempo y rol. "
            "Formato: 'persona, proyecto, horas_semanales, porcentaje_dedicacion, rol_en_proyecto' "
            "Ejemplo: 'Juan Pérez, Proyecto Gamma, 25, 60, desarrollador_senior'"
        )
    ),
    Tool(
        name="registrar_progreso_proyecto",
        func=registrar_progreso_proyecto,
        description=(
            "Actualiza el progreso de un proyecto. "
            "Formato: 'proyecto, porcentaje_completado, horas_trabajadas[, fecha_reporte]' "
            "Ejemplo: 'Proyecto Gamma, 45, 180'"
        )
    ),
    Tool(
        name="calcular_metricas_proyecto",
        func=calcular_metricas_proyecto,
        description=(
            "Genera un reporte completo de métricas para un proyecto específico. "
            "Entrada: nombre del proyecto"
        )
    ),
    Tool(
        name="generar_dashboard_metricas",
        func=lambda x: generar_dashboard_metricas(),
        description=(
            "Genera un dashboard completo con todas las métricas del equipo y proyectos. "
            "Incluye alertas, estados, y resúmenes ejecutivos. No requiere entrada."
        )
    ),
    Tool(
        name="detectar_proyectos_en_riesgo",
        func=lambda x: detectar_proyectos_en_riesgo(),
        description=(
            "Identifica proyectos que están en riesgo basado en progreso y fechas límite. "
            "No requiere entrada."
        )
    ),
    Tool(
        name="buscar_proyectos_por_estado",
        func=buscar_proyectos_por_estado,
        description=(
            "Busca proyectos filtrados por estado específico. "
            "Entrada: estado (ej: 'activo', 'completado', 'pausado')"
        )
    ),
    Tool(
        name="buscar_equipo_proyecto",
        func=buscar_equipo_proyecto,
        description=(
            "Muestra todo el equipo asignado a un proyecto específico. "
            "Entrada: nombre del proyecto"
        )
    )
]

def initialize_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=256
    )

def process_command(command: str, chat_history: list = None, modo_voz: str = "Voz y texto", file_structure: str = ""):


    """
    Procesa un comando de lenguaje natural utilizando un agente de IA para seleccionar
    y ejecutar la herramienta adecuada.
    """
    try:
        llm = initialize_llm()

        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        if chat_history:
            for message in chat_history:
                if message['type'] == 'human':
                    memory.chat_memory.add_user_message(message['content'])
                else:
                    memory.chat_memory.add_ai_message(message['content'])

        # Contexto inicial del sistema
        system_prompt = f"""Eres FileMate AI, un asistente de gestión de archivos. Tu única función es interpretar las instrucciones del usuario y ejecutar las herramientas correspondientes con los parámetros correctos. Sigue estas reglas de forma estricta.

        **CONTEXTO DE ARCHIVOS ACTUAL:**
        Aquí está la estructura de archivos y carpetas con la que estás trabajando. Úsala como referencia principal para localizar archivos y entender dónde están las cosas. No tienes que pedirle al usuario esta información, ya la tienes aquí:
        ```
        {file_structure}
        ```

        **REGLAS GENERALES:**

        1.  **Usa el Contexto:** El **CONTEXTO DE ARCHIVOS ACTUAL** es tu referencia principal para saber qué archivos existen y dónde están. Úsalo para informar tus decisiones.

        2.  **Mover Archivos es Sencillo:** Para mover un archivo, solo necesitas su nombre y el destino. La herramienta `move_file` es inteligente y lo buscará por ti si no está en la raíz.
            -   **Ejemplo:** Si el usuario dice "mueve `doc.txt` a `prueba`", la acción correcta es `move_file` con el input `doc.txt|prueba`.

        3.  **Verificación de Nombres:**
            -   Los nombres de archivos y carpetas deben ser **EXACTOS**.
            -   Si sospechas de un error tipográfico en el nombre de la carpeta de destino (ej. "prueva" en lugar de "prueba"), **DEBES** usar la herramienta `search_files` para buscar el nombre correcto antes de intentar mover nada.
            -   **NO CREES CARPETAS NUEVAS** a menos que el usuario lo pida explícitamente. Si la carpeta de destino no existe, informa al usuario.

        4.  **UN SOLO ORIGEN, UN SOLO DESTINO:** Cada instrucción de movimiento debe resolverse a un único origen y un único destino.

        **Funciones generales:**
        - Renombrar, crear, mover y eliminar archivos/carpetas.
        - Crear backups.
        - Convertir documentos e imágenes.
        - Buscar archivos.
        - Obtener fecha y hora.

        Responde en español. Tu nombre es FileMate AI."""

        agent_executor = initialize_agent(
            tools,
            llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            handle_parsing_errors=True,
            agent_kwargs={
                "system_message": system_prompt
            }
        )

        result = agent_executor.invoke({"input": command})
        respuesta = str(result["output"])

        # Determinar si la respuesta es un mensaje de éxito o de error
        # basado en el contenido del string que devuelven las herramientas.
        is_success = not respuesta.lower().startswith(("error", "no pude", "no se pudo"))

        # Determinar si la operación modificó el sistema de archivos
        modifying_tools = [
            "rename_file", "rename_folder", "convert_pdf_to_word_cloudconvert", 
            "convert_image_format", "convert_pdf_to_word_local", "create_folder", 
            "delete_file", "delete_folder", "move_file", "move_folder", 
            "create_backup", "convert_word_to_pdf", "create_zip_archive", 
            "extract_zip_archive", "move_files_batch", "rename_files_batch", 
            "convert_images_batch"
        ]
        
        # Extraer la herramienta utilizada de la traza del agente si está disponible
        tool_used = ""
        if "intermediate_steps" in result and result["intermediate_steps"]:
            tool_used = result["intermediate_steps"][0][0].tool

        files_changed = is_success and tool_used in modifying_tools

        audio_path = None
        if modo_voz == "Voz y texto" and is_success:
            try:
                tts = TTS()
                audio_path = tts.process(respuesta)
            except Exception as e:
                print(f"Error al generar audio TTS: {e}")
                # No detenemos la ejecución, solo no habrá audio.
        
        return {
            "success": is_success,
            "message": respuesta,
            "memory": memory.load_memory_variables({}),
            "audio_path": audio_path,
            "files_changed": files_changed
        }

    except Exception as e:
        error_message = f"Oops, ocurrió un error general al procesar tu comando. Error: {str(e)}. ¿Podrías intentarlo de nuevo de otra manera?"
        return {"success": False, "message": error_message, "files_changed": False}
