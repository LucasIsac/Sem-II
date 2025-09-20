# Historial de Cambios

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
