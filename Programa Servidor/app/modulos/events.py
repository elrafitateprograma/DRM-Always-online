from app.db import get_connection
from app.schemas.events import EventCreate


def get_session_by_id(id_sesion: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM sesiones
        WHERE id_sesion = %s;
        """,
        (id_sesion,)
    )

    session = cursor.fetchone()

    cursor.close()
    conn.close()

    return session


def create_event(data: EventCreate):
    session = get_session_by_id(data.id_sesion)

    if not session:
        return {
            "success": False,
            "message": "La sesión asociada al evento no existe"
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO eventos (
            tipo_evento,
            fecha,
            hora,
            descripcion,
            id_sesion
        )
        VALUES (%s, CURRENT_DATE, CURRENT_TIME, %s, %s)
        RETURNING *;
        """,
        (
            data.tipo_evento,
            data.descripcion,
            data.id_sesion
        )
    )

    event = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": "Evento registrado correctamente",
        "event": event
    }


def get_events_by_session(id_sesion: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM eventos
        WHERE id_sesion = %s
        ORDER BY fecha DESC, hora DESC;
        """,
        (id_sesion,)
    )

    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return events


def get_all_events():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM eventos
        ORDER BY fecha DESC, hora DESC;
        """
    )

    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return events