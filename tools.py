# tools.py - Herramientas para manipulación de archivos
import os
import shutil
from docx import Document
import PyPDF2
from PIL import Image
import glob
import csv
from datetime import datetime, timedelta
import json
from elevenlabs import ElevenLabs
from playsound import playsound
from dotenv import load_dotenv
import requests
import cloudconvert
from dotenv import load_dotenv
from pdf2docx import Converter
from docx2pdf import convert
from PIL import UnidentifiedImageError
import grpc
import mangle_pb2
import mangle_pb2_grpc
import re
import zipfile
from shutil import make_archive
from PIL import Image

# Cargar la API key de CloudConvert
load_dotenv()
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")
WORKING_DIR = os.getenv("WORKING_DIRECTORY", "./files")  

def rename_file(current_name, new_name):
    """Renombra un archivo con manejo de errores mejorado."""
    try:
        current_path = os.path.join('files', current_name)
        new_path = os.path.join('files', new_name)

        if not os.path.exists(current_path):
            # Sugerencia: Podríamos buscar archivos similares si no se encuentra.
            return f"No pude encontrar el archivo '{current_name}'. Por favor, verifica el nombre e inténtalo de nuevo."
        
        if os.path.isdir(current_path):
            return f"'{current_name}' es una carpeta, no un archivo. Por favor, usa la función para renombrar carpetas."

        os.rename(current_path, new_path)
        return f"¡Listo! El archivo '{current_name}' ha sido renombrado a '{new_name}'."
    except FileNotFoundError:
        return f"Error: El archivo '{current_name}' no fue encontrado. Revisa si el nombre es correcto."
    except PermissionError:
        return f"Error: No tengo permisos para renombrar '{current_name}'. Asegúrate de que el archivo no esté en uso."
    except Exception as e:
        return f"Ocurrió un error inesperado al intentar renombrar el archivo: {str(e)}"

def rename_folder(current_name, new_name):
    """Renombra una carpeta con manejo de errores mejorado."""
    try:
        current_path = os.path.join('files', current_name)
        new_path = os.path.join('files', new_name)

        if not os.path.exists(current_path):
            return f"No pude encontrar la carpeta '{current_name}'. Por favor, verifica el nombre."
        
        if not os.path.isdir(current_path):
            return f"'{current_name}' es un archivo, no una carpeta. Por favor, usa la función para renombrar archivos."

        os.rename(current_path, new_path)
        return f"¡Perfecto! La carpeta '{current_name}' ahora se llama '{new_name}'."
    except FileNotFoundError:
        return f"Error: La carpeta '{current_name}' no fue encontrada."
    except PermissionError:
        return f"Error: No tengo permisos para renombrar la carpeta '{current_name}'."
    except Exception as e:
        return f"Ocurrió un error inesperado al intentar renombrar la carpeta: {str(e)}"

def convert_pdf_to_word_cloudconvert(pdf_path, docx_path=None):
    """Convierte un PDF a Word usando CloudConvert con manejo de errores mejorado."""
    try:
        if not CLOUDCONVERT_API_KEY or CLOUDCONVERT_API_KEY == "tu_api_key":
            return "Error de configuración: La API key de CloudConvert no está configurada en el archivo .env."

        pdf_full_path = os.path.join('files', pdf_path)
        if not os.path.exists(pdf_full_path):
            return f"No se pudo convertir: el archivo PDF '{pdf_path}' no existe."

        if not docx_path:
            docx_path = os.path.splitext(pdf_path)[0] + '.docx'
        docx_full_path = os.path.join('files', docx_path)

        cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY)
        job = cloudconvert.Job.create(payload={
            "tasks": {
                'import-file': {'operation': 'import/upload'},
                'convert-file': {
                    'operation': 'convert',
                    'input': 'import-file',
                    'output_format': 'docx',
                    'engine': 'ocrmypdf'
                },
                'export-file': {'operation': 'export/url', 'input': 'convert-file'}
            }
        })

        upload_task = job['tasks'][0]
        cloudconvert.Task.upload(file_name=pdf_full_path, task=upload_task)
        
        exported_url_task_id = job['tasks'][2]['id']
        res = cloudconvert.Task.wait(id=exported_url_task_id)

        file_info = res.get("result").get("files")[0]
        cloudconvert.download(filename=docx_full_path, url=file_info['url'])

        return f"El archivo '{pdf_path}' ha sido convertido a Word usando CloudConvert y guardado como '{docx_path}'."
    except cloudconvert.exceptions.APIError as e:
        return f"Error de la API de CloudConvert: {str(e)}"
    except Exception as e:
        return f"Ocurrió un error inesperado durante la conversión con CloudConvert: {str(e)}"

