from pydantic import BaseModel, EmailStr, Field


# 🔹 Registro de usuario
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


# 🔹 Login de usuario
class UserLogin(BaseModel):
    username: str
    password: str


# 🔹 Respuesta básica del usuario (sin password)
class UserResponse(BaseModel):
    id_usuario: int
    username: str
    email: EmailStr
    estado: str


# 🔹 Respuesta genérica del sistema
class MessageResponse(BaseModel):
    status: str
    message: str