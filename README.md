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

## Componentes Adicionales: Microservicio Mangle (Go)

El proyecto incluye un microservicio de alto rendimiento construido en Go que sirve una base de conocimiento utilizando el lenguaje deductivo Mangle. Este servicio es necesario para que funcionen las herramientas de consulta a la base de conocimiento.

### Requisitos Previos

-   Tener [Go (Golang)](https://go.dev/doc/install) instalado en tu sistema.

### Ejecución del Microservicio

1.  **Abre una nueva terminal** en la raíz del proyecto (no uses la misma donde corre Streamlit).

2.  **Navega al directorio del servidor:**
    ```bash
    cd mangle_service/server
    ```

3.  **Ejecuta el servidor:**
    ```bash
    go run main.go --db=../example/knowledge_base.mgl --source=../example/demo.mg
    ```

4.  El servidor se iniciará y comenzará a escuchar peticiones en el puerto `8080`. Déjalo corriendo en segundo plano mientras usas la aplicación principal.

### ¿Cómo Funciona Mangle en Este Proyecto?

Mangle es una base de datos deductiva. A diferencia de las bases de datos tradicionales (como SQL) que almacenan datos y los recuperan, Mangle almacena **hechos** y **reglas** para **inferir nueva información**.

**1. Hechos (La Base del Conocimiento):**

Los hechos son declaraciones simples y atómicas sobre los datos. En este proyecto, cuando agregas un contacto, la función `agregar_contacto` (en `tools.py`) genera un conjunto de hechos como este:

```prolog
// Hechos para el contacto "Juan Pérez"
contacto("juan_perez").
nombre_real("juan_perez", "Juan Pérez").
tiene_puesto("juan_perez", "desarrollador").
tiene_email("juan_perez", "juan.perez@email.com").
trabaja_en_proyecto("juan_perez", "proyecto_alpha").
```

Estos hechos se envían al microservicio de Mangle a través de gRPC y se almacenan.

**2. Reglas (La Lógica de Inferencia):**

Las reglas permiten a Mangle deducir nueva información a partir de los hechos existentes. Las reglas se definen en el archivo `mangle_service/example/knowledge_base.mgl`. Por ejemplo, podrías tener una regla para definir qué es un "contacto clave":

```prolog
// Un contacto es "clave" si trabaja en el "Proyecto Alpha"
contacto_clave(Nombre) :- 
  trabaja_en_proyecto(Nombre, "proyecto_alpha").
```

**3. Consultas (Haciendo Preguntas a la Base de Conocimiento):**

Una vez que los hechos y las reglas están en la base de conocimiento, el agente de IA puede realizar consultas para obtener información que no está explícitamente almacenada.

Por ejemplo, si le preguntas a FileMate AI:

> "¿Quiénes son los contactos clave?"

El agente usará la herramienta `consultar_base_de_conocimiento` para enviar la siguiente consulta a Mangle:

```prolog
contacto_clave(X).
```

Mangle utilizará la regla `contacto_clave` y los hechos existentes para inferir que `juan_perez` es un contacto clave y devolverá ese resultado.

Esta arquitectura permite un razonamiento mucho más avanzado que simplemente buscar en un archivo de texto. Puedes definir relaciones complejas y dejar que Mangle haga las deducciones por ti.

---

## Tecnologías Utilizadas

-   **Lenguaje de Programación**:
    -   **Python**: El lenguaje principal sobre el que se construye todo el proyecto.
-   **Inteligencia Artificial y Modelos de Lenguaje**:
    -   **Google Gemini**: Modelo de lenguaje de última generación que impulsa la capacidad de razonamiento del agente.
    -   **LangChain**: Framework esencial para orquestar las interacciones entre el modelo de lenguaje, las herramientas y la lógica de la aplicación.
-   **Interfaz de Usuario**:
    -   **Streamlit**: Para crear de forma rápida una interfaz de usuario web interactiva.
-   **Interacción por Voz**:
    -   **SpeechRecognition**: Para transcribir los comandos de voz del usuario a texto.
    -   **ElevenLabs**: Para sintetizar respuestas de voz (Text-to-Speech) con alta calidad.
    -   **Playsound**: Para reproducir los archivos de audio generados.
-   **Manipulación de Archivos**:
    -   **CloudConvert API**: Servicio externo para realizar conversiones de formato de archivo robustas.
    -   **Pillow**: Para el procesamiento y conversión de imágenes.
    -   **python-docx**: Para la creación y manipulación de archivos `.docx` (Word).
    -   **PyPDF2**: Para la lectura y manipulación básica de archivos `.pdf`.
    -   **pdf2docx / docx2pdf**: Librerías especializadas para conversiones directas entre PDF y Word.
-   **Comunicación y Entorno**:
    -   **Requests**: Para realizar peticiones HTTP a APIs externas como CloudConvert.
    -   **python-dotenv**: Para la gestión de variables de entorno y claves de API.
-   **Base de Datos Deductiva y Microservicios**:
    -   **Mangle**: Lenguaje de programación deductivo (extensión de Datalog) de Google, utilizado para crear una base de conocimiento y realizar razonamiento complejo.
    -   **Go (Golang)**: Lenguaje de programación utilizado para construir el microservicio de alto rendimiento que sirve la base de conocimiento de Mangle.
    -   **gRPC**: Framework de comunicación moderno y de alta eficiencia para la comunicación entre el agente de Python y el microservicio de Go.

## Nivel de Actualidad y Relevancia de las Tecnologías

El proyecto integra un ecosistema de herramientas que se pueden clasificar según su modernidad y rol en la industria actual.

-   **Nivel Vanguardia (Cutting-Edge):** Estas son las tecnologías más recientes y disruptivas que definen el estado del arte en IA.
    -   **Mangle**: Un proyecto reciente de Google que explora el paradigma de las bases de datos deductivas, una aproximación novedosa para el razonamiento en sistemas de IA.
    -   **Google Gemini**: Como uno de los modelos de lenguaje más avanzados, representa la frontera de la capacidad de la IA generativa. Su lanzamiento es muy reciente (finales de 2023).
    -   **LangChain**: Aunque es un proyecto joven, se ha convertido en el estándar de facto para construir aplicaciones con LLMs. Su desarrollo es extremadamente activo y evoluciona a una velocidad vertiginosa.
    -   **ElevenLabs**: Líder en el campo de la síntesis de voz realista, ofreciendo una calidad que era inalcanzable hace pocos años.

-   **Nivel Moderno y Relevante:** Tecnologías que, sin ser necesariamente de última generación, son estándares actuales en el desarrollo de software, especialmente en el ámbito de datos y IA.
    -   **Go (Golang)**: Se ha establecido como un lenguaje líder para el desarrollo de microservicios de alto rendimiento, concurrencia y sistemas en la nube.
    -   **gRPC**: Es el estándar moderno para la comunicación entre microservicios, superando a las APIs REST tradicionales en escenarios que requieren alta eficiencia.
    -   **Streamlit**: Se ha consolidado como la herramienta preferida para crear prototipos y aplicaciones de datos/IA en Python de forma rápida y eficiente.
    -   **CloudConvert**: El uso de APIs especializadas para tareas complejas (como la conversión de archivos) es un enfoque de desarrollo moderno que favorece la modularidad y la eficiencia.

-   **Nivel Establecido y Maduro:** Librerías y herramientas que han demostrado su fiabilidad a lo largo del tiempo y son pilares en el ecosistema de Python.
    -   **Python**: Sigue siendo el lenguaje dominante en IA y ciencia de datos, con un ecosistema maduro y una comunidad masiva.
    -   **Pillow, PyPDF2, python-docx, Requests**: Son librerías fundamentales y altamente confiables, mantenidas activamente durante años, que resuelven problemas específicos de manera muy eficaz.
    -   **SpeechRecognition**: Una librería consolidada que proporciona una interfaz sencilla para varios motores de reconocimiento de voz.
