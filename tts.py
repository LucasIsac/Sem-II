# tts.py - Versión corregida

import os
import requests
import uuid
from dotenv import load_dotenv

class TTS():
    def __init__(self):
        load_dotenv()
        self.key = os.getenv('ELEVENLABS_API_KEY')

    def process(self, text):
        CHUNK_SIZE = 1024
        url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.key
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v1",
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.55
            }
        }

        static_dir = "static"
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)

        # Generar un nombre de archivo único para evitar conflictos
        file_name = f"response_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(static_dir, file_name)

        # ---------------------------------------------------------------------
        # CAMBIO CLAVE: Usa un bloque try-except para la llamada a requests
        # y verifica el código de estado de la respuesta.
        # ---------------------------------------------------------------------
        try:
            response = requests.post(url, json=data, headers=headers, stream=True)
            response.raise_for_status()  # Esto lanzará una excepción para códigos de error HTTP

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
            
            # Devuelve la ruta completa del archivo si todo fue exitoso
            return file_path

        except requests.exceptions.RequestException as e:
            # Captura errores de conexión o de la API
            error_message = f"Error al llamar a la API de Eleven Labs: {e}"
            print(error_message)
            return None  # Devuelve None si falla
        
        except Exception as e:
            # Captura cualquier otro error
            print(f"Ocurrió un error inesperado al procesar el audio: {e}")
            return None