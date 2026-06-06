import platform
import socket
import uuid
import hashlib
import requests

from config import SERVER_URL, REQUEST_TIMEOUT


class DRMClient:
    def __init__(self):
        self.user_id = None
        self.device_id = None
        self.session_token = None
        self.session_id = None
        self.fingerprint = self.generate_fingerprint()
        self.device_name = socket.gethostname()

    def generate_fingerprint(self) -> str:
        raw_data = "|".join([
            platform.system(),
            platform.release(),
            platform.machine(),
            platform.processor(),
            socket.gethostname(),
            str(uuid.getnode())
        ])

        return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
    def _extract_error(self, response) -> str:
        try:
            detail = response.json().get("detail", "ERR_UNKNOWN")
        except Exception:
            return "ERR_UNKNOWN"

        if isinstance(detail, str):
            return self._translate_error(detail)

        if isinstance(detail, list):
            messages = []

            for error in detail:
                loc = error.get("loc", [])
                msg = error.get("msg", "")
                field = loc[-1] if loc else ""

                if field == "email":
                    messages.append("El correo electrónico introducido no tiene un formato válido.")
                elif field == "username":
                    messages.append("El nombre de usuario debe tener al menos 6 caracteres.")
                elif field == "password":
                    messages.append("La contraseña debe tener al menos 6 caracteres.")
                elif field == "clave_licencia":
                    messages.append("La licencia debe tener el formato XXXX-XXXX usando caracteres hexadecimales.")
                else:
                    messages.append(msg)

            return " ".join(messages)

        return str(detail)


    def _translate_error(self, error: str) -> str:
        errors = {
            "El usuario no existe": "El usuario no existe.",
            "Contraseña incorrecta": "La contraseña introducida no es correcta.",
            "La cuenta no se encuentra activa": "La cuenta no se encuentra activa.",
            "El nombre de usuario ya existe": "El nombre de usuario ya existe.",
            "El email ya está registrado": "El correo electrónico ya está registrado.",
            "ERR_SERVER_UNAVAILABLE": "No se puede conectar con el servidor DRM.",
            "ERR_SERVER_TIMEOUT": "El servidor DRM no respondió a tiempo."
        }

        return errors.get(error, error)

    def _post(self, endpoint: str, data: dict):
        try:
            response = requests.post(
                f"{SERVER_URL}{endpoint}",
                json=data,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code >= 400:
                return {
                    "success": False,
                    "error": self._extract_error(response)
                }

            return response.json()

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "ERR_SERVER_UNAVAILABLE"
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "ERR_SERVER_TIMEOUT"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"ERR_UNKNOWN: {e}"
            }

    def _get(self, endpoint: str):
        try:
            response = requests.get(
                f"{SERVER_URL}{endpoint}",
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code >= 400:
                return {
                    "success": False,
                    "error": self._extract_error(response)
                }

            return response.json()

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "ERR_SERVER_UNAVAILABLE"
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "ERR_SERVER_TIMEOUT"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"ERR_UNKNOWN: {e}"
            }

    def register_user(self, username: str, email: str, password: str):
        return self._post("/users/register", {
            "username": username,
            "email": email,
            "password": password
        })

    def login(self, username: str, password: str):
        self.user_id = None
        self.device_id = None
        self.session_token = None
        self.session_id = None

        result = self._post("/users/login", {
            "username": username,
            "password": password
        })

        if result.get("success"):
            self.user_id = result["user"]["id_usuario"]

        return result

    def activate_license(self, license_key: str):
        if not self.user_id:
            return {"success": False, "error": "ERR_USER_NOT_LOGGED"}

        return self._post("/licenses/activate", {
            "id_usuario": self.user_id,
            "clave_licencia": license_key
        })

    def remove_license(self):
        if not self.user_id:
            return {"success": False, "error": "ERR_USER_NOT_LOGGED"}

        return self._post("/licenses/remove", {
            "id_usuario": self.user_id
        })

    def get_license_status(self):
        if not self.user_id:
            return {"success": False, "error": "ERR_USER_NOT_LOGGED"}

        return self._get(f"/licenses/status/{self.user_id}")

    def register_device(self):
        if not self.user_id:
            return {"success": False, "error": "ERR_USER_NOT_LOGGED"}

        result = self._post("/devices/register", {
            "id_usuario": self.user_id,
            "fingerprint": self.fingerprint,
            "nombre": self.device_name
        })

        if result.get("success"):
            self.device_id = result["device"]["id_dispositivo"]

        return result

    def start_session(self):
        if not self.user_id:
            return {"success": False, "error": "ERR_USER_NOT_LOGGED"}

        if not self.device_id:
            return {"success": False, "error": "ERR_DEVICE_NOT_REGISTERED"}

        result = self._post("/sesions/start", {
            "id_usuario": self.user_id,
            "id_dispositivo": self.device_id
        })

        if result.get("success"):
            self.session_token = result["token_sesion"]
            self.session_id = result["id_sesion"]

        return result

    def heartbeat(self):
        if not self.session_token:
            return {"success": False, "error": "ERR_NO_ACTIVE_SESSION"}

        return self._post("/sesions/heartbeat", {
            "token_sesion": self.session_token
        })

    def end_session(self):
        if not self.session_token:
            return {"success": False, "error": "ERR_NO_ACTIVE_SESSION"}

        result = self._post("/sesions/end", {
            "token_sesion": self.session_token
        })

        if result.get("success"):
            self.session_token = None
            self.session_id = None

        return result

    def send_event(self, tipo_evento: str, descripcion: str):
        if not self.session_id:
            return {"success": False, "error": "ERR_NO_ACTIVE_SESSION"}

        return self._post("/events/create", {
            "tipo_evento": tipo_evento,
            "descripcion": descripcion,
            "id_sesion": self.session_id
        })