import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from tools import rename_file, rename_folder, convert_pdf_to_word_cloudconvert, convert_image_format, list_files, search_files
from langchain_core.tools import Tool

# Cargar variables de entorno
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Verificar si la API key está configurada
if not api_key:
    raise ValueError("La variable de entorno OPENAI_API_KEY no está configurada.")

# Inicializar el modelo de lenguaje
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)

# Definir las herramientas que el agente puede usar
tools = [
    Tool.from_function(
        func=rename_file,
        name="rename_file",
        description="Renombra un archivo"
    ),
    Tool.from_function(
        func=rename_folder,
        name="rename_folder",
        description="Renombra una carpeta"
    ),
    Tool.from_function(
        func=convert_pdf_to_word_cloudconvert,
        name="convert_pdf_to_word_cloudconvert",
        description="Convierte un archivo PDF a Word"
    ),
    Tool.from_function(
        func=convert_image_format,
        name="convert_image_format",
        description="Convierte una imagen a otro formato"
    ),
    Tool.from_function(
        func=list_files,
        name="list_files",
        description="Lista todos los archivos en un directorio"
    ),
    Tool.from_function(
        func=search_files,
        name="search_files",
        description="Busca archivos que coincidan con un patrón"
    ),
]

# Vincular las herramientas al modelo
llm_with_tools = llm.bind_tools(tools)

# Crear el prompt para el agente
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Eres un asistente útil que puede gestionar archivos y carpetas."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Crear el agente
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

# Crear el ejecutor del agente
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def get_agent_executor():
    """Retorna el ejecutor del agente."""
    return agent_executor
