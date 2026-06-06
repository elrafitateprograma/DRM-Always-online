from pydantic import BaseModel, Field
from typing import Optional


class EventCreate(BaseModel):
    tipo_evento: str = Field(..., min_length=2, max_length=50)
    descripcion: str = Field(..., min_length=2)
    id_sesion: int


class EventResponse(BaseModel):
    id_evento: int
    tipo_evento: str
    fecha: str
    hora: str
    descripcion: str
    id_sesion: int


class MessageResponse(BaseModel):
    status: str
    message: str