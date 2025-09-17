# tools.py - Herramientas para manipulación de archivos
import os
import shutil
from docx import Document
import PyPDF2
from PIL import Image
import glob
from datetime import datetime
from elevenlabs import ElevenLabs
from playsound import playsound
import os
from dotenv import load_dotenv
import requests
import cloudconvert
from dotenv import load_dotenv
from pdf2docx import Converter

# Cargar la API key de CloudConvert
load_dotenv()
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")


def rename_file(current_name, new_name):
    """Renombra un archivo"""
    current_path = os.path.join('files', current_name)
    new_path = os.path.join('files', new_name)
    if not os.path.exists(current_path):
        return {"success": False, "message": f"El archivo '{current_name}' no existe"}
    
    try:
        os.rename(current_path, new_path)
        return {"success": True, "message": f"Archivo renombrado de '{current_name}' a '{new_name}'"}
    except Exception as e:
        return {"success": False, "message": f"Error al renombrar: {str(e)}"}

def rename_folder(current_name, new_name):
    """Renombra una carpeta"""
    current_path = os.path.join('files', current_name)
    new_path = os.path.join('files', new_name)
    if not os.path.exists(current_path):
        return {"success": False, "message": f"La carpeta '{current_name}' no existe"}
    
    try:
        os.rename(current_path, new_path)
        return {"success": True, "message": f"Carpeta renombrada de '{current_name}' a '{new_name}'"}
    except Exception as e:
        return {"success": False, "message": f"Error al renombrar carpeta: {str(e)}"}


def convert_pdf_to_word_cloudconvert(pdf_path, docx_path=None):
    """
    Convierte un archivo PDF a Word usando la API de CloudConvert.
    """
    if not CLOUDCONVERT_API_KEY:
        return {"success": False, "message": "La API key de CloudConvert no está configurada."}

    pdf_full_path = os.path.join('files', pdf_path)
    if not os.path.exists(pdf_full_path):
        return {"success": False, "message": f"El archivo PDF '{pdf_path}' no existe."}

    if not docx_path:
        docx_path = pdf_path.replace('.pdf', '.docx')
    docx_full_path = os.path.join('files', docx_path)

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

        upload_task = job['tasks'][0]
        cloudconvert.Task.upload(file_name=pdf_full_path, task=upload_task)
        
        exported_url_task_id = job['tasks'][2]['id']
        res = cloudconvert.Task.wait(id=exported_url_task_id)

        file_info = res.get("result").get("files")[0]
        cloudconvert.download(filename=docx_full_path, url=file_info['url'])

        return {"success": True, "message": f"PDF convertido a Word con CloudConvert: {docx_path}", "new_file": docx_full_path}
    except Exception as e:
        return {"success": False, "message": f"Error en la conversión con CloudConvert: {str(e)}"}

def convert_image_format(image_path, new_format, output_path=None):
    """Convierte una imagen a otro formato"""
    image_full_path = os.path.join('files', image_path)
    if not os.path.exists(image_full_path):
        return {"success": False, "message": f"La imagen '{image_path}' no existe"}
    
    if not output_path:
        name, _ = os.path.splitext(image_path)
        output_path = f"{name}.{new_format.lower()}"
    output_full_path = os.path.join('files', output_path)
    
    try:
        with Image.open(image_full_path) as img:
            img.save(output_full_path, format=new_format.upper())
        return {"success": True, "message": f"Imagen convertida a {new_format}: {output_path}", "new_file": output_full_path}
    except Exception as e:
        return {"success": False, "message": f"Error en la conversión de imagen: {str(e)}"}

def list_files(directory="files"):
    """Lista todos los archivos en un directorio"""
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def search_files(pattern, directory="files"):
    """Busca archivos que coincidan con un patrón"""
    results = []
    for root, _, files in os.walk(directory):
        for file in files:
            if pattern.lower() in file.lower():
                results.append(os.path.join(root, file))
    return results


def get_datetime():
    """Obtiene la fecha y hora actual"""
    now = datetime.now()
    formatted_date = now.strftime("%A, %d de %B de %Y - %H:%M")
    return {"success": True, "message": f"Son las {formatted_date}"}


def convert_pdf_to_word_local(pdf_path, docx_path=None):
    """
    Convierte un archivo PDF a Word localmente usando pdf2docx. Es una alternativa a la API de CloudConvert.
    """
    pdf_full_path = os.path.join('files', pdf_path)
    if not os.path.exists(pdf_full_path):
        return {"success": False, "message": f"El archivo PDF '{pdf_path}' no existe."}

    if not docx_path:
        docx_path = pdf_path.replace('.pdf', '.docx')
    docx_full_path = os.path.join('files', docx_path)

    try:
        cv = Converter(pdf_full_path)
        cv.convert(docx_full_path, start=0, end=None)
        cv.close()
        return {"success": True, "message": f"PDF convertido a Word localmente: {docx_path}", "new_file": docx_full_path}
    except Exception as e:
        return {"success": False, "message": f"Error en la conversión local de PDF a Word: {str(e)}"}

