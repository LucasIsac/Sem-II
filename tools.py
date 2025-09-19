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
from docx2pdf import convert


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
    """Lista todos los archivos y carpetas en un directorio, ordenando carpetas primero."""
    folders = []
    files = []
    
    if not os.path.exists(directory):
        return []

    for f in os.listdir(directory):
        path = os.path.join(directory, f)
        if os.path.isdir(path):
            folders.append({"name": f, "type": "carpeta"})
        elif os.path.isfile(path):
            files.append({"name": f, "type": "archivo"})
    
    # Ordenar alfabéticamente cada lista
    folders.sort(key=lambda x: x['name'])
    files.sort(key=lambda x: x['name'])
    
    # Combinar, carpetas primero
    return folders + files


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

def create_folder(folder_name, base_dir="files"):
    """
    Crea una nueva carpeta dentro del directorio base.
    """
    folder_path = os.path.join(base_dir, folder_name)
    
    if os.path.exists(folder_path):
        return {"success": False, "message": f"La carpeta '{folder_name}' ya existe en {base_dir}"}
    
    try:
        os.makedirs(folder_path)
        return {"success": True, "message": f"Carpeta '{folder_name}' creada exitosamente en {base_dir}"}
    except Exception as e:
        return {"success": False, "message": f"No se pudo crear la carpeta: {str(e)}"}

def delete_file(file_name, base_dir="files"):
    """
    Elimina un archivo dentro del directorio base.
    """
    file_path = os.path.join(base_dir, file_name)
    
    if not os.path.exists(file_path):
        return {"success": False, "message": f"El archivo '{file_name}' no existe en {base_dir}"}
    
    if not os.path.isfile(file_path):
        return {"success": False, "message": f"'{file_name}' no es un archivo válido"}
    
    try:
        os.remove(file_path)
        return {"success": True, "message": f"Archivo '{file_name}' eliminado exitosamente"}
    except Exception as e:
        return {"success": False, "message": f"No se pudo eliminar el archivo: {str(e)}"}

def delete_folder(folder_name, base_dir="files"):
    """
    Elimina una carpeta y todo su contenido dentro del directorio base.
    """
    folder_path = os.path.join(base_dir, folder_name)
    
    if not os.path.exists(folder_path):
        return {"success": False, "message": f"La carpeta '{folder_name}' no existe en {base_dir}"}
    
    if not os.path.isdir(folder_path):
        return {"success": False, "message": f"'{folder_name}' no es una carpeta válida"}
    
    try:
        shutil.rmtree(folder_path)
        return {"success": True, "message": f"Carpeta '{folder_name}' y su contenido eliminados exitosamente"}
    except Exception as e:
        return {"success": False, "message": f"No se pudo eliminar la carpeta: {str(e)}"}

def move_file(file_name, dest_folder, base_dir="files"):
    """
    Mueve un archivo a otra carpeta dentro del directorio base.
    """
    source_path = os.path.join(base_dir, file_name)
    dest_dir = os.path.join(base_dir, dest_folder)

    if not os.path.exists(source_path):
        return {"success": False, "message": f"El archivo '{file_name}' no existe."}
    
    if not os.path.isfile(source_path):
        return {"success": False, "message": f"'{file_name}' no es un archivo válido."}
    
    # Crear carpeta destino si no existe
    os.makedirs(dest_dir, exist_ok=True)

    try:
        shutil.move(source_path, dest_dir)
        return {"success": True, "message": f"Archivo '{file_name}' movido a la carpeta '{dest_folder}'."}
    except Exception as e:
        return {"success": False, "message": f"No se pudo mover el archivo: {str(e)}"}

def move_folder(folder_name, dest_folder, base_dir="files"):
    """
    Mueve una carpeta y todo su contenido a otra carpeta dentro del directorio base.
    """
    source_path = os.path.join(base_dir, folder_name)
    dest_dir = os.path.join(base_dir, dest_folder)

    if not os.path.exists(source_path):
        return {"success": False, "message": f"La carpeta '{folder_name}' no existe."}
    
    if not os.path.isdir(source_path):
        return {"success": False, "message": f"'{folder_name}' no es una carpeta válida."}
    
    # Crear carpeta destino si no existe
    os.makedirs(dest_dir, exist_ok=True)

    try:
        shutil.move(source_path, dest_dir)
        return {"success": True, "message": f"Carpeta '{folder_name}' movida a la carpeta '{dest_folder}'."}
    except Exception as e:
        return {"success": False, "message": f"No se pudo mover la carpeta: {str(e)}"}

def create_backup(item_name, base_dir="files", backup_dir="backups"):
    """
    Crea un backup de un archivo o carpeta dentro de una carpeta de backups.
    Se agrega la fecha y hora al nombre del backup para diferenciarlo.
    """
    source_path = os.path.join(base_dir, item_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_backup_dir = os.path.join(base_dir, backup_dir)
    os.makedirs(dest_backup_dir, exist_ok=True)

    # Determinar nombre del backup
    if os.path.isfile(source_path):
        name, ext = os.path.splitext(item_name)
        backup_name = f"{name}_backup_{timestamp}{ext}"
        dest_path = os.path.join(dest_backup_dir, backup_name)
        try:
            shutil.copy2(source_path, dest_path)  # copia incluyendo metadatos
            return {"success": True, "message": f"Backup del archivo creado: {backup_name}", "backup_path": dest_path}
        except Exception as e:
            return {"success": False, "message": f"No se pudo crear el backup: {str(e)}"}

    elif os.path.isdir(source_path):
        backup_name = f"{item_name}_backup_{timestamp}"
        dest_path = os.path.join(dest_backup_dir, backup_name)
        try:
            shutil.copytree(source_path, dest_path)
            return {"success": True, "message": f"Backup de la carpeta creado: {backup_name}", "backup_path": dest_path}
        except Exception as e:
            return {"success": False, "message": f"No se pudo crear el backup de la carpeta: {str(e)}"}

    else:
        return {"success": False, "message": f"'{item_name}' no es un archivo ni una carpeta válida"}

def convert_word_to_pdf(word_file, output_dir="files"):
    """
    Convierte un archivo Word (.docx) a PDF (.pdf)
    """
    word_path = os.path.join(output_dir, word_file)
    
    if not os.path.exists(word_path):
        return {"success": False, "message": f"El archivo '{word_file}' no existe."}

    if not word_file.lower().endswith(".docx"):
        return {"success": False, "message": "El archivo debe ser un .docx"}

    # Crear el nombre del PDF
    pdf_file = word_file.replace(".docx", ".pdf")
    pdf_path = os.path.join(output_dir, pdf_file)

    try:
        convert(word_path, pdf_path)
        return {"success": True, "message": f"Archivo convertido a PDF: {pdf_file}", "new_file": pdf_path}
    except Exception as e:
        return {"success": False, "message": f"Error al convertir Word a PDF: {str(e)}"}
