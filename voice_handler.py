# voice_handler.py

import os
import requests
import uuid
from dotenv import load_dotenv

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

def speak_response(text):
    CHUNK_SIZE = 1024
    url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
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

    file_name = f"response_{uuid.uuid4().hex}.mp3" 
    file_path = os.path.join(static_dir, file_name)
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
        return {"success": True, "file_path": file_path}
    else:
        return {"success": False, "error": f"Error en la API: {response.text}"}