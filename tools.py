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

def convert_pdf_to_word(pdf_path, docx_path=None):
    """Convierte un archivo PDF a formato Word"""
    pdf_full_path = os.path.join('files', pdf_path)
    if not os.path.exists(pdf_full_path):
        return {"success": False, "message": f"El archivo PDF '{pdf_path}' no existe"}
    
    if not docx_path:
        docx_path = pdf_path.replace('.pdf', '.docx')
    docx_full_path = os.path.join('files', docx_path)
    
    try:
        # Leer el PDF
        pdf_file = open(pdf_full_path, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Crear un nuevo documento Word
        doc = Document()
        
        # Extraer texto de cada página
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            doc.add_paragraph(text)
            if page_num < len(pdf_reader.pages) - 1:  # No agregar salto de página después de la última página
                doc.add_page_break()
        
        # Guardar el documento Word
        doc.save(docx_full_path)
        pdf_file.close()
        
        return {"success": True, "message": f"PDF convertido a Word: {docx_path}", "new_file": docx_full_path}
    except Exception as e:
        return {"success": False, "message": f"Error en la conversión: {str(e)}"}

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