def convert_image_format(image_path, new_format, output_path=None):
    """Convierte una imagen a otro formato con manejo de errores mejorado."""
    try:
        image_full_path = os.path.join('files', image_path)
        if not os.path.exists(image_full_path):
            return f"No se pudo convertir: la imagen '{image_path}' no existe."

        if not output_path:
            name, _ = os.path.splitext(image_path)
            output_path = f"{name}.{new_format.lower()}"
        output_full_path = os.path.join('files', output_path)
        
        with Image.open(image_full_path) as img:
            # Algunos formatos como JPG no soportan transparencia, así que convertimos a RGB.
            if new_format.lower() in ['jpeg', 'jpg']:
                img = img.convert('RGB')
            img.save(output_full_path, format=new_format.upper())
        return f"La imagen '{image_path}' se ha convertido a {new_format.upper()} y guardado como '{output_path}'."
    except FileNotFoundError:
        return f"Error: No se encontró el archivo de imagen '{image_path}'."
    except UnidentifiedImageError:
        return f"Error: El archivo '{image_path}' no parece ser una imagen válida."
    except ValueError as e:
        return f"Error: El formato '{new_format}' no es válido para guardar. ({str(e)})"
    except Exception as e:
        return f"Ocurrió un error inesperado al convertir la imagen: {str(e)}"

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
    """Convierte un PDF a Word localmente con manejo de errores mejorado."""
    try:
        pdf_full_path = os.path.join('files', pdf_path)
        if not os.path.exists(pdf_full_path):
            return f"No se pudo convertir: el archivo PDF '{pdf_path}' no existe."

        if not pdf_path.lower().endswith(".pdf"):
            return f"El archivo '{pdf_path}' no parece ser un documento PDF."

        if not docx_path:
            docx_path = os.path.splitext(pdf_path)[0] + '.docx'
        docx_full_path = os.path.join('files', docx_path)

        cv = Converter(pdf_full_path)
        cv.convert(docx_full_path, start=0, end=None)
        cv.close()
        return f"El archivo '{pdf_path}' se ha convertido a Word localmente como '{docx_path}'."
    except FileNotFoundError:
        return f"Error: No se encontró el archivo PDF '{pdf_path}'."
    except Exception as e:
        return f"Ocurrió un error durante la conversión local de PDF a Word: {str(e)}"

def create_folder(folder_name, base_dir="files"):
    """Crea una nueva carpeta con manejo de errores mejorado."""
    try:
        folder_path = os.path.join(base_dir, folder_name)
        
        if os.path.exists(folder_path):
            return f"No se pudo crear: la carpeta '{folder_name}' ya existe."
        
        os.makedirs(folder_path)
        return f"La carpeta '{folder_name}' ha sido creada con éxito."
    except PermissionError:
        return f"Error: No tengo permisos para crear la carpeta en '{base_dir}'."
    except FileExistsError:
         return f"Error: Ya existe un archivo con el nombre '{folder_name}' en esta ubicación, por lo que no se puede crear una carpeta con el mismo nombre."
    except Exception as e:
        return f"Ocurrió un error inesperado al crear la carpeta: {str(e)}"

def delete_file(file_name, base_dir="files"):
    """Elimina un archivo con manejo de errores mejorado."""
    try:
        file_path = os.path.join(base_dir, file_name)
        
        if not os.path.exists(file_path):
            return f"No se pudo eliminar: el archivo '{file_name}' no existe."
        
        if not os.path.isfile(file_path):
            return f"'{file_name}' es una carpeta, no un archivo. No se puede eliminar con esta función."
        
        os.remove(file_path)
        return f"El archivo '{file_name}' ha sido eliminado correctamente."
    except FileNotFoundError:
        return f"Error: El archivo '{file_name}' no fue encontrado al intentar eliminarlo."
    except PermissionError:
        return f"Error: No tengo permisos para eliminar '{file_name}'. Asegúrate de que no esté protegido o en uso."
    except Exception as e:
        return f"Ocurrió un error inesperado al eliminar el archivo: {str(e)}"

def delete_folder(folder_name, base_dir="files"):
    """Elimina una carpeta y todo su contenido con manejo de errores mejorado."""
    try:
        folder_path = os.path.join(base_dir, folder_name)
        
        if not os.path.exists(folder_path):
            return f"No se pudo eliminar: la carpeta '{folder_name}' no existe."
        
        if not os.path.isdir(folder_path):
            return f"'{folder_name}' es un archivo, no una carpeta. No se puede eliminar con esta función."
        
        shutil.rmtree(folder_path)
        return f"La carpeta '{folder_name}' y todo su contenido han sido eliminados."
    except FileNotFoundError:
        return f"Error: La carpeta '{folder_name}' no fue encontrada al intentar eliminarla."
    except PermissionError:
        return f"Error: No tengo permisos para eliminar la carpeta '{folder_name}'. Revisa si algún archivo dentro está en uso."
    except OSError as e:
        return f"Error del sistema al eliminar la carpeta: {str(e)}. Es posible que la carpeta no esté vacía."
    except Exception as e:
        return f"Ocurrió un error inesperado al eliminar la carpeta: {str(e)}"

