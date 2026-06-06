from fastapi import FastAPI, HTTPException

from app.db import test_connection
from app.schemas.users import UserRegister, UserLogin
from app.modulos.users import register_user, login_user
from app.schemas.licenses import LicenseActivate, LicenseRemove, LicenseStatusResponse, MessageResponse
from app.modulos.licenses import activate_license, remove_license, get_license_status
from app.schemas.devices import DeviceRegister
from app.modulos.devices import register_device, get_devices_by_user
from app.schemas.sesions import SessionStart, SessionHeartbeat, SessionEnd, SessionResponse
from app.modulos.sesions import start_session, heartbeat_session, end_session
from app.schemas.events import EventCreate
from app.modulos.events import create_event, get_events_by_session, get_all_events

app = FastAPI(
    title="Servidor DRM Always-Online",
    description="API del servidor DRM para gestión de usuarios, licencias, dispositivos y sesiones.",
    version="0.1.0"
)


@app.get("/")
def home():
    return {
        "mensaje": "Servidor DRM funcionando correctamente"
    }


@app.get("/health/db")
def check_database():
    if test_connection():
        return {
            "status": "ok",
            "database": "connected"
        }

    return {
        "status": "error",
        "database": "not connected"
    }


@app.post("/users/register")
def register(data: UserRegister):
    result = register_user(data)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


@app.post("/users/login")
def login(data: UserLogin):
    result = login_user(data)

    if not result["success"]:
        raise HTTPException(
            status_code=401,
            detail=result["message"]
        )

    return result


@app.post("/licenses/activate")
def activate(data: LicenseActivate):
    result = activate_license(data)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result

@app.post("/licenses/remove")
def remove(data: LicenseRemove):
    result = remove_license(data)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result

@app.get("/licenses/status/{id_usuario}", response_model=LicenseStatusResponse)
def get_status(id_usuario: int):
    result = get_license_status(id_usuario)

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

    if not result["has_license"]:
        return LicenseStatusResponse(
            has_license=False,
            message=result["message"]
        )

    license_data = result["license"]

    return LicenseStatusResponse(
        has_license=True,
        message=result["message"],
        id_licencia=license_data["id_licencia"],
        clave_licencia=license_data["clave_licencia"],
        clase_licencia=license_data["clase_licencia"],
        fecha_activacion=str(license_data["fecha_activacion"]) if license_data["fecha_activacion"] else None,
        fecha_caducidad=str(license_data["fecha_caducidad"]) if license_data["fecha_caducidad"] else None,
        estado_licencia=license_data["estado_licencia"],
        num_dispositivos=license_data["num_dispositivos"]
    )
    
    
@app.post("/devices/register")
def register_device_endpoint(data: DeviceRegister):
    result = register_device(data)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result

@app.get("/devices/{id_usuario}")
def get_devices(id_usuario: int):
    devices = get_devices_by_user(id_usuario)
    return {"devices": devices}


@app.post("/sesions/start", response_model=SessionResponse)
def start_session_endpoint(data: SessionStart):
    result = start_session(data.id_usuario, data.id_dispositivo)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return SessionResponse(**result)

@app.post("/sesions/heartbeat", response_model=SessionResponse)
def heartbeat_endpoint(data: SessionHeartbeat):
    result = heartbeat_session(data.token_sesion)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return SessionResponse(**result)


@app.post("/sesions/end", response_model=SessionResponse)
def end_session_endpoint(data: SessionEnd):
    result = end_session(data.token_sesion)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return SessionResponse(**result)


@app.post("/events/create")
def create_event_endpoint(data: EventCreate):
    result = create_event(data)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


@app.get("/events/session/{id_sesion}")
def get_events_session_endpoint(id_sesion: int):
    events = get_events_by_session(id_sesion)
    return {"events": events}


@app.get("/events")
def get_all_events_endpoint():
    events = get_all_events()
    return {"events": events}