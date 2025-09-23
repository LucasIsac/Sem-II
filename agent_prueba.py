from tools import (
    cargar_conocimiento_desde_archivo, 
    consultar_base_de_conocimiento, 
    limpiar_base_de_conocimiento, 
    analizar_y_cargar_contactos_desde_archivo,
    agregar_contacto_a_archivo
)

def probar_flujo_completo_interactivo():
    """
    Script que simula el flujo completo:
    1. Carga inicial de conocimiento.
    2. Añade un nuevo contacto a un archivo (simulando un comando de chat).
    3. Actualiza la base de conocimiento desde el archivo modificado.
    4. Verifica que el nuevo contacto existe en Mangle.
    """
    ruta_contactos_txt = "contactos.txt"

    print("--- INICIO DE LA PRUEBA DE FLUJO INTERACTIVO ---")

    # 1. Limpiar la base de conocimiento para un estado inicial limpio.
    print("\nPaso 1: Limpiando la base de conocimiento...")
    print(f"Resultado: {limpiar_base_de_conocimiento()}")

    # 2. Añadir un nuevo contacto al archivo, simulando la entrada del usuario.
    print("\nPaso 2: Añadiendo a 'Pepe' al archivo de contactos...")
    print(f"Resultado: {agregar_contacto_a_archivo('Pepe', 'Tester', 'pepeejemplo@gamil.com', 'Proyecto de FileMateIa')}")

    # 3. Analizar el archivo de contactos actualizado y cargar la información a Mangle.
    print(f"\nPaso 3: Analizando '{ruta_contactos_txt}' y actualizando Mangle...")
    print(f"Resultado: {analizar_y_cargar_contactos_desde_archivo(ruta_contactos_txt)}")

    # 4. Consultar por el nuevo contacto para verificar que se añadió correctamente.
    print("\nPaso 4: Verificando que 'Pepe' fue añadido a la base de conocimiento...")
    consulta_pepe = consultar_base_de_conocimiento('trabaja_en("Pepe", Puesto).')
    print(f"Resultado de la consulta para Pepe: {consulta_pepe}")
    
    print("\n--- FIN DE LA PRUEBA ---")

if __name__ == "__main__":
    probar_flujo_completo_interactivo()