def move_file(file_name, dest_folder, base_dir="files"):
    """
    Mueve un archivo a otra carpeta. Esta función es inteligente: si el archivo no se encuentra
    en la ruta especificada, lo buscará en todas las subcarpetas.
    """
    try:
        dest_dir = os.path.join(base_dir, dest_folder)
        source_path = os.path.join(base_dir, file_name)

        # Si la ruta proporcionada no existe, buscar el archivo en todo el directorio base.
        if not os.path.exists(source_path):
            found_files = []
            # os.path.basename para buscar solo por el nombre del archivo
            target_filename = os.path.basename(file_name)
            for root, _, files in os.walk(base_dir):
                if target_filename in files:
                    # Construir la ruta completa del archivo encontrado
                    found_files.append(os.path.join(root, target_filename))
            
            if len(found_files) == 0:
                return f"No se pudo mover: el archivo '{target_filename}' no se encontró en ninguna carpeta."
            if len(found_files) > 1:
                return f"Conflicto: Se encontraron varios archivos llamados '{target_filename}'. Por favor, especifica la ruta completa."
            
            # Si se encontró un único archivo, esa es nuestra nueva ruta de origen.
            source_path = found_files[0]

        if not os.path.isfile(source_path):
            return f"La ruta de origen '{file_name}' es una carpeta, no un archivo. Usa la función para mover carpetas."
        
        # Crear carpeta destino si no existe
        os.makedirs(dest_dir, exist_ok=True)

        # Usar el nombre base del archivo para el destino final
        final_dest_path = os.path.join(dest_dir, os.path.basename(source_path))

        shutil.move(source_path, final_dest_path)
        
        # Obtener la ruta relativa para el mensaje de éxito
        relative_source = os.path.relpath(source_path, base_dir)
        return f"El archivo '{relative_source}' se ha movido correctamente a la carpeta '{dest_folder}'."

    except PermissionError:
        return f"Error: No tengo permisos para mover el archivo '{file_name}'."
    except shutil.Error as e:
        return f"Error al mover el archivo: {str(e)}. Es posible que un archivo con el mismo nombre ya exista en el destino."
    except Exception as e:
        return f"Ocurrió un error inesperado al mover el archivo: {str(e)}"

def move_folder(folder_name, dest_folder, base_dir="files"):
    """Mueve una carpeta y todo su contenido a otra carpeta con manejo de errores mejorado."""
    try:
        source_path = os.path.join(base_dir, folder_name)
        dest_dir = os.path.join(base_dir, dest_folder)

        if not os.path.exists(source_path):
            return f"No se pudo mover: la carpeta de origen '{folder_name}' no existe."
        
        if not os.path.isdir(source_path):
            return f"La ruta de origen '{folder_name}' es un archivo, no una carpeta. Usa la función para mover archivos."
        
        # Crear carpeta destino si no existe
        os.makedirs(dest_dir, exist_ok=True)

        shutil.move(source_path, dest_dir)
        return f"La carpeta '{folder_name}' se ha movido correctamente a '{dest_folder}'."
    except FileNotFoundError:
        return f"Error: No se encontró la carpeta de origen o destino al intentar mover '{folder_name}'."
    except PermissionError:
        return f"Error: No tengo permisos para mover la carpeta '{folder_name}'."
    except shutil.Error as e:
        return f"Error al mover la carpeta: {str(e)}. Es posible que una carpeta con el mismo nombre ya exista en el destino."
    except Exception as e:
        return f"Ocurrió un error inesperado al mover la carpeta: {str(e)}"

def create_backup(item_name, base_dir="files", backup_dir="backups"):
    """Crea un backup de un archivo o carpeta con manejo de errores mejorado."""
    try:
        source_path = os.path.join(base_dir, item_name)
        
        if not os.path.exists(source_path):
            return f"No se pudo crear el backup: el archivo o carpeta '{item_name}' no existe."

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_backup_dir = os.path.join(base_dir, backup_dir)
        os.makedirs(dest_backup_dir, exist_ok=True)

        if os.path.isfile(source_path):
            name, ext = os.path.splitext(item_name)
            backup_name = f"{name}_backup_{timestamp}{ext}"
            dest_path = os.path.join(dest_backup_dir, backup_name)
            shutil.copy2(source_path, dest_path)
            return f"Backup del archivo '{item_name}' creado con éxito como '{backup_name}'."

        elif os.path.isdir(source_path):
            backup_name = f"{item_name}_backup_{timestamp}"
            dest_path = os.path.join(dest_backup_dir, backup_name)
            shutil.copytree(source_path, dest_path)
            return f"Backup de la carpeta '{item_name}' creado con éxito como '{backup_name}'."
        else:
            return f"'{item_name}' no es un archivo ni una carpeta válida, así que no puedo crear un backup."
            
    except PermissionError:
        return f"Error de permisos: no pude crear el backup de '{item_name}'."
    except shutil.Error as e:
        return f"Error al crear el backup: {str(e)}."
    except Exception as e:
        return f"Ocurrió un error inesperado al crear el backup: {str(e)}"

def convert_word_to_pdf(word_file, output_dir="files"):
    """Convierte un archivo Word (.docx) a PDF (.pdf) con manejo de errores mejorado."""
    try:
        word_path = os.path.join(output_dir, word_file)
        
        if not os.path.exists(word_path):
            return f"No se pudo convertir: el archivo '{word_file}' no existe."

        if not word_file.lower().endswith(".docx"):
            return f"El archivo '{word_file}' no es un documento de Word (.docx)."

        pdf_file = os.path.splitext(word_file)[0] + ".pdf"
        pdf_path = os.path.join(output_dir, pdf_file)

        convert(word_path, pdf_path)
        return f"El archivo '{word_file}' ha sido convertido a PDF exitosamente como '{pdf_file}'."
    except FileNotFoundError:
        return f"Error: No se encontró el archivo '{word_file}'."
    except Exception as e:
        # Esto puede ocurrir si Word no está instalado o hay problemas con COM en Windows.
        return f"Ocurrió un error inesperado al convertir de Word a PDF: {str(e)}"





