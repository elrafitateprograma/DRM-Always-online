from pydantic import BaseModel
from typing import Optional


class SessionStart(BaseModel):
    id_usuario: int
    id_dispositivo: int


class SessionHeartbeat(BaseModel):
    token_sesion: str


class SessionEnd(BaseModel):
    token_sesion: str


class SessionResponse(BaseModel):
    success: bool
    message: str
    token_sesion: Optional[str] = None
    id_sesion: Optional[int] = None