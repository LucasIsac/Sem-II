import os
from pdfminer.high_level import extract_text
from docx import Document
import csv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import pickle

VECTOR_DB_PATH = "knowledge/vectorstore.pkl"

# Cargar vector store existente o crear uno nuevo
if os.path.exists(VECTOR_DB_PATH):
    with open(VECTOR_DB_PATH, "rb") as f:
        vectorstore = pickle.load(f)
else:
    vectorstore = FAISS(embeddings=OpenAIEmbeddings(), index=None)

def procesar_archivo(file_path):
    texto = ""
    if file_path.endswith(".pdf"):
        texto = extract_text(file_path)
    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        texto = "\n".join([p.text for p in doc.paragraphs])
    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            texto = f.read()
    elif file_path.endswith(".csv"):
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            texto = "\n".join([", ".join(row) for row in reader])
    else:
        print("Formato no soportado:", file_path)
        return

    agregar_a_base_conocimiento(file_path, texto)

def agregar_a_base_conocimiento(file_path, texto):
    vectorstore.add_texts([texto], metadatas=[{"source": file_path}])
    with open(VECTOR_DB_PATH, "wb") as f:
        pickle.dump(vectorstore, f)
    print(f"Archivo agregado a la base de conocimiento: {file_path}")

def procesar_carpeta_recursiva(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            full_path = os.path.join(root, file)
            procesar_archivo(full_path)
