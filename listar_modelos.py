import google.generativeai as genai

# Configura tu API key
genai.configure(api_key="AIzaSyDQQy9AHCNa5ZbFQgUZc_wsDBhp7LIHdOI")

# Listar modelos disponibles
modelos = genai.list_models()
print("Modelos disponibles:")
for modelo in modelos:
    print(modelo.name)  # <- acceder como atributo

