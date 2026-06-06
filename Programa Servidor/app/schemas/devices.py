from pydantic import BaseModel, Field
from typing import Optional


class DeviceRegister(BaseModel):
    id_usuario: int
    fingerprint: str = Field(..., min_length=5, max_length=255)
    nombre: str = Field(..., min_length=2, max_length=120)


class DeviceResponse(BaseModel):
    id_dispositivo: int
    fingerprint: str
    nombre: str
    estado_dispositivo: str


class MessageResponse(BaseModel):
    status: str
    message: str