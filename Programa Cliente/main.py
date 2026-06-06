from cliente_drm import DRMClient
from cliente_heartbeat import HeartbeatManager
from config import HEARTBEAT_INTERVAL
from ui.menu_drm import DRMMenuPygame
from juego import SnakeGame


def translate_error(error: str) -> str:
    errors = {
        "El usuario no tiene una licencia asociada": "No existe una licencia activa asociada a este usuario.",
        "La licencia no está activa": "La licencia asociada no se encuentra activa.",
        "La licencia está caducada": "La licencia ha caducado. Renueva o introduce una licencia válida.",
        "La licencia ha sido revocada": "La licencia ha sido revocada.",
        "Se ha alcanzado el número máximo de dispositivos simultáneos": "Se ha alcanzado el número máximo de dispositivos permitidos para esta licencia.",
        "El dispositivo no existe": "El dispositivo no está registrado correctamente.",
        "El dispositivo no pertenece al usuario": "El dispositivo no pertenece al usuario autenticado.",
        "El dispositivo se encuentra bloqueado": "Este dispositivo se encuentra bloqueado.",
        "ERR_SERVER_UNAVAILABLE": "No se puede conectar con el servidor DRM.",
        "ERR_SERVER_TIMEOUT": "El servidor DRM no respondió a tiempo.",
        "ERR_DEVICE_NOT_REGISTERED": "El dispositivo no ha sido registrado correctamente.",
        "ERR_USER_NOT_LOGGED": "No hay ningún usuario autenticado.",
        "ERR_LICENSE_EXPIRED": "La licencia ha caducado durante la ejecución del producto.",
        "ERR_LICENSE_NOT_ACTIVE": "La licencia asociada ya no se encuentra activa.",
        "ERR_SESSION_NOT_ACTIVE": "La sesión DRM ya no se encuentra activa.",
        "ERR_SESSION_NOT_FOUND": "La sesión DRM no existe.",
    }

    return errors.get(error, error)

from datetime import datetime


def format_license_expiration(drm_client: DRMClient) -> str:
    status = drm_client.get_license_status()

    if status.get("error") or not status.get("has_license"):
        return "Licencia no disponible"

    fecha_caducidad = status.get("fecha_caducidad")

    if not fecha_caducidad:
        return "Licencia sin fecha de caducidad"

    try:
        expiration_date = datetime.fromisoformat(str(fecha_caducidad))
    except ValueError:
        return f"Caduca el: {fecha_caducidad}"

    remaining = expiration_date - datetime.now()

    if remaining.total_seconds() <= 0:
        return "La licencia está caducada"

    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60

    if days > 0:
        return f"La licencia caduca en {days} días, {hours} horas y {minutes} minutos"

    if hours > 0:
        return f"La licencia caduca en {hours} horas y {minutes} minutos"

    return f"La licencia caduca en {minutes} minutos"

def show_drm_error(drm_client: DRMClient, title: str, message: str):
    menu = DRMMenuPygame(drm_client)
    menu.set_message(title, message, is_error=True)
    menu.run()


def run_game_with_drm(drm_client: DRMClient):
    device_result = drm_client.register_device()

    if not device_result.get("success"):
        show_drm_error(
            drm_client,
            "Error de dispositivo",
            translate_error(device_result.get("error", "No se pudo registrar el dispositivo"))
        )
        return True

    session_result = drm_client.start_session()

    if not session_result.get("success"):
        show_drm_error(
            drm_client,
            "Error al iniciar el producto",
            translate_error(session_result.get("error", "No se pudo crear una sesión DRM"))
        )
        return True

    game_holder = {"game": None}

    def on_heartbeat_failure(error_code):
        game = game_holder.get("game")

        drm_client.send_event(
            "HEARTBEAT_ERROR",
            f"Fallo de heartbeat: {error_code}"
        )

        if game:
            game.force_close_by_drm(
                error_code,
                translate_error(error_code)
            )

    heartbeat = HeartbeatManager(
        drm_client=drm_client,
        interval=HEARTBEAT_INTERVAL
    )

    license_expiration_text = format_license_expiration(drm_client)
    game = SnakeGame(license_expiration_text=license_expiration_text)
    game_holder["game"] = game

    drm_client.send_event(
        "GAME_START",
        "El usuario ha iniciado el producto protegido"
    )

    heartbeat.start(on_heartbeat_failure)

    return_to_drm = game.run()

    heartbeat.stop()

    drm_client.send_event(
        "GAME_END",
        "El usuario ha cerrado el producto protegido"
    )

    drm_client.end_session()

    return return_to_drm


def main():
    drm_client = DRMClient()

    while True:
        menu = DRMMenuPygame(drm_client)
        result = menu.run()

        if result == "EXIT":
            break

        if result == "PLAY":
            return_to_drm = run_game_with_drm(drm_client)

            if not return_to_drm:
                break


if __name__ == "__main__":
    main()