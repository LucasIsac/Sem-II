# tools.py - Herramientas extendidas para trabajar a nivel del SO
import os
import sys
import io
import re
import shutil
import json
import platform
import unicodedata
import logging
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
from attr import Converter
from gtts import gTTS
from dotenv import load_dotenv
from PIL import Image
import cloudconvert
import datetime
from docx2pdf import convert as docx2pdf_convert
import PyPDF2
import psutil

# Cargar variables de entorno (CloudConvert API KEY, etc.)
load_dotenv()
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")

# ----------------- Función de Normalización de Texto -----------------
def normalize_string(text: Optional[str]) -> str:
    """
    Normaliza cadenas eliminando acentos, caracteres especiales y espacios múltiples.
    Resultado: solo caracteres ascii, minúsculas, sin signos de puntuación (a-z0-9 y espacios).
    """
    if not isinstance(text, str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', text)
    only_ascii = nfkd_form.encode('ascii', 'ignore').decode('utf-8')
    lower_case = only_ascii.lower()
    cleaned = re.sub(r'[^a-z0-9\s]', '', lower_case)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# ----------------- SEGURIDAD -----------------
class SecurityManager:
    """
    Control básico de rutas y extensiones peligrosas.
    - is_path_allowed: asegura que la ruta esté dentro del home del usuario
      y que no pertenezca a rutas restringidas del sistema.
    - is_extension_allowed: evita manipular extensiones marcadas como peligrosas.
    """
    def __init__(self):
        self.restricted_paths = [
            os.path.abspath(os.path.expanduser("~/.ssh")),
            "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin",
            "/System", "/Library", os.path.abspath("C:\\Windows\\System32"),
            os.path.abspath(os.path.expanduser("~/.config")),
            os.path.abspath(os.path.expanduser("~/.password-store"))
        ]
        # Mantén aquí extensiones que no quieres manipular desde el agente
        self.dangerous_extensions = [".exe", ".bat", ".cmd", ".sh", ".py", ".js", ".vbs", ".ps1"]

    def is_path_allowed(self, path: str) -> bool:
        try:
            abs_path = os.path.abspath(os.path.expanduser(path))
            user_home = os.path.abspath(os.path.expanduser("~"))
            # Debe estar dentro del home del usuario
            if not abs_path.startswith(user_home):
                return False
            # No debe estar dentro de rutas restringidas
            for restricted in self.restricted_paths:
                if restricted and abs_path.startswith(restricted):
                    return False
            return True
        except Exception:
            return False

    def is_extension_allowed(self, filename: str) -> bool:
        _, ext = os.path.splitext(filename)
        return ext.lower() not in self.dangerous_extensions

# ----------------- UTILIDADES -----------------
# Wrapper para list_files con memoria de carpeta y recursividad opcional
def list_files_context(directory: Optional[str] = None, recursive: bool = False) -> List[Dict[str, str]]:
    """
    Lista archivos y carpetas desde directory (por defecto 'files' del proyecto)
    - directory: ruta o carpeta especial (documentos, descargas, escritorio, etc.)
    - recursive: si True, incluye subcarpetas recursivamente
    """
    import streamlit as st

    # Carpeta por defecto
    default_folder = os.path.join(os.getcwd(), "files")

    # Si no hay directory, usa memoria o carpeta por defecto
    if not directory:
        directory = st.session_state.get("last_folder", default_folder)

    abs_path, err = get_absolute_path(directory)
    if err:
        return []

    # Guardar en memoria la última carpeta
    st.session_state["last_folder"] = abs_path

    # Listado de archivos y carpetas
    items = []
    try:
        for entry in os.scandir(abs_path):
            if entry.is_file():
                items.append({"name": entry.name, "type": "archivo", "path": entry.path})
            elif entry.is_dir():
                items.append({"name": entry.name, "type": "carpeta", "path": entry.path})
                # Si es recursivo, agrega contenido de subcarpeta
                if recursive:
                    sub_items = list_files_context(entry.path, recursive=True)
                    items.extend(sub_items)
        # Orden alfabético
        items.sort(key=lambda x: x['name'])
        return items
    except Exception:
        return []



def get_absolute_path(path_input: str, base_dir: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """
    Convierte rutas “naturales” en rutas absolutas:
    - Soporta carpetas especiales: escritorio, documentos, descargas, imagenes
    - Soporta subcarpetas, ej: "documentos/MiCarpeta/archivo.txt"
    - Si es ruta absoluta, la devuelve tal cual
    - Si base_dir está dado, se usa como raíz para rutas relativas
    """
    try:
        if not path_input:
            return None, "Ruta vacía provista"

        # Carpetas comunes
        common_paths = {
            "escritorio": os.path.expanduser("~\\Desktop") if platform.system() == "Windows" else os.path.expanduser("~/Desktop"),
            "documentos": os.path.expanduser("~\\Documents") if platform.system() == "Windows" else os.path.expanduser("~/Documents"),
            "descargas": os.path.expanduser("~\\Downloads") if platform.system() == "Windows" else os.path.expanduser("~/Downloads"),
            "imagenes": os.path.expanduser("~\\Pictures") if platform.system() == "Windows" else os.path.expanduser("~/Pictures")
        }

        path_input = path_input.strip().replace("/", os.sep).replace("\\", os.sep)
        lowered = path_input.lower()

        # Detecta carpeta común al inicio
        abs_path = None
        for key in common_paths:
            if lowered.startswith(key):
                # Obtiene lo que sigue después de la carpeta común
                rest = path_input[len(key):].lstrip("/\\")
                abs_path = os.path.join(common_paths[key], rest)
                break

        # Si no se reconoce como carpeta común
        if abs_path is None:
            if os.path.isabs(path_input):
                abs_path = os.path.abspath(path_input)
            elif base_dir:
                abs_path = os.path.abspath(os.path.join(base_dir, path_input))
            else:
                abs_path = os.path.abspath(os.path.expanduser(path_input))

        # Verificación de seguridad
        security = SecurityManager()
        if not security.is_path_allowed(abs_path):
            return None, "Ruta no permitida por razones de seguridad"

        return abs_path, None

    except Exception as e:
        return None, f"Error resolviendo ruta: {str(e)}"


# ----------------- SISTEMA OPERATIVO -----------------
class SystemManager:
    def __init__(self):
        self.security = SecurityManager()

    def _format_bytes(self, bytes_value: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    def get_system_resources(self) -> Dict[str, Any]:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(os.path.expanduser("~"))
            return {
                "success": True,
                "message": f"Uso de CPU: {cpu_percent}%, Memoria: {memory.percent}%, Disco: {disk.percent}%",
                "details": {
                    "cpu": {
                        "percent": cpu_percent,
                        "cores": cpu_count,
                        "frequency": cpu_freq.current if cpu_freq else "N/A"
                    },
                    "memory": {
                        "percent": memory.percent,
                        "total": self._format_bytes(memory.total),
                        "available": self._format_bytes(memory.available),
                        "used": self._format_bytes(memory.used)
                    },
                    "disk": {
                        "percent": disk.percent,
                        "total": self._format_bytes(disk.total),
                        "free": self._format_bytes(disk.free),
                        "used": self._format_bytes(disk.used)
                    }
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Error al obtener recursos: {str(e)}"}

    def open_program(self, program_name: str) -> Dict[str, Any]:
        """
        Intenta abrir un programa por nombre.
        Soporta algunos alias comunes. Retorna estructura con success/message.
        """
        try:
            system_name = platform.system()
            program_map = {
                "microsoft edge": "msedge",
                "edge": "msedge",
                "explorador de archivos": "explorer",
                "explorador": "explorer",
                "explorer": "explorer",
                "calculadora": "calc",
                "bloc de notas": "notepad",
                "notepad": "notepad",
                "word": "WINWORD",
                "excel": "excel",
                "powerpoint": "powerpnt",
                "terminal": "cmd" if system_name == "Windows" else "terminal"
            }

            executable = program_map.get(program_name.lower(), program_name)

            if system_name == "Windows":
                # Caso especial: abrir carpeta Descargas si lo pide
                if "explorador" in program_name.lower() and "descargas" in program_name.lower():
                    downloads_path = os.path.expanduser("~\\Downloads")
                    subprocess.run(f"explorer \"{downloads_path}\"", shell=True, check=True)
                    return {"success": True, "message": "Abriendo carpeta Descargas"}
                else:
                    subprocess.run(executable, shell=True, check=True)
                    return {"success": True, "message": f"Abriendo {program_name}"}
        except FileNotFoundError:
            return {"success": False, "message": f"El programa '{program_name}' (ejecutable: '{executable}') no se encontró."}
        except Exception as e:
            return {"success": False, "message": f"Error al abrir programa: {str(e)}"}

    def search_files_smart(self, query: str, search_path: Optional[str] = None, max_results: int = 50) -> Dict[str, Any]:
        """
        Búsqueda inteligente de archivos:
        - Normaliza mayúsculas, acentos, espacios y caracteres especiales
        - Devuelve coincidencias exactas primero, luego parciales
        - Limita la cantidad de resultados
        - Compatible con Windows y Linux
        """
        security = SecurityManager()
        normalized_query = normalize_string(query)

        # Definir rutas de búsqueda
        if search_path:
            abs_path, err = get_absolute_path(search_path)
            if err:
                return {"success": False, "message": err}
            search_paths = [abs_path]
        else:
            if platform.system() == "Windows":
                search_paths = [
                    os.path.expanduser("~\\Desktop"),
                    os.path.expanduser("~\\Documents"),
                    os.path.expanduser("~\\Downloads"),
                    os.path.expanduser("~\\Pictures")
                ]
            else:
                search_paths = [os.path.expanduser("~")]

        exact_matches = []
        partial_matches = []

        for base_path in search_paths:
            if not os.path.exists(base_path):
                continue
            for root, _, files in os.walk(base_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    if not security.is_path_allowed(full_path):
                        continue

                    name_no_ext, _ = os.path.splitext(file)
                    normalized_name = normalize_string(name_no_ext)

                    if normalized_name == normalized_query:
                        exact_matches.append(full_path)
                    elif normalized_query in normalized_name:
                        partial_matches.append(full_path)

                    if len(exact_matches) + len(partial_matches) >= max_results:
                        break
                if len(exact_matches) + len(partial_matches) >= max_results:
                    break

        results = exact_matches + partial_matches
        if results:
            return {
                "success": True,
                "message": f"Encontrados {len(results)} archivos que coinciden con '{query}'",
                "results": results
            }
        else:
            return {
                "success": False,
                "message": f"No se encontraron archivos que coincidan con '{query}'",
                "results": []
            }

    def get_running_processes(self) -> Dict[str, Any]:
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            processes.sort(key=lambda x: x.get('memory_percent') or 0, reverse=True)
            return {"success": True, "message": f"Encontrados {len(processes)} procesos", "processes": processes[:15]}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener procesos: {str(e)}"}

# ----------------- FUNCIONES DE ARCHIVOS -----------------

def rename_file(current_name: str, new_name: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
    current_full_path, error_current = get_absolute_path(current_name, base_dir)
    if error_current:
        return {"success": False, "message": error_current}

    new_full_path, error_new = get_absolute_path(new_name, base_dir)
    if error_new:
        return {"success": False, "message": error_new}

    if not os.path.exists(current_full_path):
        return {"success": False, "message": f"El archivo '{current_name}' no existe en la ruta esperada: '{current_full_path}'."}

    try:
        os.rename(current_full_path, new_full_path)
        return {"success": True, "message": f"Archivo renombrado de '{current_name}' a '{new_name}'."}
    except Exception as e:
        return {"success": False, "message": f"Error al renombrar: {str(e)}"}

def create_folder(folder_name: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
    folder_path, error = get_absolute_path(folder_name, base_dir)
    if error:
        return {"success": False, "message": error}

    if os.path.exists(folder_path):
        return {"success": False, "message": f"La carpeta '{folder_name}' ya existe"}

    try:
        os.makedirs(folder_path, exist_ok=True)
        return {"success": True, "message": f"Carpeta '{folder_name}' creada exitosamente en '{folder_path}'"}
    except Exception as e:
        return {"success": False, "message": f"No se pudo crear la carpeta: {str(e)}"}
    

def convert_image_format(image_path: str, new_format: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convierte una imagen a otro formato usando PIL.
    new_format e.g. 'png', 'jpeg', 'webp'.
    """
    image_full_path, error = get_absolute_path(image_path)
    if error:
        return {"success": False, "message": error}

    if not os.path.exists(image_full_path):
        return {"success": False, "message": f"La imagen '{image_path}' no existe"}

    if Image is None:
        return {"success": False, "message": "Pillow no está instalado (Image es None)"}

    if not output_path:
        name, _ = os.path.splitext(image_path)
        output_path = f"{name}.{new_format.lower()}"

    output_full_path, error = get_absolute_path(output_path)
    if error:
        return {"success": False, "message": error}

    try:
        with Image.open(image_full_path) as img:
            img.save(output_full_path, format=new_format.upper())
        return {"success": True, "message": f"Imagen convertida a {new_format}: {output_path}", "new_file": output_full_path}
    except Exception as e:
        return {"success": False, "message": f"Error en la conversión de imagen: {str(e)}"}

def convert_pdf_to_word_cloudconvert(pdf_path: str, docx_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convierte un archivo PDF a Word usando la API de CloudConvert.
    Requiere CLOUDCONVERT_API_KEY en variables de entorno.
    """
    if cloudconvert is None:
        return {"success": False, "message": "La librería cloudconvert no está instalada."}

    if not CLOUDCONVERT_API_KEY:
        return {"success": False, "message": "La API key de CloudConvert no está configurada."}

    pdf_full_path, error = get_absolute_path(pdf_path)
    if error:
        return {"success": False, "message": error}

    if not os.path.exists(pdf_full_path):
        return {"success": False, "message": f"El archivo PDF '{pdf_path}' no existe"}
    
    if not docx_path:
        name, _ = os.path.splitext(pdf_path)
        docx_path = f"{name}.docx"

    docx_full_path, error = get_absolute_path(docx_path)
    if error:
        return {"success": False, "message": error}

    try:
        cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY)

        job = cloudconvert.Job.create(payload={
            "tasks": {
                'import-file': {
                    'operation': 'import/upload'
                },
                'convert-file': {
                    'operation': 'convert',
                    'input': 'import-file',
                    'output_format': 'docx',
                    'engine': 'ocrmypdf'
                },
                'export-file': {
                    'operation': 'export/url',
                    'input': 'convert-file'
                }
            }
        })

        # subir el archivo al task import-file
        upload_task = None
        for t in job['tasks']:
            if t['name'] == 'import-file' or t['operation'] == 'import/upload':
                upload_task = t
                break
        if not upload_task:
            upload_task = job['tasks'][0]

        cloudconvert.Task.upload(file_name=pdf_full_path, task=upload_task)

        exported_url_task_id = job['tasks'][-1]['id']
        res = cloudconvert.Task.wait(id=exported_url_task_id)

        file_info = res.get("result", {}).get("files", [])[0]
        cloudconvert.download(filename=docx_full_path, url=file_info['url'])

        return {"success": True, "message": f"PDF convertido a Word con CloudConvert: {docx_path}", "new_file": docx_full_path}
    except Exception as e:
        return {"success": False, "message": f"Error en la conversión: {str(e)}"}

def convert_pdf_to_word_local(pdf_path: str, docx_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convierte un PDF a DOCX localmente usando pdf2docx.
    """
    if Converter is None:
        return {"success": False, "message": "pdf2docx no está instalado."}

    pdf_full_path, error = get_absolute_path(pdf_path)
    if error:
        return {"success": False, "message": error}

    if not os.path.exists(pdf_full_path):
        return {"success": False, "message": f"El archivo PDF '{pdf_path}' no existe."}

    if not docx_path:
        name, _ = os.path.splitext(pdf_path)
        docx_path = f"{name}.docx"

    docx_full_path, error = get_absolute_path(docx_path)
    if error:
        return {"success": False, "message": error}

    try:
        cv = Converter(pdf_full_path)
        cv.convert(docx_full_path, start=0, end=None)
        cv.close()
        return {"success": True, "message": f"PDF convertido a Word localmente: {docx_path}", "new_file": docx_full_path}
    except Exception as e:
        return {"success": False, "message": f"Error en la conversión local de PDF a Word: {str(e)}"}

# ----------------- FUNCIONES DE ARCHIVOS NATURALES -----------------

def create_folder(folder_name: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
    folder_path, error = get_absolute_path(folder_name, base_dir)
    if error:
        return {"success": False, "message": error}

    if os.path.exists(folder_path):
        return {"success": False, "message": f"La carpeta '{folder_name}' ya existe"}

    try:
        os.makedirs(folder_path, exist_ok=True)
        return {"success": True, "message": f"Carpeta '{folder_name}' creada exitosamente en '{folder_path}'"}
    except Exception as e:
        return {"success": False, "message": f"No se pudo crear la carpeta: {str(e)}"}

def delete_file(file_name: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
    file_path, error = get_absolute_path(file_name, base_dir)
    if error:
        return {"success": False, "message": error}

    if not os.path.isfile(file_path):
        return {"success": False, "message": f"El archivo '{file_name}' no existe o no es válido"}

    try:
        os.remove(file_path)
        return {"success": True, "message": f"Archivo '{file_name}' eliminado exitosamente"}
    except Exception as e:
        return {"success": False, "message": f"No se pudo eliminar el archivo: {str(e)}"}

def delete_folder(folder_name: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
    folder_path, error = get_absolute_path(folder_name, base_dir)
    if error:
        return {"success": False, "message": error}

    if not os.path.isdir(folder_path):
        return {"success": False, "message": f"La carpeta '{folder_name}' no existe o no es válida"}

    try:
        shutil.rmtree(folder_path)
        return {"success": True, "message": f"Carpeta '{folder_name}' y su contenido eliminados exitosamente"}
    except Exception as e:
        return {"success": False, "message": f"No se pudo eliminar la carpeta: {str(e)}"}

def move_file(file_name: str, dest_folder: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
    source_path, error = get_absolute_path(file_name, base_dir)
    if error:
        return {"success": False, "message": error}

    dest_path, error = get_absolute_path(dest_folder, base_dir)
    if error:
        return {"success": False, "message": error}

    if not os.path.isfile(source_path):
        return {"success": False, "message": f"El archivo '{file_name}' no existe o no es válido"}

    os.makedirs(dest_path, exist_ok=True)
    try:
        dest_file_path = os.path.join(dest_path, os.path.basename(source_path))
        shutil.move(source_path, dest_file_path)
        return {"success": True, "message": f"Archivo '{file_name}' movido a '{dest_path}'"}
    except Exception as e:
        return {"success": False, "message": f"No se pudo mover el archivo: {str(e)}"}

def move_folder(folder_name: str, dest_folder: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
    source_path, error = get_absolute_path(folder_name, base_dir)
    if error:
        return {"success": False, "message": error}

    dest_path, error = get_absolute_path(dest_folder, base_dir)
    if error:
        return {"success": False, "message": error}

    if not os.path.isdir(source_path):
        return {"success": False, "message": f"La carpeta '{folder_name}' no existe o no es válida"}

    os.makedirs(dest_path, exist_ok=True)
    try:
        dest_folder_path = os.path.join(dest_path, os.path.basename(source_path))
        shutil.move(source_path, dest_folder_path)
        return {"success": True, "message": f"Carpeta '{folder_name}' movida a '{dest_path}'"}
    except Exception as e:
        return {"success": False, "message": f"No se pudo mover la carpeta: {str(e)}"}
def rename_folder(current_name: str, new_name: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Renombra una carpeta de forma “natural”.
    current_name: nombre o ruta relativa de la carpeta actual
    new_name: nuevo nombre o ruta relativa de la carpeta
    base_dir: directorio base para rutas relativas (opcional)
    """
    current_path, error = get_absolute_path(current_name, base_dir)
    if error:
        return {"success": False, "message": error}

    new_path, error = get_absolute_path(new_name, base_dir)
    if error:
        return {"success": False, "message": error}

    if not os.path.isdir(current_path):
        return {"success": False, "message": f"La carpeta '{current_name}' no existe o no es válida"}

    try:
        os.makedirs(os.path.dirname(new_path), exist_ok=True)  # asegura que la ruta destino exista
        os.rename(current_path, new_path)
        return {"success": True, "message": f"Carpeta renombrada de '{current_name}' a '{new_name}'"}
    except Exception as e:
        return {"success": False, "message": f"Error al renombrar carpeta: {str(e)}"}


def create_backup(item_name: str, base_dir: Optional[str] = None, backup_dir: str = "backups") -> Dict[str, Any]:
    source_path, error = get_absolute_path(item_name, base_dir)
    if error:
        return {"success": False, "message": error}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if base_dir:
        dest_backup_dir = os.path.join(base_dir, backup_dir)
    else:
        dest_backup_dir = backup_dir

    dest_backup_path, error = get_absolute_path(dest_backup_dir)
    if error:
        return {"success": False, "message": error}

    os.makedirs(dest_backup_path, exist_ok=True)

    if os.path.isfile(source_path):
        name, ext = os.path.splitext(os.path.basename(item_name))
        backup_name = f"{name}_backup_{timestamp}{ext}"
        dest_path = os.path.join(dest_backup_path, backup_name)
        try:
            shutil.copy2(source_path, dest_path)
            return {"success": True, "message": f"Backup del archivo creado: {backup_name}", "backup_path": dest_path}
        except Exception as e:
            return {"success": False, "message": f"No se pudo crear el backup: {str(e)}"}
    elif os.path.isdir(source_path):
        backup_name = f"{os.path.basename(item_name)}_backup_{timestamp}"
        dest_path = os.path.join(dest_backup_path, backup_name)
        try:
            shutil.copytree(source_path, dest_path)
            return {"success": True, "message": f"Backup de la carpeta creado: {backup_name}", "backup_path": dest_path}
        except Exception as e:
            return {"success": False, "message": f"No se pudo crear el backup de la carpeta: {str(e)}"}
    else:
        return {"success": False, "message": f"'{item_name}' no es un archivo ni una carpeta válida"}

def convert_word_to_pdf(word_file: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Convierte .docx a .pdf usando docx2pdf (Windows/MS Office) si está disponible.
    """
    word_path, error = get_absolute_path(word_file, output_dir)
    if error:
        return {"success": False, "message": error}

    if not os.path.exists(word_path):
        return {"success": False, "message": f"El archivo '{word_file}' no existe."}

    if not word_file.lower().endswith(".docx"):
        return {"success": False, "message": "El archivo debe ser un .docx"}

    pdf_file = word_file.replace(".docx", ".pdf")
    pdf_path, error = get_absolute_path(pdf_file, output_dir)
    if error:
        return {"success": False, "message": error}

    if docx2pdf_convert is None:
        return {"success": False, "message": "docx2pdf no está instalado o no está disponible en este entorno."}

    try:
        # docx2pdf.convert puede aceptar (input, output) o solo input
        docx2pdf_convert(word_path, pdf_path)
        return {"success": True, "message": f"Archivo convertido a PDF: {pdf_file}", "new_file": pdf_path}
    except Exception as e:
        return {"success": False, "message": f"Error al convertir Word a PDF: {str(e)}"}

def list_files(directory: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista la estructura de archivos y carpetas de manera recursiva.
    - Si directory no se pasa, lista las carpetas principales del usuario (Escritorio, Documentos, Descargas, Imágenes)
    - Cada carpeta incluye sus archivos y subcarpetas (children)
    """
    security = SecurityManager()

    # Rutas por defecto del sistema
    default_dirs = {
        "Escritorio": os.path.expanduser("~\\Desktop") if platform.system() == "Windows" else os.path.expanduser("~/Desktop"),
        "Documentos": os.path.expanduser("~\\Documents") if platform.system() == "Windows" else os.path.expanduser("~/Documents"),
        "Descargas": os.path.expanduser("~\\Downloads") if platform.system() == "Windows" else os.path.expanduser("~/Downloads"),
        "Imágenes": os.path.expanduser("~\\Pictures") if platform.system() == "Windows" else os.path.expanduser("~/Pictures")
    }

    # Si no se pasa directorio, devolvemos las carpetas principales
    if not directory:
        result = []
        for name, path in default_dirs.items():
            if os.path.exists(path):
                result.append({
                    "name": name,
                    "type": "carpeta_sistema",
                    "path": path,
                    "children": list_files(path)  # recursivo
                })
        return result

    # Convertir a ruta absoluta segura
    directory, error = get_absolute_path(directory)
    if error or not os.path.exists(directory) or not os.path.isdir(directory):
        return []

    items = []
    try:
        for f in sorted(os.listdir(directory)):
            path = os.path.join(directory, f)
            if not security.is_path_allowed(path):
                continue
            if os.path.isdir(path):
                items.append({
                    "name": f,
                    "type": "carpeta",
                    "path": path,
                    "children": list_files(path)  # recursivo
                })
            elif os.path.isfile(path):
                items.append({
                    "name": f,
                    "type": "archivo",
                    "path": path
                })
    except Exception:
        pass

    return items


def search_files(pattern: str, directory: str = "files") -> List[str]:
    """
    Búsqueda no normalizada simple: busca substring en filenames.
    (Esta es una versión simple; para búsqueda más robusta usar search_files_os)
    """
    results = []
    for root, _, files in os.walk(directory):
        for file in files:
            if pattern.lower() in file.lower():
                results.append(os.path.join(root, file))
    return results


# ----------------- INSTANCIAS GLOBALES -----------------
system_manager = SystemManager()

