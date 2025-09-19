# FileMate AI - Lista de Tareas y Mejoras

Este documento contiene una lista de sugerencias para mejorar y ampliar las capacidades del asistente FileMate AI.

---

## ✅ **Sugerencias de Mejora para el Código Actual**

Estas son mejoras enfocadas en hacer el código existente más robusto, seguro y amigable para el usuario.

### 1. Mejorar Manejo de Errores y Feedback al Usuario
- **Problema:** Actualmente, si una herramienta falla, a menudo devuelve un mensaje de error técnico (por ejemplo, una excepción de Python). Esto puede ser confuso para un usuario no técnico.
- **Sugerencia:** Refinar las funciones en `tools.py` para que capturen excepciones específicas y devuelvan mensajes más amigables. El agente podría ser instruido para ofrecer soluciones o alternativas cuando un error ocurre.
  - *Ejemplo:* Si `rename_file` no encuentra un archivo, en lugar de solo decir "El archivo no existe", el agente podría responder: "No pude encontrar el archivo 'documento.txt'. ¿Quizás quisiste decir 'documento_final.txt'? Puedes pedirme que liste los archivos para ver los nombres correctos."

### 2. Añadir Validación de Rutas y Seguridad
- **Problema:** Las operaciones se ejecutan directamente en el sistema de archivos. Aunque están limitadas al directorio `files`, un comando mal interpretado por el LLM podría intentar acceder a rutas inesperadas (ej. `../`).
- **Sugerencia:** Añadir una capa de validación en cada función de `tools.py` para asegurarse de que la ruta final del archivo o carpeta a modificar esté siempre contenida dentro del directorio de trabajo (`WORKING_DIR`). Esto previene cualquier intento de "escapar" de la carpeta designada.

### 3. Implementar Confirmación para Acciones Destructivas
- **Problema:** Las acciones como `delete_file` y `delete_folder` se ejecutan de inmediato. Un error de transcripción de voz o una instrucción ambigua podría llevar a la pérdida de datos irreversible.
- **Sugerencia:** Modificar el agente para que, antes de ejecutar una herramienta destructiva, haga una pregunta de confirmación al usuario.
  - *Ejemplo:* "Estás a punto de eliminar la carpeta 'proyecto_importante' y todo su contenido. ¿Estás seguro de que quieres continuar? (sí/no)".

### 4. Refactorizar el Paso de Argumentos a las Herramientas
- **Problema:** El uso de `lambda x: func(*x.split("|"))` en `agent.py` es frágil. Si el LLM no genera el string con el formato exacto `argumento1|argumento2`, la herramienta fallará.
- **Sugerencia:** Modificar las funciones en `tools.py` para que acepten un único string como argumento y sean ellas mismas las responsables de parsearlo. Esto hace que las herramientas sean más robustas y el agente más simple.

---

## 🚀 **Nuevas Funcionalidades Propuestas**

Estas son nuevas capacidades que se pueden agregar para que el asistente sea mucho más potente y versátil.

### 1. Interactuar con el Contenido de los Archivos
- **Descripción:** Permitir que el asistente pueda "leer" y "entender" el contenido de los archivos, no solo gestionar sus nombres y formatos.
- **Nuevas Herramientas Sugeridas:**
  - `read_file_content(file_path)`: Para leer el contenido de archivos de texto (`.txt`, `.md`, `.py`, etc.).
  - `summarize_document(file_path)`: Para extraer las ideas principales de un `.txt`, `.pdf` o `.docx`.
  - `search_in_file(file_path, query)`: Para buscar una palabra o frase específica dentro de un archivo.

### 2. Compresión y Descompresión de Archivos (ZIP)
- **Descripción:** Añadir la capacidad de trabajar con archivos comprimidos, una tarea muy común en la gestión de archivos.
- **Nuevas Herramientas Sugeridas:**
  - `create_zip_archive(source_files, zip_name)`: Para comprimir uno o más archivos/carpetas en un archivo `.zip`.
  - `extract_zip_archive(zip_path, destination_folder)`: Para descomprimir un archivo `.zip`.

### 3. Implementar Operaciones en Lote (Múltiples Archivos)
- **Descripción:** Permitir al usuario realizar acciones sobre muchos archivos a la vez para mejorar la eficiencia.
- **Ejemplos de Comandos:**
  - "Mueve todos los archivos PDF de la carpeta 'descargas' a 'facturas'".
  - "Renombra todos los archivos que empiezan con 'IMG_' y ponles el prefijo 'foto_vacaciones_'".
  - "Convierte todas las imágenes `.jpg` de la carpeta 'fotos' a formato `.png`".

### 4. Descarga de Archivos desde Internet
- **Descripción:** Hacer que el asistente pueda traer nuevos archivos al sistema desde la web.
- **Nueva Herramienta Sugerida:**
  - `download_file(url, save_name)`: Para descargar un archivo desde una URL y guardarlo en el directorio de trabajo.

### 5. Integración con Git (Control de Versiones)
- **Descripción:** Para usuarios más avanzados, añadir la capacidad de realizar operaciones básicas de Git mediante comandos de voz o texto.
- **Nuevas Herramientas Sugeridas:**
  - `git_status()`: Para ver el estado de los cambios.
  - `git_add(file_name)`: Para añadir un archivo al staging.
  - `git_commit(message)`: Para hacer un commit con un mensaje.
