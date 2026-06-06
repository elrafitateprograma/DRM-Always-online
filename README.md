# DRM Always-Online

## Description

DRM Always-Online is an academic Digital Rights Management (DRM) prototype developed for educational and research purposes.

The project implements a client-server architecture capable of controlling access to a protected application through user authentication, license management, device registration, session control, and continuous validation using a heartbeat mechanism.

Unlike commercial DRM solutions, this project does not aim to provide industrial-grade protection against advanced reverse engineering. Instead, its goal is to offer an open and understandable implementation that allows students, researchers, and developers to study the internal operation of modern DRM systems.

The system includes a Snake game developed with Pygame, which serves as a protected demonstration application.

---

## Main Features

* User registration and authentication.
* Software license management.
* License activation and removal.
* License association with user accounts.
* Automatic device registration through fingerprinting.
* Simultaneous device control per license.
* Authenticated session management.
* Periodic heartbeat system.
* Dynamic session revocation.
* Automatic license expiration handling.
* Event logging and auditing.
* REST API based on FastAPI.
* PostgreSQL persistence layer.
* Graphical client developed with Pygame.

---

## Architecture

The system is divided into three main components:

### DRM Client

Responsible for:

* User authentication.
* License management.
* Communication with the server.
* Device fingerprint generation.
* Session management.
* Periodic heartbeat transmission.
* Execution of the protected application.

### DRM Server

Responsible for:

* User validation.
* License management.
* Device management.
* Session management.
* Heartbeat validation.
* Event logging.
* Enforcement of business rules.

### PostgreSQL Database

Stores:

* Users.
* Licenses.
* Devices.
* Sessions.
* Events.

---

## Technologies Used

### Backend

* Python 3.12
* FastAPI
* Uvicorn
* PostgreSQL
* Psycopg2

### Client

* Python 3.12
* Pygame
* Requests

### Security

* bcrypt
* SHA-256

### Additional Libraries

* Pydantic
* python-dotenv
* UUID

---

## Prerequisites

Before installing the project, make sure you have:

* Python 3.12 or later
* PostgreSQL 15 or later
* Git
* Pip

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure PostgreSQL

Create a PostgreSQL database and import the SQL scripts included in the project.

Then configure the database credentials in the:

```text
.env
```

file.

Example:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=drm_db
DB_USER=postgres
DB_PASSWORD=your_password
```

### 6. Start the Server

From the server directory:

```bash
uvicorn app.main:app --reload
```

The server will be available at:

```text
http://127.0.0.1:8000
```

### 7. Run the Client

```bash
python main.py
```

---

## Integrating the DRM into Another Application

The DRM has been designed to be integrated into virtually any Python-based application. This proyect have two modules (juego.py and menu drm.py) which are considered as testing.
The idea is that you integrate your own software with the rest of the DRM so your app get the full protection seeked. In other words, you could delete this two modules if you want.
In juego.py there's a snake type videogame which has been used to test if the DRM work as planned. In Menu DRM.py there's the full frontend of the application made with pygame, however this UI is basic, therefore you can develop a better version of it.

To protect an existing application, the following components must be added:

### 1. Initialize the DRM Client

When the application starts:

```python
drm_client = DRMClient()
```

### 2. Display the DRM Menu

Before allowing access to the protected application:

```python
menu = DRMMenuPygame(drm_client)
result = menu.run()
```

The user must:

* Register or log in.
* Activate a valid license.
* Obtain a valid DRM session.

### 3. Start the Heartbeat Manager

Once the session has been validated:

```python
heartbeat_manager.start()
```

The heartbeat mechanism will maintain periodic communication with the server.

### 4. Handle DRM Errors

The protected application should react appropriately to:

* Expired licenses.
* Revoked licenses.
* Invalid sessions.
* Server outages.
* Unauthorized devices.

In any of these situations, the application should either terminate or return the user to the DRM menu.

---

## Demonstration Application

The repository includes a DRM-protected Snake game.

Its purpose is to demonstrate how the DRM can be integrated into a real application and to provide a testing environment for validating licenses, devices, sessions, and heartbeat functionality.

---

## Limitations

This project was developed for academic purposes.

It does not include several advanced techniques commonly found in commercial DRM solutions, such as:

* Code obfuscation.
* Anti-debugging techniques.
* Anti-tampering protections.
* Code virtualization.
* Runtime executable encryption.
* Advanced reverse engineering protection.

Therefore, it should not be considered a production-ready commercial DRM solution.

---

## Future Work

Potential future developments include:

* Runtime executable encryption.
* Anti-debugging mechanisms.
* Advanced code obfuscation.
* Distributed license revocation systems.
* Multi-product support.
* Web-based administration panel.
* Monitoring and analytics.
* Integration with subscription and payment systems.

---

## License

This project is distributed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

Users are free to use, modify, distribute, and commercially exploit the software, provided that proper credit is given to the original author.

---

## Author

Rafael Becerra Villalobos

Bachelor's Degree Final Project — Computer Engineering

University of Cádiz (UCA)
