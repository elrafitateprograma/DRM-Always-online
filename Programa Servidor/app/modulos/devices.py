from app.db import get_connection
from app.schemas.devices import DeviceRegister


def get_device_by_fingerprint_and_user(fingerprint: str, id_usuario: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM dispositivos
        WHERE fingerprint = %s
          AND id_usuario = %s;
        """,
        (fingerprint, id_usuario)
    )

    device = cursor.fetchone()

    cursor.close()
    conn.close()

    return device


def register_device(data: DeviceRegister):
    existing_device = get_device_by_fingerprint_and_user(
        data.fingerprint,
        data.id_usuario
    )

    if existing_device:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE dispositivos
            SET fecha_ultima = CURRENT_TIMESTAMP,
                estado_dispositivo = 'conectado',
                nombre = %s
            WHERE id_dispositivo = %s
            RETURNING *;
            """,
            (data.nombre, existing_device["id_dispositivo"])
        )

        updated = cursor.fetchone()

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "success": True,
            "message": "Dispositivo actualizado",
            "device": updated
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO dispositivos (
            fingerprint,
            nombre,
            fecha_registro,
            fecha_ultima,
            estado_dispositivo,
            id_usuario
        )
        VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, %s)
        RETURNING *;
        """,
        (data.fingerprint, data.nombre, "conectado", data.id_usuario)
    )

    new_device = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": "Dispositivo registrado",
        "device": new_device
    }


def get_devices_by_user(id_usuario: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM dispositivos
        WHERE id_usuario = %s
        ORDER BY fecha_ultima DESC NULLS LAST;
        """,
        (id_usuario,)
    )

    devices = cursor.fetchall()

    cursor.close()
    conn.close()

    return devices