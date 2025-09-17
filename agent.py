# agent.py - Agente para procesar comandos con LangChain y Gemma
import os
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI

from tools import rename_file, rename_folder, convert_image_format, search_files, convert_pdf_to_word_cloudconvert, convert_pdf_to_word_local
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar la API key de Gemma desde .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "tu_api_key_de_google_gemini_aqui":
    raise ValueError("Por favor configura tu API key de Gemini en el archivo .env")



# Definir las herramientas disponibles
# Las descripciones son muy importantes para que el LLM sepa cómo usar la herramienta.
tools = [
    Tool(
        name="rename_file",
        func=lambda x: rename_file(*x.split("|")),
        description="Util para renombrar archivos. La entrada deben ser dos strings separados por |: nombre_actual|nuevo_nombre"
    ),
    Tool(
        name="rename_folder",
        func=lambda x: rename_folder(*x.split("|")),
        description="Util para renombrar carpetas. La entrada deben ser dos strings separados por |: nombre_actual|nuevo_nombre"
    ),
    Tool(
        name="convert_pdf_to_word_cloudconvert",
        func=lambda x: convert_pdf_to_word_cloudconvert(x),
        description="Útil para convertir archivos PDF a formato Word manteniendo formato y imágenes. La entrada debe ser la ruta al archivo PDF."
    ),
    Tool(
        name="convert_image_format",
        func=lambda x: convert_image_format(*x.split("|")),
        description="Util para convertir formatos de imagen. La entrada deben ser dos strings separados por |: ruta_imagen|nuevo_formato (ej. jpg, png)"
    ),
    Tool(
        name="search_files",
        func=lambda x: search_files(x),
        description="Util para buscar archivos por un patrón en el nombre. La entrada debe ser el patrón de búsqueda."
    ),
    Tool(
        name="convert_pdf_to_word_local",
        func=lambda x: convert_pdf_to_word_local(x),
        description="Convierte un PDF a Word localmente. Úsalo como alternativa si la conversión con CloudConvert falla. La entrada debe ser la ruta al archivo PDF."
    )
]

# Inicializar el modelo de lenguaje
def initialize_llm():
    """Inicializa el modelo de lenguaje Gemma a través de la API de Google."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=256
    )


# Procesar el comando del usuario usando un agente de LangChain
def process_command(command: str):
    """
    Procesa un comando de lenguaje natural utilizando un agente de IA para seleccionar
    y ejecutar la herramienta adecuada.
    """
    try:
        llm = initialize_llm()
        
        # Inicializamos el agente. ZERO_SHOT_REACT_DESCRIPTION es un tipo de agente estándar
        # que decide qué herramienta usar basándose en las descripciones de las herramientas.
        agent_executor = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True  # Poner en True para ver los pensamientos del agente en la consola
        )
        
        # Ejecutamos el agente con el comando del usuario
        # El agente pensará y decidirá qué herramienta llamar
        result = agent_executor.invoke({"input": command})
        
        # LangChain puede devolver directamente el diccionario de la herramienta o un string.
        # Si es un string, lo envolvemos en el formato esperado.
        if isinstance(result, dict):
            return result
        else:
            return {"success": True, "message": str(result)}

    except Exception as e:
        # Si algo falla durante la ejecución del agente, devolvemos un error.
        error_message = f"El agente de IA no pudo procesar el comando. Error: {str(e)}"
        return {"success": False, "message": error_message}
