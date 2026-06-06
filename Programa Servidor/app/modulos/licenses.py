from datetime import datetime
from app.db import get_connection
from app.schemas.licenses import LicenseActivate, LicenseRemove


def get_license_by_key(clave_licencia: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM licencias
        WHERE clave_licencia = %s;
        """,
        (clave_licencia,)
    )

    license_data = cursor.fetchone()

    cursor.close()
    conn.close()

    return license_data


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


def mark_license_as_expired(id_licencia: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE licencias
        SET estado_licencia = 'caducada'
        WHERE id_licencia = %s
        RETURNING *;
        """,
        (id_licencia,)
    )

    updated_license = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return updated_license


def is_license_expired(license_data) -> bool:
    return (
        license_data["fecha_caducidad"] is not None
        and license_data["fecha_caducidad"] < datetime.now()
    )


def activate_license(data: LicenseActivate):
    current_license = get_license_by_user(data.id_usuario)

    if current_license:
        if is_license_expired(current_license):
            mark_license_as_expired(current_license["id_licencia"])
            return {
                "success": False,
                "message": "Tu licencia actual está caducada. Primero debes eliminarla para introducir una nueva"
            }

        return {
            "success": False,
            "message": "Ya tienes una licencia válida. Si quieres introducir otra, primero debes borrarla"
        }

    license_data = get_license_by_key(data.clave_licencia)

    if not license_data:
        return {
            "success": False,
            "message": "La licencia introducida no existe"
        }

    if license_data["id_usuario"] is not None:
        return {
            "success": False,
            "message": "La licencia ya está asociada a otro usuario"
        }

    if license_data["estado_licencia"] == "revocada":
        return {
            "success": False,
            "message": "La licencia ha sido revocada"
        }

    if license_data["estado_licencia"] == "caducada":
        return {
            "success": False,
            "message": "La licencia está caducada"
        }

    if is_license_expired(license_data):
        mark_license_as_expired(license_data["id_licencia"])
        return {
            "success": False,
            "message": "La licencia ha superado su fecha de caducidad"
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE licencias
        SET id_usuario = %s,
            fecha_activacion = CURRENT_TIMESTAMP,
            estado_licencia = 'activa'
        WHERE id_licencia = %s
        RETURNING *;
        """,
        (data.id_usuario, license_data["id_licencia"])
    )

    updated_license = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": "Licencia activada correctamente",
        "license": updated_license
    }


def remove_license(data: LicenseRemove):
    license_data = get_license_by_user(data.id_usuario)

    if not license_data:
        return {
            "success": False,
            "message": "El usuario no tiene ninguna licencia asociada"
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE licencias
        SET id_usuario = NULL,
            fecha_activacion = NULL,
            estado_licencia = 'libre'
        WHERE id_licencia = %s
        RETURNING *;
        """,
        (license_data["id_licencia"],)
    )

    updated_license = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": "Licencia eliminada correctamente del usuario",
        "license": updated_license
    }


def get_license_status(id_usuario: int):
    license_data = get_license_by_user(id_usuario)

    if not license_data:
        return {
            "success": True,
            "has_license": False,
            "message": "El usuario no tiene ninguna licencia asociada"
        }

    if is_license_expired(license_data):
        license_data = mark_license_as_expired(license_data["id_licencia"])

        return {
            "success": True,
            "has_license": True,
            "message": "El usuario tiene una licencia, pero está caducada",
            "license": license_data
        }

    return {
        "success": True,
        "has_license": True,
        "message": "Licencia encontrada",
        "license": license_data
    }