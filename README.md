# FileMate AI - Asistente de Archivos Inteligente

FileMate AI es un asistente inteligente que te permite manipular archivos y carpetas en tu sistema local mediante comandos de voz o texto. Utiliza la potencia del modelo de lenguaje Gemma de Google para interpretar tus intenciones y ejecutar acciones como renombrar archivos, convertir formatos y más.

## Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

```
/
|-- files/                # Directorio de trabajo para los archivos del usuario
|-- .gitignore            # Archivos y carpetas ignorados por Git
|-- app.py                # Aplicación principal de Streamlit
|-- agent.py              # Agente de IA que procesa los comandos
|-- tools.py              # Funciones para manipular archivos
|-- requirements.txt      # Dependencias del proyecto
|-- .env                  # Archivo para variables de entorno (API key)
|-- README.md             # Este archivo
```

## Instalación

Para poner en marcha el proyecto, sigue estos pasos:

1.  **Clona el repositorio:**

    ```bash
    git clone https://github.com/LucasIsac/Sem-II.git
    cd Sem-II
    ```

2.  **Crea un entorno virtual:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instala las dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura tu API Key:**

    -   Renombra el archivo `.env.example` a `.env`.
    -   Abre el archivo `.env` y reemplaza `"tu_api_key_de_google_gemini_aqui"` con tu API key de Google Gemini.

## ¿Qué hace cada programa?

-   `app.py`: Es el punto de entrada de la aplicación. Crea la interfaz de usuario con Streamlit, gestiona la carga de archivos y recibe los comandos del usuario.
-   `agent.py`: Contiene la lógica del agente de IA. Utiliza LangChain y el modelo Gemini para interpretar el comando del usuario y decidir qué herramienta ejecutar.
-   `tools.py`: Define las funciones que el agente puede utilizar para manipular archivos, como renombrar, convertir formatos, etc.

## ¿Cómo probar el proyecto?

1.  **Inicia la aplicación:**

    ```bash
    streamlit run app.py
    ```

2.  **Abre tu navegador:**

    -   Streamlit te proporcionará una URL local (normalmente `http://localhost:8501`).

3.  **Interactúa con la aplicación:**

    -   Sube archivos utilizando la interfaz.
    -   Escribe comandos en el campo de texto, por ejemplo:
        -   "Renombra `mi_archivo.txt` a `documento_final.txt`"
        -   "Convierte `informe.pdf` a Word"
        -   "Cambia el formato de `logo.jpg` a `png`"

## Tecnologías Utilizadas

-   **Python**: Lenguaje de programación principal.
-   **Streamlit**: Para crear la interfaz de usuario web.
-   **LangChain**: Framework para construir aplicaciones con modelos de lenguaje.
-   **Google Gemini**: Modelo de lenguaje para la IA.
-   **Pillow**: Para la manipulación de imágenes.
-   **python-docx**: Para crear archivos de Word.
-   **PyPDF2**: Para leer archivos PDF.

## Nivel de Actualidad de las Tecnologías

El proyecto combina tecnologías de vanguardia con herramientas modernas y establecidas para lograr un resultado robusto y funcional.

-   **Tecnologías de Vanguardia (Lo más nuevo):**
    -   **Google Gemini / Gemma:** Modelo de lenguaje de última generación (lanzado entre finales de 2023 y principios de 2024).
    -   **LangChain:** Framework líder para el desarrollo con LLMs, en constante y rápida evolución.

-   **Tecnologías Modernas:**
    -   **Streamlit:** Un framework relativamente reciente y muy popular para crear aplicaciones web interactivas en el ecosistema de Python y la IA.

-   **Tecnologías Establecidas y Maduras:**
    -   **Python:** Lenguaje de programación con décadas de existencia, pero más relevante que nunca gracias a su dominio en el campo de la IA.
    -   **Pillow, PyPDF2, python-docx:** Librerías estándar y muy confiables para la manipulación de archivos, mantenidas activamente durante años.
