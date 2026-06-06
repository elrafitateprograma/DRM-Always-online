from passlib.context import CryptContext
from app.db import get_connection
from app.schemas.users import UserRegister, UserLogin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user_by_username(username: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id_usuario, nombre_usuario, email, password, estado
        FROM usuarios
        WHERE nombre_usuario = %s;
        """,
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def get_user_by_email(email: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id_usuario, nombre_usuario, email, password, estado
        FROM usuarios
        WHERE email = %s;
        """,
        (email,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def register_user(data: UserRegister):
    if get_user_by_username(data.username):
        return {
            "success": False,
            "message": "El nombre de usuario ya existe"
        }

    if get_user_by_email(data.email):
        return {
            "success": False,
            "message": "El email ya está registrado"
        }

    password_hash = hash_password(data.password)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO usuarios (nombre_usuario, email, password, estado)
        VALUES (%s, %s, %s, %s)
        RETURNING id_usuario, nombre_usuario, email, estado;
        """,
        (data.username, data.email, password_hash, "activa")
    )

    new_user = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": "Usuario registrado correctamente",
        "user": new_user
    }


def login_user(data: UserLogin):
    user = get_user_by_username(data.username)

    if not user:
        return {
            "success": False,
            "message": "El usuario no existe"
        }

    if user["estado"] != "activa":
        return {
            "success": False,
            "message": "La cuenta no se encuentra activa"
        }

    if not verify_password(data.password, user["password"]):
        return {
            "success": False,
            "message": "Contraseña incorrecta"
        }

    return {
        "success": True,
        "message": "Inicio de sesión correcto",
        "user": {
            "id_usuario": user["id_usuario"],
            "username": user["nombre_usuario"],
            "email": user["email"],
            "estado": user["estado"]
        }
    }