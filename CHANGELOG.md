# Historial de Cambios

## Lucas

### Modificaciones y Mejoras

- **Corrección del `system_prompt`**: Se ajustó la lógica en `agent.py` para asegurar que el modelo de IA (Gemini) adopte correctamente la personalidad de "FileMate AI". El `system_prompt` ahora se pasa a través de `agent_kwargs` en la inicialización del agente de LangChain.
- **Eliminación de Conflicto de Modelos**: Se identificó y resolvió un conflicto que causaba que la aplicación utilizara un modelo de OpenAI en lugar del modelo Gemini configurado.
  - Se eliminaron las importaciones y la configuración de la API de OpenAI del archivo `app.py`.
  - Se limpió el archivo `requirements.txt` para eliminar la dependencia de `langchain-openai`.
  - Se desinstalaron los paquetes `langchain-openai` y `openai` del entorno para forzar el uso exclusivo de Gemini.
- **Actualización de Documentación**: Se actualizó el archivo `README.md` para incluir **ElevenLabs** en la lista de tecnologías utilizadas para la síntesis de voz.
