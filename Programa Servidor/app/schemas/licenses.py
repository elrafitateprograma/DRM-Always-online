from pydantic import BaseModel, Field
from typing import Optional


class LicenseActivate(BaseModel):
    id_usuario: int
    clave_licencia: str = Field(
        ...,
        pattern=r"^[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}$",
        description="Clave de licencia en formato hexadecimal XXXX-XXXX"
    )


class LicenseRemove(BaseModel):
    id_usuario: int


class LicenseStatusResponse(BaseModel):
    has_license: bool
    message: str
    id_licencia: Optional[int] = None
    clave_licencia: Optional[str] = None
    clase_licencia: Optional[str] = None
    fecha_activacion: Optional[str] = None
    fecha_caducidad: Optional[str] = None
    estado_licencia: Optional[str] = None
    num_dispositivos: Optional[int] = None


class MessageResponse(BaseModel):
    status: str
    message: str