# nuevas funciones para leer, resumir y buscar en archivos de texto, PDF y DOCX
def read_file_content(file_path):
    """Lee el contenido de un archivo de texto o código (.txt, .md, .py)."""
    full_path = os.path.join('files', file_path)
    if not os.path.exists(full_path):
        return f"No se encontró el archivo '{file_path}'."
    
    try:
        if full_path.lower().endswith(('.txt', '.md', '.py', '.csv')):
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif full_path.lower().endswith('.docx'):
            doc = Document(full_path)
            return "\n".join([p.text for p in doc.paragraphs])
        elif full_path.lower().endswith('.pdf'):
            content = []
            with open(full_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    content.append(page.extract_text() or "")
            return "\n".join(content)
        else:
            return f"El formato de archivo '{file_path}' no es compatible para lectura."
    except Exception as e:
        return f"Ocurrió un error al leer '{file_path}': {str(e)}"

def search_in_file(file_path, query):
    """Busca una palabra o frase en un archivo y devuelve las líneas donde aparece."""
    try:
        content = read_file_content(file_path)
        if content.startswith("No se encontró") or content.startswith("Ocurrió un error"):
            return content

        results = []
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if query.lower() in line.lower():
                results.append(f"Línea {i}: {line.strip()}")

        if not results:
            return f"No se encontró '{query}' en '{file_path}'."
        
        # Devolvemos las líneas crudas para que la IA las resuma
        return results

    except Exception as e:
        return f"Ocurrió un error al buscar en '{file_path}': {str(e)}"

def create_zip_archive(source_list: str, zip_path: str = None, base_dir=WORKING_DIR):
    """
    Comprime archivos o carpetas específicas dentro del directorio de trabajo.
    
    - source_list: string con rutas relativas separadas por coma. Ej: "pruebas/archivo1.txt, pruebas/archivo2.pdf"
    - zip_path: ruta de destino del archivo .zip (ej: "backups/mis_archivos.zip").
    """
    try:
        items = [s.strip() for s in source_list.split(",")]

        # Si no se proporciona un nombre para el zip, se devuelve un error claro.
        if not zip_path or zip_path.isspace():
            return "Error: Debes proporcionar un nombre para el archivo ZIP."

        # Si el nombre del zip no termina en .zip, se añade la extensión.
        if not zip_path.endswith(".zip"):
            zip_path += ".zip"

        zip_full_path = os.path.join(base_dir, zip_path)

        # Si el archivo ya existe, se informa al usuario en lugar de crear copias.
        if os.path.exists(zip_full_path):
            return f"Error: El archivo '{zip_path}' ya existe. Por favor, elige otro nombre."

        # Asegurarse de que el directorio de destino exista.
        os.makedirs(os.path.dirname(zip_full_path), exist_ok=True)

        # Crear el ZIP
        with zipfile.ZipFile(zip_full_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for item in items:
                path = os.path.join(base_dir, item)
                if not os.path.exists(path):
                    return f"No se encontró '{item}' en {base_dir}."

                if os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for file in files:
                            full = os.path.join(root, file)
                            arcname = os.path.relpath(full, os.path.dirname(path))  
                            zf.write(full, arcname)
                else:
                    arcname = os.path.basename(path)  # Solo nombre del archivo
                    zf.write(path, arcname)

        return f"Archivo ZIP '{zip_path}' creado con éxito."

    except Exception as e:
        return f"Ocurrió un error al crear ZIP: {str(e)}"

def extract_zip_archive(zip_path: str, destination_folder: str, base_dir=WORKING_DIR):
    """
    Extrae un archivo ZIP dentro del directorio de trabajo.
    - zip_path: nombre del .zip
    - destination_folder: carpeta destino donde se extraen los contenidos
    """
    try:
        full_zip = os.path.join(base_dir, zip_path)
        dest = os.path.join(base_dir, destination_folder)
        if not os.path.exists(full_zip):
            return f"No se encontró el archivo ZIP '{zip_path}'."
        if not zipfile.is_zipfile(full_zip):
            return f"'{zip_path}' no es un archivo ZIP válido."
        os.makedirs(dest, exist_ok=True)
        with zipfile.ZipFile(full_zip, 'r') as zf:
            zf.extractall(path=dest)
        return f"Contenido de '{zip_path}' extraído correctamente en carpeta '{destination_folder}'."
    except Exception as e:
        return f"Ocurrió un error al extraer ZIP: {str(e)}"

def get_file_structure(directory):
    """
    Genera un string que representa la estructura de archivos y carpetas
    de un directorio de forma recursiva para dar contexto al LLM.
    """
    tree = []
    for root, dirs, files in os.walk(directory):
        # No incluir el directorio base en el path relativo
        if root == directory:
            relative_path = ""
        else:
            relative_path = os.path.relpath(root, directory)
        
        # Ignorar carpetas de backup para no ensuciar el contexto
        if "backups" in relative_path.split(os.sep):
            continue

        level = relative_path.count(os.sep)
        indent = "    " * level
        
        # Añadir la carpeta actual al árbol
        if relative_path:
            tree.append(f"{indent}📁 {os.path.basename(root)}/")
        
        # Añadir los archivos de la carpeta actual
        sub_indent = "    " * (level + 1)
        for f in sorted(files):
            tree.append(f"{sub_indent}📄 {f}")
            
    return "\n".join(tree)

def move_files_batch(source_folder: str, dest_folder: str, pattern: str = "*"):
    """
    Mueve archivos de una carpeta a otra según un patrón.
    
    - source_folder: carpeta origen relativa a WORKING_DIR
    - dest_folder: carpeta destino relativa a WORKING_DIR
    - pattern: patrón para filtrar archivos (ej: "*.pdf", "IMG_*")
    """
    base_dir = WORKING_DIR
    src_path = os.path.join(base_dir, source_folder)
    dst_path = os.path.join(base_dir, dest_folder)
    os.makedirs(dst_path, exist_ok=True)

    files = glob.glob(os.path.join(src_path, pattern))
    if not files:
        return f"No se encontraron archivos en {src_path} que coincidan con {pattern}"

    for f in files:
        shutil.move(f, dst_path)

    return f"Movidos {len(files)} archivos de {source_folder} a {dest_folder}"

def rename_files_batch(folder: str, pattern: str, prefix: str = "", suffix: str = ""):
    """
    Renombra archivos en lote según patrón, agregando prefijo o sufijo.
    
    - folder: carpeta relativa a WORKING_DIR
    - pattern: patrón de archivos a renombrar (ej: "IMG_*")
    - prefix: texto a agregar al inicio del nombre
    - suffix: texto a agregar al final del nombre antes de la extensión
    """
    base_dir = WORKING_DIR
    path = os.path.join(base_dir, folder)
    files = glob.glob(os.path.join(path, pattern))

    if not files:
        return f"No se encontraron archivos en {folder} que coincidan con {pattern}"

    for f in files:
        dir_name, file_name = os.path.split(f)
        name, ext = os.path.splitext(file_name)
        new_name = f"{prefix}{name}{suffix}{ext}"
        new_path = os.path.join(dir_name, new_name)
        os.rename(f, new_path)

    return f"Renombrados {len(files)} archivos en {folder}"

def convert_images_batch(folder: str, source_ext: str = ".jpg", target_ext: str = ".png"):

    """
    Convierte imágenes en lote de un formato a otro.
    
    - folder: carpeta relativa a WORKING_DIR
    - source_ext: extensión de origen (ej: ".jpg")
    - target_ext: extensión de destino (ej: ".png")
    """
    base_dir = WORKING_DIR
    path = os.path.join(base_dir, folder)
    files = glob.glob(os.path.join(path, f"*{source_ext}"))

    if not files:
        return f"No se encontraron archivos {source_ext} en {folder}"

    for f in files:
        img = Image.open(f)
        new_name = os.path.splitext(f)[0] + target_ext
        img.save(new_name)

    return f"Convertidas {len(files)} imágenes de {source_ext} a {target_ext} en {folder}"



# Funciones para interactuar con Mangle a través de gRPC


def consultar_base_de_conocimiento(query: str):
    """
    Se conecta al servicio de Mangle, envía una consulta y devuelve los resultados procesados.
    """
    try:
        with grpc.insecure_channel('localhost:8080') as channel:
            stub = mangle_pb2_grpc.MangleStub(channel)
            response = stub.Query(mangle_pb2.QueryRequest(query=query))
            
            resultados = []
            
            for result in response:
                # result.answer contiene la respuesta completa, ej: 'horas_semanales("Lucas", "Proyecto_Gamma", 20)'
                answer = result.answer.strip()
                
                # Intentar extraer información de diferentes tipos de respuestas
                if "(" in answer and ")" in answer:
                    # Extraer el contenido dentro de los paréntesis
                    start = answer.find("(") + 1
                    end = answer.rfind(")")
                    contenido = answer[start:end]
                    
                    # Dividir por comas y limpiar cada parte
                    partes = []
                    for parte in contenido.split(","):
                        parte = parte.strip()
                        # Quitar comillas si las tiene
                        if parte.startswith('"') and parte.endswith('"'):
                            parte = parte[1:-1]
                        partes.append(parte)
                    
                    # Formatear según el tipo de consulta
                    if len(partes) >= 3 and any(keyword in query for keyword in ["horas_semanales", "progreso_proyecto", "presupuesto"]):
                        # Para consultas con 3 parámetros como horas_semanales(Persona, Proyecto, Horas)
                        if len(partes) == 3:
                            resultados.append(f"{partes[0]} en {partes[1]}: {partes[2]}")
                        else:
                            resultados.append(" - ".join(partes))
                    elif len(partes) == 2:
                        # Para consultas con 2 parámetros como contacto(Persona, Email)
                        resultados.append(f"{partes[0]} ({partes[1]})")
                    elif len(partes) == 1:
                        # Para consultas simples
                        resultados.append(partes[0])
                    else:
                        # Formato genérico
                        resultados.append(" - ".join(partes))
                else:
                    # Si no tiene paréntesis, usar el patrón original
                    pattern = re.compile(r'\"(.*?)\"')
                    matches = pattern.findall(answer)
                    if matches:
                        resultados.extend(matches)
                    else:
                        # Como último recurso, agregar la respuesta completa
                        resultados.append(answer)
            
            if not resultados:
                return "No se encontraron resultados para la consulta."

            return f"Resultados de la consulta: {', '.join(resultados)}"

    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            return "Error: No se pudo conectar al servicio de Mangle. ¿Está el servidor en funcionamiento?"
        return f"Ocurrió un error de gRPC: {e.details()}"
    except Exception as e:
        return f"Ocurrió un error inesperado al consultar la base de conocimiento: {str(e)}"

def actualizar_base_de_conocimiento_grpc(program: str):
    """Se comunica con el servidor gRPC de Mangle para actualizar la base de conocimiento."""
    with grpc.insecure_channel("localhost:8080") as channel:
        stub = mangle_pb2_grpc.MangleStub(channel)
        req = mangle_pb2.UpdateRequest(program=program)
        response = stub.Update(req)
        return response.updated_predicates

def limpiar_base_de_conocimiento():
    """
    Limpia por completo la base de conocimiento de Mangle.
    """
    try:
        print("Limpiando la base de conocimiento de Mangle...")
        respuesta = actualizar_base_de_conocimiento_grpc("")
        return "La base de conocimiento de Mangle ha sido limpiada con éxito."
    except Exception as e:
        return f"Ocurrió un error al limpiar la base de conocimiento: {str(e)}"

def cargar_conocimiento_desde_archivo(file_path: str):
    """
    Carga un programa de Mangle desde un archivo .mgl y lo utiliza
    para actualizar la base de conocimiento.
    """
    try:
        # Se construye la ruta completa asumiendo que el archivo está en el directorio de trabajo 'files'
        full_path = os.path.join(WORKING_DIR, file_path)

        if not os.path.exists(full_path):
            return f"Error: No se pudo encontrar el archivo '{file_path}'."

        with open(full_path, 'r', encoding='utf-8') as f:
            programa_mangle = f.read()
        
        print(f"Cargando conocimiento desde '{full_path}'...")
        actualizar_base_de_conocimiento_grpc(programa_mangle)
        return f"El conocimiento del archivo '{file_path}' ha sido cargado exitosamente."

    except Exception as e:
        return f"Ocurrió un error al cargar el archivo de conocimiento: {str(e)}"

def normalizar_nombre_para_mangle(nombre: str) -> str:
    """
    Normaliza un nombre para usarlo como átomo en Mangle.
    Mantiene el formato legible pero válido para Mangle.
    """
    # Solo reemplazamos espacios por guiones bajos, mantenemos mayúsculas
    return nombre.replace(" ", "_")

def cargar_todos_los_contactos_desde_archivo(file_path: str = "contactos.txt"):
    """
    Carga TODOS los contactos desde el archivo usando el esquema unificado.
    IMPORTANTE: Esto reemplaza todos los contactos en la base de conocimiento.
    """
    try:
        full_path = os.path.join('files', file_path)
        if not os.path.exists(full_path):
            return f"Error: No se pudo encontrar el archivo '{file_path}'."

        hechos = []
        contactos_cargados = 0
        
        with open(full_path, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if linea and ',' in linea:
                    partes = [p.strip() for p in linea.split(',')]
                    if len(partes) >= 4:
                        nombre, puesto, email, proyecto = partes[:4]
                        nombre_mangle = normalizar_nombre_para_mangle(nombre)
                        
                        # Usar el esquema de tu archivo .mgl existente
                        hechos.extend([
                            f'contacto("{nombre_mangle}", "{email}").',
                            f'puesto("{nombre_mangle}", "{puesto}").',
                            f'trabaja_en("{nombre_mangle}", "{proyecto}").'
                        ])
                        contactos_cargados += 1

        if not hechos:
            return "No se encontraron contactos válidos en el archivo."

        # Cargar todo el programa
        programa_mangle = "\n".join(hechos)
        print(f"Cargando {contactos_cargados} contactos a Mangle...")
        actualizar_base_de_conocimiento_grpc(programa_mangle)
        
        return f"Se cargaron {contactos_cargados} contactos desde '{file_path}' usando el esquema unificado."

    except Exception as e:
        return f"Error al cargar contactos: {str(e)}"

def agregar_contacto(input_data, archivo_default="contactos.txt"):
    """
    Agrega UN contacto al archivo y a la base de conocimiento usando el esquema unificado.
    """
    if not isinstance(input_data, str):
        return "Error: El formato de entrada debe ser un string."

    partes = [x.strip() for x in input_data.split(",")]
    
    if len(partes) < 4:
        return "Error: Faltan datos. El formato debe ser 'nombre, puesto, email, proyecto[, archivo]'."

    nombre, puesto, email, proyecto = partes[:4]
    archivo = partes[4] if len(partes) > 4 else archivo_default
    
    try:
        # Paso 1: Agregar al archivo de texto
        full_path = os.path.join("files", archivo)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'a', encoding='utf-8') as f:
            f.write(f"{nombre},{puesto},{email},{proyecto}\n")

        # Paso 2: Agregar a la base de conocimiento usando el esquema unificado
        nombre_mangle = normalizar_nombre_para_mangle(nombre)
        
        hechos = [
            f'contacto("{nombre_mangle}", "{email}").',
            f'puesto("{nombre_mangle}", "{puesto}").',
            f'trabaja_en("{nombre_mangle}", "{proyecto}").'
        ]
        
        programa_mangle = "\n".join(hechos)
        actualizar_base_de_conocimiento_grpc(programa_mangle)
        
        return f"Contacto '{nombre}' agregado exitosamente al archivo y base de conocimiento."

    except Exception as e:
        return f"Error al agregar contacto '{nombre}': {str(e)}"

def inicializar_base_conocimiento_completa():
    """
    Función de utilidad para inicializar completamente la base de conocimiento.
    1. Carga el archivo .mgl base
    2. Carga todos los contactos del archivo
    """
    try:
        resultado1 = cargar_conocimiento_desde_archivo("conocimiento.mangle")
        resultado2 = cargar_todos_los_contactos_desde_archivo("contactos.txt")
        
        return f"Inicialización completa:\n{resultado1}\n{resultado2}"
    
    except Exception as e:
        return f"Error durante la inicialización: {str(e)}"

# Funciones de consulta de ejemplo
def buscar_contactos_por_proyecto(proyecto: str):
    """Busca contactos que trabajen en un proyecto específico"""
    query = f'trabaja_en(Persona, "{proyecto}").'
    return consultar_base_de_conocimiento(query)

def buscar_contactos_prioritarios():
    """Busca contactos prioritarios usando la regla definida"""
    query = 'contacto_prioritario(Persona).'
    return consultar_base_de_conocimiento(query)

def listar_todos_los_proyectos():
    """Lista todos los proyectos únicos"""
    query = 'trabaja_en(_, Proyecto).'
    return consultar_base_de_conocimiento(query)


# Funciones avanzadas para tu sistema Mangle

def agregar_metricas_proyecto(input_data):
    """
    Agrega métricas y configuración a un proyecto.
    Formato: 'proyecto, estado, fecha_inicio, fecha_fin, presupuesto, prioridad, horas_estimadas'
    """
    try:
        partes = [x.strip() for x in input_data.split(",")]
        
        if len(partes) < 7:
            return "Error: Formato requerido: 'proyecto, estado, fecha_inicio, fecha_fin, presupuesto, prioridad, horas_estimadas'"
        
        proyecto, estado, fecha_inicio, fecha_fin, presupuesto, prioridad, horas_estimadas = partes
        
        # Normalizar nombre del proyecto
        proyecto_mangle = proyecto.replace(" ", "_")
        
        hechos = [
            f'proyecto("{proyecto_mangle}").',
            f'estado_proyecto("{proyecto_mangle}", "{estado}").',
            f'fecha_inicio_proyecto("{proyecto_mangle}", "{fecha_inicio}").',
            f'fecha_fin_proyecto("{proyecto_mangle}", "{fecha_fin}").',
            f'presupuesto_proyecto("{proyecto_mangle}", {presupuesto}).',
            f'prioridad_proyecto("{proyecto_mangle}", "{prioridad}").',
            f'horas_estimadas_proyecto("{proyecto_mangle}", {horas_estimadas}).'
        ]
        
        programa = "\n".join(hechos)
        actualizar_base_de_conocimiento_grpc(programa)
        
        return f"Métricas del proyecto '{proyecto}' agregadas exitosamente."
    
    except Exception as e:
        return f"Error al agregar métricas del proyecto: {str(e)}"

def asignar_horas_persona_proyecto(input_data):
    """
    Asigna horas trabajadas por una persona en un proyecto específico.
    Formato: 'persona, proyecto, horas_semanales, porcentaje_dedicacion, rol_en_proyecto'
    """
    try:
        partes = [x.strip() for x in input_data.split(",")]
        
        if len(partes) < 5:
            return "Error: Formato: 'persona, proyecto, horas_semanales, porcentaje_dedicacion, rol_en_proyecto'"
        
        persona, proyecto, horas_semanales, porcentaje, rol = partes
        
        # Normalizar nombres
        persona_mangle = persona.replace(" ", "_")
        proyecto_mangle = proyecto.replace(" ", "_")
        
        hechos = [
            f'asignacion("{persona_mangle}", "{proyecto_mangle}").',
            f'horas_semanales("{persona_mangle}", "{proyecto_mangle}", {horas_semanales}).',
            f'porcentaje_dedicacion("{persona_mangle}", "{proyecto_mangle}", {porcentaje}).',
            f'rol_en_proyecto("{persona_mangle}", "{proyecto_mangle}", "{rol}").'
        ]
        
        programa = "\n".join(hechos)
        actualizar_base_de_conocimiento_grpc(programa)
        
        return f"Asignación de {persona} al proyecto {proyecto} registrada exitosamente."
    
    except Exception as e:
        return f"Error al asignar horas: {str(e)}"

def registrar_progreso_proyecto(input_data):
    """
    Registra el progreso actual de un proyecto.
    Formato: 'proyecto, porcentaje_completado, horas_trabajadas, fecha_reporte'
    """
    try:
        partes = [x.strip() for x in input_data.split(",")]
        
        if len(partes) < 3:
            return "Error: Formato: 'proyecto, porcentaje_completado, horas_trabajadas[, fecha_reporte]'"
        
        proyecto = partes[0]
        porcentaje = partes[1]
        horas_trabajadas = partes[2]
        fecha = partes[3] if len(partes) > 3 else datetime.now().strftime('%Y-%m-%d')
        
        proyecto_mangle = proyecto.replace(" ", "_")
        
        hechos = [
            f'progreso_proyecto("{proyecto_mangle}", {porcentaje}, "{fecha}").',
            f'horas_trabajadas_total("{proyecto_mangle}", {horas_trabajadas}, "{fecha}").'
        ]
        
        programa = "\n".join(hechos)
        actualizar_base_de_conocimiento_grpc(programa)
        
        return f"Progreso del proyecto '{proyecto}' actualizado: {porcentaje}% completado."
    
    except Exception as e:
        return f"Error al registrar progreso: {str(e)}"

def calcular_metricas_proyecto(proyecto):
    """
    Calcula métricas completas de un proyecto específico.
    """
    try:
        proyecto_mangle = proyecto.replace(" ", "_")
        
        queries = {
            'estado': f'estado_proyecto("{proyecto_mangle}", Estado).',
            'presupuesto': f'presupuesto_proyecto("{proyecto_mangle}", Presupuesto).',
            'horas_estimadas': f'horas_estimadas_proyecto("{proyecto_mangle}", Horas).',
            'progreso': f'progreso_proyecto("{proyecto_mangle}", Porcentaje, Fecha).',
            'equipo': f'asignacion(Persona, "{proyecto_mangle}").',
            'horas_por_persona': f'horas_semanales(Persona, "{proyecto_mangle}", Horas).'
        }
        
        resultados = {}
        for metrica, query in queries.items():
            resultado = consultar_base_de_conocimiento(query)
            resultados[metrica] = resultado
        
        # Formatear respuesta
        reporte = f"📊 MÉTRICAS DEL PROYECTO: {proyecto}\n"
        reporte += "=" * 50 + "\n"
        
        for metrica, valor in resultados.items():
            reporte += f"{metrica.upper()}: {valor}\n"
        
        return reporte
    
    except Exception as e:
        return f"Error al calcular métricas: {str(e)}"

def detectar_proyectos_en_riesgo():
    """
    Detecta proyectos que están en riesgo basado en métricas.
    """
    query = '''
    proyecto_en_riesgo(Proyecto, Razon) :-
        estado_proyecto(Proyecto, "activo"),
        progreso_proyecto(Proyecto, Porcentaje, _),
        fecha_fin_proyecto(Proyecto, FechaFin),
        Porcentaje < 50,
        FechaFin < "2025-12-31".
    '''
    return consultar_base_de_conocimiento(query)

def calcular_carga_trabajo_equipo():
    """
    Calcula la carga de trabajo total por persona.
    """
    query = '''
    carga_total(Persona, HorasTotal) :-
        asignacion(Persona, _),
        findall(H, horas_semanales(Persona, _, H), Lista),
        sum_list(Lista, HorasTotal).
    '''
    return consultar_base_de_conocimiento(query)

def sugerir_redistribucion_carga():
    """
    Sugiere redistribución de carga basada en sobrecarga detectada.
    """
    query = '''
    persona_sobrecargada(Persona) :-
        carga_total(Persona, Horas),
        Horas > 40.
    
    persona_disponible(Persona) :-
        carga_total(Persona, Horas),
        Horas < 30.
    '''
    return consultar_base_de_conocimiento(query)

def generar_dashboard_metricas():
    """
    Genera un dashboard completo con todas las métricas clave.
    """
    try:
        queries = {
            'proyectos_activos': 'estado_proyecto(P, "activo").',
            'proyectos_completados': 'estado_proyecto(P, "completado").',
            'proyectos_en_pausa': 'estado_proyecto(P, "pausado").',
            'total_presupuesto': 'presupuesto_proyecto(P, B).',
            'equipo_total': 'asignacion(Persona, _).',
            'proyectos_prioritarios': 'prioridad_proyecto(P, "alta").'
        }
        
        dashboard = "\n🎯 DASHBOARD DE MÉTRICAS DEL EQUIPO\n"
        dashboard += "=" * 60 + "\n\n"
        
        for metrica, query in queries.items():
            resultado = consultar_base_de_conocimiento(query)
            dashboard += f"📈 {metrica.upper().replace('_', ' ')}: {resultado}\n"
        
        # Métricas calculadas adicionales
        dashboard += "\n🚨 ALERTAS:\n"
        dashboard += f"Proyectos en riesgo: {detectar_proyectos_en_riesgo()}\n"
        dashboard += f"Personas sobrecargadas: {sugerir_redistribucion_carga()}\n"
        
        return dashboard
    
    except Exception as e:
        return f"Error al generar dashboard: {str(e)}"

def exportar_metricas_csv(archivo_salida="metricas_equipo.csv"):
    """
    Exporta todas las métricas a un archivo CSV para análisis externo.
    """
    try:
        # Consultar datos principales
        proyectos = consultar_base_de_conocimiento('proyecto(P).')
        asignaciones = consultar_base_de_conocimiento('asignacion(Persona, Proyecto).')
        
        # Crear CSV con métricas
        with open(archivo_salida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Proyecto', 'Persona', 'Horas_Semanales', 'Porcentaje_Dedicacion', 'Estado', 'Presupuesto'])
            
            # Aquí procesarías los resultados de las consultas
            # Este es un ejemplo simplificado
            writer.writerow(['Proyecto_Alpha', 'Juan_Pérez', '20', '50%', 'activo', '50000'])
        
        return f"Métricas exportadas a {archivo_salida}"
    
    except Exception as e:
        return f"Error al exportar métricas: {str(e)}"

# Funciones auxiliares para consultas específicas
def buscar_proyectos_por_estado(estado):
    """Busca proyectos por estado específico"""
    query = f'estado_proyecto(Proyecto, "{estado}").'
    return consultar_base_de_conocimiento(query)

def buscar_equipo_proyecto(proyecto):
    """Busca todo el equipo asignado a un proyecto"""
    proyecto_mangle = proyecto.replace(" ", "_")
    query = f'asignacion(Persona, "{proyecto_mangle}").'
    return consultar_base_de_conocimiento(query)

def calcular_progreso_promedio():
    """Calcula el progreso promedio de todos los proyectos activos"""
    query = '''
    progreso_promedio(PromedioTotal) :-
        findall(P, progreso_proyecto(_, P, _), ListaProgresos),
        length(ListaProgresos, Cantidad),
        sum_list(ListaProgresos, SumaTotal),
        PromedioTotal is SumaTotal / Cantidad.
    '''
    return consultar_base_de_conocimiento(query)
