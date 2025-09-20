# agent.py

import os
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from tts import TTS
from tools import rename_file, rename_folder, convert_image_format, search_files, convert_pdf_to_word_cloudconvert, convert_pdf_to_word_local,  get_datetime, create_folder, delete_file, delete_folder, move_file, move_folder, create_backup, convert_word_to_pdf, read_file_content, search_in_file, consultar_base_de_conocimiento



load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "tu_api_key_de_google_gemini_aqui":
    raise ValueError("Por favor configura tu API key de Gemini en el archivo .env")

# Definir las herramientas disponibles
# Las descripciones son muy importantes para que el LLM sepa cómo usar la herramienta.

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
        name="consultar_base_de_conocimiento",
        func=consultar_base_de_conocimiento,
        description="Útil para realizar consultas complejas o deductivas sobre una base de conocimiento. Úsalo cuando el usuario haga preguntas que requieran razonar sobre relaciones entre datos, como '¿quién es prioritario?' o '¿qué proyectos están relacionados?'. La entrada debe ser la consulta en formato Mangle, por ejemplo: 'contacto_prioritario(X).'"
    )
]

def initialize_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=256
    )

def process_command(command: str, chat_history: list = None, modo_voz: str = "Voz y texto"):
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
        system_prompt = """Eres FileMate AI, un asistente de gestión de archivos. Tu única función es interpretar las instrucciones del usuario y ejecutar las herramientas correspondientes con los parámetros correctos. Sigue estas reglas de forma estricta.

        **REGLAS OBLIGATORIAS PARA MOVER ARCHIVOS Y CARPETAS:**

        1.  **ANÁLISIS DE RUTA COMPLETA:** Tu objetivo principal es determinar la **RUTA DE ORIGEN COMPLETA** y la **CARPETA DE DESTINO**.
        
        2.  **CONSTRUCCIÓN DEL ORIGEN:**
            -   Las palabras "en", "dentro de", "desde" indican que un archivo o carpeta está dentro de otra. Debes construir una ruta anidada.
            -   **EJEMPLO 1**: Si el usuario dice "Mueve `fotos.zip` que está en `documentos` a la carpeta `backups`", la ruta de origen es `documentos/fotos.zip`. El destino es `backups`. La herramienta se llama con `documentos/fotos.zip|backups`.
            -   **EJEMPLO 2**: Si el usuario dice "Mueve la carpeta `imagenes` que está en `pruebas` a `carpeta de prueba`", la ruta de origen es `pruebas/imagenes`. El destino es `carpeta de prueba`. La herramienta se llama con `pruebas/imagenes|carpeta de prueba`.
            -   **NUNCA** asumas que el origen es solo el primer nombre que aparece. Analiza la frase completa.

        3.  **VERIFICACIÓN DE NOMBRES (REGLA CRÍTICA):**
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
            "audio_path": audio_path
        }

    except Exception as e:
        error_message = f"Oops, ocurrió un error general al procesar tu comando. Error: {str(e)}. ¿Podrías intentarlo de nuevo de otra manera?"
        return {"success": False, "message": error_message}
