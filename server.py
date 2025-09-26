# server.py - Servidor FASTAPI para operaciones con permisos elevados
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from tools import SystemManager
import os

app = FastAPI(title="EVA Files Server")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Autenticación
API_KEY = os.getenv("FILEMATE_API_KEY", "default-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key")

class SystemCommand(BaseModel):
    command: str
    parameters: dict = {}

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.post("/api/system/command")
async def execute_system_command(
    command: SystemCommand, 
    api_key: str = Security(get_api_key)
):
    """Ejecuta comandos del sistema de forma segura"""
    system_manager = SystemManager()
    
    try:
        if command.command == "get_resources":
            result = system_manager.get_system_resources()
        elif command.command == "open_program":
            result = system_manager.open_program(command.parameters.get("name"))
        elif command.command == "search_files":
            result = system_manager.search_files_os(
                command.parameters.get("pattern"),
                command.parameters.get("path")
            )
        elif command.command == "get_processes":
            result = system_manager.get_running_processes()
        else:
            raise HTTPException(status_code=400, detail="Comando no válido")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)
