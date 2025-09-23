from pydantic import BaseModel, Field

class ContactoInput(BaseModel):
    nombre: str = Field(..., description="Nombre del contacto")
    rol: str = Field(..., description="Rol del contacto")
    email: str = Field(..., description="Correo electrónico del contacto")
    proyecto: str = Field(..., description="Proyecto asociado al contacto")
    archivo_destino: str = Field(..., description="Archivo donde guardar el contacto, ej: contactos.txt")
