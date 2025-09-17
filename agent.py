# agent.py

import os
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from tools import rename_file, rename_folder, convert_image_format, search_files, convert_pdf_to_word_cloudconvert, convert_pdf_to_word_local
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from tts import TTS
from tools import rename_file, rename_folder, convert_image_format, search_files, convert_pdf_to_word_cloudconvert, convert_pdf_to_word_local,  get_datetime


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
    )
]

def initialize_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
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
        system_prompt = """Sos FileMate AI, un asistente especializado en gestión de archivos.
        Tu objetivo es asistir al usuario con tareas de manipulación de archivos.
        Podés ayudar al usuario a realizar las siguientes acciones:
        - 📂 Renombrar archivos
        - 📂 Renombrar carpetas
        - 📄 Convertir PDF a Word (usando CloudConvert o localmente)
        - 🖼️ Convertir imágenes entre formatos
        - 🔎 Buscar archivos
        - 📅 Obtener la fecha y hora actual

        Siempre respondé de manera clara y amigable en español.
        Si te preguntan qué podés hacer, describí estas funciones.
        No digas que sos un modelo de Google ni una IA genérica. Tu nombre es FileMate AI."""

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
    
        audio_path = None
        if modo_voz == "Voz y texto":
            tts = TTS()
            audio_path = tts.process(respuesta)
        
        return {
            "success": True,
            "message": respuesta,
            "memory": memory.load_memory_variables({}),
            "audio_path": audio_path
        }

    except Exception as e:
        error_message = f"Oops, no pude procesarlo. Error: {str(e)}. ¿Podés reformularlo?"
        return {"success": False, "message": error_message}
