import uuid
from datetime import datetime

from app.db import get_connection


HEARTBEAT_TIMEOUT_SECONDS = 15


def expire_old_sessions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE sesiones
        SET estado_sesion = 'expirada',
            fecha_fin = CURRENT_TIMESTAMP
        WHERE estado_sesion = 'activa'
          AND last_heartbeat < (CURRENT_TIMESTAMP - INTERVAL %s);
        """,
        (f"{HEARTBEAT_TIMEOUT_SECONDS} seconds",)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_user(id_usuario: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM usuarios
        WHERE id_usuario = %s;
        """,
        (id_usuario,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def get_device(id_dispositivo: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM dispositivos
        WHERE id_dispositivo = %s;
        """,
        (id_dispositivo,)
    )

    device = cursor.fetchone()

    cursor.close()
    conn.close()

    return device


def get_license_by_user(id_usuario: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM licencias
        WHERE id_usuario = %s;
        """,
        (id_usuario,)
    )

    license_data = cursor.fetchone()

    cursor.close()
    conn.close()

    return license_data


def get_active_session_for_device(id_usuario: int, id_dispositivo: int, id_licencia: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM sesiones
        WHERE id_usuario = %s
          AND id_dispositivo = %s
          AND id_licencia = %s
          AND estado_sesion = 'activa'
          AND last_heartbeat >= (CURRENT_TIMESTAMP - INTERVAL %s)
        LIMIT 1;
        """,
        (
            id_usuario,
            id_dispositivo,
            id_licencia,
            f"{HEARTBEAT_TIMEOUT_SECONDS} seconds"
        )
    )

    session = cursor.fetchone()

    cursor.close()
    conn.close()

    return session


def count_active_sessions_by_license(id_licencia: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM sesiones
        WHERE id_licencia = %s
          AND estado_sesion = 'activa'
          AND last_heartbeat >= (CURRENT_TIMESTAMP - INTERVAL %s);
        """,
        (id_licencia, f"{HEARTBEAT_TIMEOUT_SECONDS} seconds")
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["total"]


def mark_license_as_expired(cursor, id_licencia: int):
    cursor.execute(
        """
        UPDATE licencias
        SET estado_licencia = 'caducada'
        WHERE id_licencia = %s;
        """,
        (id_licencia,)
    )


def mark_session_as_expired(cursor, token_sesion: str):
    cursor.execute(
        """
        UPDATE sesiones
        SET estado_sesion = 'expirada',
            fecha_fin = CURRENT_TIMESTAMP
        WHERE token_sesion = %s;
        """,
        (token_sesion,)
    )


def is_license_expired(license_data) -> bool:
    return (
        license_data["fecha_caducidad"] is not None
        and license_data["fecha_caducidad"] < datetime.now()
    )


def start_session(id_usuario: int, id_dispositivo: int):
    expire_old_sessions()

    user = get_user(id_usuario)

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

    device = get_device(id_dispositivo)

    if not device:
        return {
            "success": False,
            "message": "El dispositivo no existe"
        }

    if device["id_usuario"] != id_usuario:
        return {
            "success": False,
            "message": "El dispositivo no pertenece al usuario"
        }

    if device["estado_dispositivo"] == "bloqueado":
        return {
            "success": False,
            "message": "El dispositivo se encuentra bloqueado"
        }

    license_data = get_license_by_user(id_usuario)

    if not license_data:
        return {
            "success": False,
            "message": "El usuario no tiene una licencia asociada"
        }

    if license_data["estado_licencia"] != "activa":
        return {
            "success": False,
            "message": "La licencia no está activa"
        }

    if is_license_expired(license_data):
        conn = get_connection()
        cursor = conn.cursor()

        mark_license_as_expired(cursor, license_data["id_licencia"])

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "success": False,
            "message": "La licencia está caducada"
        }

    existing_session = get_active_session_for_device(
        id_usuario,
        id_dispositivo,
        license_data["id_licencia"]
    )

    if existing_session:
        return {
            "success": True,
            "message": "Ya existe una sesión activa para este dispositivo",
            "token_sesion": str(existing_session["token_sesion"]),
            "id_sesion": existing_session["id_sesion"]
        }

    active_sessions = count_active_sessions_by_license(license_data["id_licencia"])

    if active_sessions >= license_data["num_dispositivos"]:
        return {
            "success": False,
            "message": "Se ha alcanzado el número máximo de dispositivos simultáneos"
        }

    token = uuid.uuid4()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO sesiones (
            token_sesion,
            fecha_inicio,
            fecha_fin,
            last_heartbeat,
            estado_sesion,
            id_usuario,
            id_dispositivo,
            id_licencia
        )
        VALUES (%s, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP, %s, %s, %s, %s)
        RETURNING *;
        """,
        (
            str(token),
            "activa",
            id_usuario,
            id_dispositivo,
            license_data["id_licencia"]
        )
    )

    session = cursor.fetchone()

    cursor.execute(
        """
        UPDATE dispositivos
        SET estado_dispositivo = 'conectado',
            fecha_ultima = CURRENT_TIMESTAMP
        WHERE id_dispositivo = %s;
        """,
        (id_dispositivo,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": "Sesión iniciada correctamente",
        "token_sesion": str(session["token_sesion"]),
        "id_sesion": session["id_sesion"]
    }


def heartbeat_session(token_sesion: str):
    expire_old_sessions()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM sesiones
        WHERE token_sesion = %s;
        """,
        (token_sesion,)
    )

    session = cursor.fetchone()

    if not session:
        cursor.close()
        conn.close()

        return {
            "success": False,
            "message": "La sesión no existe",
            "error": "ERR_SESSION_NOT_FOUND"
        }

    if session["estado_sesion"] != "activa":
        cursor.close()
        conn.close()

        return {
            "success": False,
            "message": "La sesión no está activa",
            "error": "ERR_SESSION_NOT_ACTIVE"
        }

    cursor.execute(
        """
        SELECT *
        FROM licencias
        WHERE id_licencia = %s;
        """,
        (session["id_licencia"],)
    )

    license_data = cursor.fetchone()

    if not license_data:
        mark_session_as_expired(cursor, token_sesion)

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "success": False,
            "message": "La licencia asociada a la sesión no existe",
            "error": "ERR_LICENSE_NOT_FOUND"
        }

    if is_license_expired(license_data):
        mark_license_as_expired(cursor, license_data["id_licencia"])
        mark_session_as_expired(cursor, token_sesion)

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "success": False,
            "message": "La licencia ha caducado durante la ejecución",
            "error": "ERR_LICENSE_EXPIRED"
        }

    if license_data["estado_licencia"] != "activa":
        mark_session_as_expired(cursor, token_sesion)

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "success": False,
            "message": "La licencia no está activa",
            "error": "ERR_LICENSE_NOT_ACTIVE"
        }

    cursor.execute(
        """
        UPDATE sesiones
        SET last_heartbeat = CURRENT_TIMESTAMP
        WHERE token_sesion = %s
        RETURNING *;
        """,
        (token_sesion,)
    )

    updated = cursor.fetchone()

    cursor.execute(
        """
        UPDATE dispositivos
        SET fecha_ultima = CURRENT_TIMESTAMP,
            estado_dispositivo = 'conectado'
        WHERE id_dispositivo = %s;
        """,
        (updated["id_dispositivo"],)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": "Heartbeat recibido correctamente",
        "token_sesion": str(updated["token_sesion"]),
        "id_sesion": updated["id_sesion"]
    }


def end_session(token_sesion: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM sesiones
        WHERE token_sesion = %s;
        """,
        (token_sesion,)
    )

    session = cursor.fetchone()

    if not session:
        cursor.close()
        conn.close()

        return {
            "success": False,
            "message": "La sesión no existe"
        }

    cursor.execute(
        """
        UPDATE sesiones
        SET estado_sesion = 'cerrada',
            fecha_fin = CURRENT_TIMESTAMP
        WHERE token_sesion = %s
        RETURNING *;
        """,
        (token_sesion,)
    )

    updated = cursor.fetchone()

    cursor.execute(
        """
        UPDATE dispositivos
        SET estado_dispositivo = 'desconectado',
            fecha_ultima = CURRENT_TIMESTAMP
        WHERE id_dispositivo = %s;
        """,
        (updated["id_dispositivo"],)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": "Sesión cerrada correctamente",
        "token_sesion": str(updated["token_sesion"]),
        "id_sesion": updated["id_sesion"]
    }