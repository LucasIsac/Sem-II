# Historial de Cambios

## 22 de Septiembre de 2025 - Limpieza y Refactorización del Proyecto

### 🧹 Limpieza de Archivos No Utilizados

-   Se han identificado y marcado para eliminación varios archivos que no están siendo utilizados en la aplicación principal. El objetivo es reducir el desorden en el repositorio y simplificar la estructura del proyecto.
-   **Archivos a eliminar:**
    -   `file_processor.py`: Módulo para la creación de una base de datos vectorial que no se implementó.
    -   `watcher.py`: Observador del sistema de archivos, diseñado para `file_processor.py`.
    -   `test.py`: Versión de prueba o copia antigua de `app.py`.
    -   `agent_prueba.py`: Archivo de prueba para el agente de IA.
    -   `mangle_client_test.py`: Pruebas para el cliente de Mangle.

---

## 21 de Septiembre de 2025 - Optimización de Rendimiento y Corrección del Repositorio

### ✨ Nuevas Características y Mejoras

-   **Implementación de Caché de Archivos (`app.py`, `agent.py`):** Se ha introducido un sistema de caché inteligente para la estructura de archivos.
    -   La aplicación ahora solo escanea el directorio de trabajo una vez al inicio o cuando se produce un cambio real en los archivos (crear, renombrar, eliminar, etc.).
    -   Esto resulta en una mejora significativa del rendimiento, ya que las operaciones de solo lectura (como buscar archivos) son ahora instantáneas y no requieren un escaneo del disco.
    -   Se ha añadido un botón "Refrescar vista de archivos" en la interfaz para actualizar manualmente el caché si se realizan cambios externos.

### 🐞 Problema Solucionado

-   **Corrección de Repositorio Git Anidado:** Se solucionó un problema crítico que causaba que la carpeta `mangle_service` apareciera como un "submódulo sucio" en GitHub, impidiendo ver su contenido.
    -   Se eliminó el repositorio `.git` anidado dentro de `mangle_service`.
    -   Se corrigió el índice de Git para que el repositorio principal (`Sem-II`) ahora rastree correctamente todos los archivos del microservicio.

---

## 20 de Septiembre de 2025 - Robustecimiento del Agente y Herramientas de Archivos

### 🐞 Problema Solucionado

-   **Fallo de Lógica del Agente al Mover Archivos:** Se identificó un problema crítico donde el agente de IA no utilizaba el contexto de la estructura de archivos para localizar ficheros en subcarpetas. Esto causaba que comandos como "mover `doc.txt` a `prueba`" fallaran, ya que el agente no construía la ruta de origen completa.

### 🛠️ Solución Implementada

-   **Herramienta `move_file` Inteligente (`tools.py`):** Se rediseñó por completo la función `move_file`. Ahora, si la ruta inicial no se encuentra, la herramienta busca proactivamente el archivo en todo el árbol de directorios. Esta modificación traslada la lógica de búsqueda del LLM (que era propenso a errores) al código Python, garantizando un comportamiento fiable.
-   **Simplificación del Prompt del Agente (`agent.py`):** Como consecuencia de la mejora en la herramienta, se simplificaron las complejas reglas de movimiento de archivos en el `system_prompt` del agente. El agente ahora puede operar de manera más directa, reduciendo la probabilidad de errores de razonamiento.

### ✨ Resultado

-   El asistente ahora puede mover archivos entre carpetas de forma fiable, incluso si se encuentran en subdirectorios profundos, sin necesidad de que el usuario especifique la ruta completa. La interacción es más natural y robusta.

---

## 20 de Septiembre de 2025 - Integración de Mangle para Razonamiento Deductivo

### ✨ Nuevas Características

-   **Integración con Mangle:** Se ha añadido una nueva capacidad de razonamiento deductivo al agente de IA mediante la integración del lenguaje de programación Mangle.
-   **Servicio de Conocimiento gRPC:** Se ha configurado un microservicio local basado en Go que sirve una base de conocimiento de Mangle a través de gRPC.
-   **Nueva Herramienta - `consultar_base_de_conocimiento`:** Se ha añadido una nueva herramienta en `tools.py` que permite al agente realizar consultas complejas a la base de conocimiento. El cliente gRPC en Python se encarga de la comunicación con el servicio de Mangle.
-   **Agente Mejorado:** El agente principal en `agent.py` ha sido actualizado para utilizar esta nueva herramienta, permitiéndole responder a preguntas que requieren deducción y razonamiento sobre relaciones de datos.

### 🔧 Configuración

-   Se requiere la instalación de **Go** para ejecutar el servidor de Mangle.
-   Se han añadido las dependencias de Python `grpcio` y `grpcio-tools`.
-   Los archivos de la base de conocimiento (`.mgl`) se encuentran en el directorio `mangle_service/example`.



### Modificaciones y Mejoras

- **Mejora en la Lógica del Agente de IA (`agent.py`)**:
  - Se reescribieron las instrucciones (`system_prompt`) del agente con reglas críticas y obligatorias para interpretar comandos de movimiento de archivos y carpetas.
  - El agente ahora debe construir rutas de origen completas y anidadas, prestando atención a palabras clave como "en", "dentro de", "desde".
  - Se implementó una regla de "verificar antes de actuar": el agente ahora está obligado a usar la herramienta `search_files` para confirmar nombres de archivos o carpetas si sospecha de un error tipográfico o ambigüedad, evitando movimientos incorrectos.
- **Corrección de Bug en Funciones de Movimiento (`tools.py`)**:
  - Se solucionó un bug crítico en las funciones `move_file` y `move_folder` que causaba que la ruta de destino se construyera incorrectamente. Ahora `shutil.move` funciona de manera predecible.
- **Mejora en la Visualización de Archivos (`app.py`, `test.py`)**:
  - Se implementó una vista de árbol jerárquica para mostrar archivos y carpetas.
  - Las carpetas ahora aparecen con un ícono (📁) y son desplegables para ver su contenido.
  - Los archivos se muestran con un ícono (📄).
- **Optimización de `list_files` (`tools.py`)**:
  - La función ahora ordena los resultados para mostrar siempre las carpetas primero, y luego los archivos, ambos ordenados alfabéticamente.

## Lucas

### Modificaciones y Mejoras

- **Corrección del `system_prompt`**: Se ajustó la lógica en `agent.py` para asegurar que el modelo de IA (Gemini) adopte correctamente la personalidad de "FileMate AI". El `system_prompt` ahora se pasa a través de `agent_kwargs` en la inicialización del agente de LangChain.
- **Eliminación de Conflicto de Modelos**: Se identificó y resolvió un conflicto que causaba que la aplicación utilizara un modelo de OpenAI en lugar del modelo Gemini configurado.
  - Se eliminaron las importaciones y la configuración de la API de OpenAI del archivo `app.py`.
  - Se limpió el archivo `requirements.txt` para eliminar la dependencia de `langchain-openai`.
  - Se desinstalaron los paquetes `langchain-openai` y `openai` del entorno para forzar el uso exclusivo de Gemini.
- **Actualización de Documentación**: Se actualizó el archivo `README.md` para incluir **ElevenLabs** en la lista de tecnologías utilizadas para la síntesis de voz.
