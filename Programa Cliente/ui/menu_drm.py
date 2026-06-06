import pygame
from enum import Enum, auto
from typing import Optional, Callable

WINDOW_WIDTH = 720
WINDOW_HEIGHT = 520
FPS = 30

BLACK = (18, 18, 18)
DARK_GRAY = (35, 35, 35)
LIGHT_GRAY = (80, 80, 80)
WHITE = (240, 240, 240)
YELLOW = (245, 220, 110)
BLUE = (90, 140, 220)
RED = (220, 70, 70)
GREEN = (70, 200, 110)


class MenuState(Enum):
    START = auto()
    LOGIN = auto()
    REGISTER = auto()
    MAIN = auto()
    LICENSE = auto()
    LICENSE_STATUS = auto()
    MESSAGE = auto()


class TextInput:
    def __init__(self, x: int, y: int, w: int, h: int, label: str, password: bool = False):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.text = ""
        self.active = False
        self.password = password
        

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            else:
                if len(self.text) < 128 and event.unicode:
                    self.text += event.unicode

    def draw(self, screen: pygame.Surface, font_label: pygame.font.Font, font_text: pygame.font.Font) -> None:
        label_surface = font_label.render(self.label, True, WHITE)
        screen.blit(label_surface, (self.rect.x, self.rect.y - 26))

        border_color = YELLOW if self.active else WHITE
        pygame.draw.rect(screen, DARK_GRAY, self.rect, border_radius=8)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=8)

        visible_text = "*" * len(self.text) if self.password else self.text
        text_surface = font_text.render(visible_text, True, WHITE)
        screen.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))

    def clear(self) -> None:
        self.text = ""
        self.active = False


class Button:
    def __init__(self, x: int, y: int, w: int, h: int, text: str, action: Callable[[], None]):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.action()

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)
        color = BLUE if hovered else DARK_GRAY

        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=12)

        text_surface = font.render(self.text, True, YELLOW if hovered else WHITE)
        screen.blit(text_surface, text_surface.get_rect(center=self.rect.center))


class DRMMenuPygame:
    def __init__(self, drm_client):
        pygame.init()
        pygame.display.set_caption("DRM Always-Online")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.cached_license_status = None
        self.font_title = pygame.font.SysFont("Arial", 34, bold=True)
        self.font_button = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 18)
        self.font_text = pygame.font.SysFont("Arial", 20)

        self.drm_client = drm_client
        self.state = MenuState.START
        self.running = True
        self.result: Optional[str] = None
        self.message_return_state = MenuState.MAIN
        self.message_title = ""
        self.message_body = ""
        self.message_is_error = False

        self.login_user = TextInput(210, 170, 300, 42, "Usuario")
        self.login_password = TextInput(210, 250, 300, 42, "Contraseña", password=True)

        self.register_user = TextInput(210, 135, 300, 42, "Usuario")
        self.register_email = TextInput(210, 215, 300, 42, "Email")
        self.register_password = TextInput(210, 295, 300, 42, "Contraseña", password=True)

        self.license_key = TextInput(210, 205, 300, 42, "Licencia (XXXX-XXXX)")

    def run(self) -> Optional[str]:
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        return self.result

    def set_message(self, title: str, body: str, is_error: bool = False, return_state=None) -> None:
        self.message_title = title
        self.message_body = body
        self.message_is_error = is_error
        self.message_return_state = return_state or MenuState.MAIN
        self.state = MenuState.MESSAGE

    def back_to_start(self) -> None:
        self.clear_inputs()
        self.cached_license_status = None
        self.state = MenuState.START
        
    def refresh_license_status(self):
        self.cached_license_status = self.drm_client.get_license_status()


    def open_license_menu(self):
        self.refresh_license_status()
        self.change_state(MenuState.LICENSE)

    def back_to_main(self) -> None:
        self.clear_inputs()
        self.state = MenuState.MAIN

    def clear_inputs(self) -> None:
        for field in [
            self.login_user,
            self.login_password,
            self.register_user,
            self.register_email,
            self.register_password,
            self.license_key,
        ]:
            field.clear()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.result = "EXIT"
                return

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.state in (MenuState.LOGIN, MenuState.REGISTER):
                    self.back_to_start()
                elif self.state in (MenuState.LICENSE, MenuState.LICENSE_STATUS, MenuState.MESSAGE):
                    if self.drm_client.user_id:
                        self.back_to_main()
                    else:
                        self.back_to_start()
                elif self.state == MenuState.MAIN:
                    self.back_to_start()
                continue

            self.dispatch_event(event)

    def dispatch_event(self, event: pygame.event.Event) -> None:
        if self.state == MenuState.START:
            self.start_buttons(event)
        elif self.state == MenuState.LOGIN:
            self.login_user.handle_event(event)
            self.login_password.handle_event(event)
            self.login_buttons(event)
        elif self.state == MenuState.REGISTER:
            self.register_user.handle_event(event)
            self.register_email.handle_event(event)
            self.register_password.handle_event(event)
            self.register_buttons(event)
        elif self.state == MenuState.MAIN:
            self.main_buttons(event)
        elif self.state == MenuState.LICENSE:
            self.license_key.handle_event(event)
            self.license_buttons(event)
        elif self.state == MenuState.LICENSE_STATUS:
            self.status_buttons(event)
        elif self.state == MenuState.MESSAGE:
            self.message_buttons(event)

    def start_buttons(self, event: pygame.event.Event) -> None:
        buttons = [
            Button(240, 175, 240, 50, "Iniciar sesión", lambda: self.change_state(MenuState.LOGIN)),
            Button(240, 245, 240, 50, "Registrar usuario", lambda: self.change_state(MenuState.REGISTER)),
            Button(240, 315, 240, 50, "Salir", self.exit_app),
        ]
        for button in buttons:
            button.handle_event(event)

    def login_buttons(self, event: pygame.event.Event) -> None:
        buttons = [
            Button(210, 330, 140, 48, "Entrar", self.do_login),
            Button(370, 330, 140, 48, "Volver", self.back_to_start),
        ]
        for button in buttons:
            button.handle_event(event)

    def register_buttons(self, event: pygame.event.Event) -> None:
        buttons = [
            Button(210, 380, 140, 48, "Registrar", self.do_register),
            Button(370, 380, 140, 48, "Volver", self.back_to_start),
        ]
        for button in buttons:
            button.handle_event(event)

    def main_buttons(self, event: pygame.event.Event) -> None:
        buttons = [
            Button(220, 145, 280, 48, "Usar producto", self.play_product),
            Button(220, 210, 280, 48, "Gestionar licencia", self.open_license_menu),
            Button(220, 275, 280, 48, "Estado de licencia", self.show_license_status),
            Button(220, 340, 280, 48, "Cerrar sesión", self.logout),
        ]
        for button in buttons:
            button.handle_event(event)

    def license_buttons(self, event: pygame.event.Event) -> None:
        buttons = [
            Button(135, 330, 200, 48, "Activar", self.do_activate_license),
            Button(365, 330, 200, 48, "Eliminar", self.do_remove_license),
            Button(260, 400, 200, 48, "Volver", self.back_to_main),
        ]
        for button in buttons:
            button.handle_event(event)

    def status_buttons(self, event: pygame.event.Event) -> None:
        Button(260, 405, 200, 48, "Volver", self.back_to_main).handle_event(event)

    def message_buttons(self, event: pygame.event.Event) -> None:
        Button(
            260, 380, 200, 48,
            "Aceptar",
            lambda: self.change_state(self.message_return_state)
        ).handle_event(event)
        
        
    def change_state(self, state: MenuState) -> None:
        self.clear_inputs()
        self.state = state

    def exit_app(self) -> None:
        self.result = "EXIT"
        self.running = False

    def logout(self) -> None:
        self.drm_client.user_id = None
        self.drm_client.device_id = None
        self.drm_client.session_token = None
        self.drm_client.session_id = None
        self.cached_license_status = None
        self.back_to_start()

    def play_product(self) -> None:
        self.result = "PLAY"
        self.running = False

    def do_login(self) -> None:
        result = self.drm_client.login(self.login_user.text, self.login_password.text)

        self.cached_license_status = None

        if result.get("success"):
            self.refresh_license_status()
            self.set_message(
                "Acceso correcto",
                "Usuario autenticado correctamente",
                return_state=MenuState.MAIN
            )
        else:
            self.set_message(
                "Error de acceso",
                result.get("error", "Credenciales incorrectas"),
                True,
                return_state=MenuState.LOGIN
            )
    def do_register(self) -> None:
        result = self.drm_client.register_user(
            self.register_user.text,
            self.register_email.text,
            self.register_password.text,
        )

        self.cached_license_status = None

        if result.get("success"):
            self.set_message(
                "Registro correcto",
                "Usuario registrado correctamente",
                return_state=MenuState.START
            )
        else:
            self.set_message(
                "Error de registro",
                result.get("error", "No se pudo registrar el usuario"),
                True,
                return_state=MenuState.REGISTER
            ) 
            
    def do_activate_license(self) -> None:
        result = self.drm_client.activate_license(self.license_key.text)

        if result.get("success"):
            self.refresh_license_status()
            self.set_message(
                "Licencia activada",
                "La licencia se ha asociado correctamente",
                return_state=MenuState.LICENSE
            )
        else:
            self.set_message(
                "Error de licencia",
                result.get("error", "No se pudo activar la licencia"),
                True,
                return_state=MenuState.LICENSE
            )
        
    def do_remove_license(self) -> None:
        result = self.drm_client.remove_license()

        if result.get("success"):
            self.refresh_license_status()
            self.set_message(
                "Licencia eliminada",
                "La licencia ha quedado libre",
                return_state=MenuState.LICENSE
            )
        else:
            self.set_message(
                "Error de licencia",
                result.get("error", "No se pudo eliminar la licencia"),
                True,
                return_state=MenuState.LICENSE
            )
            
    def show_license_status(self) -> None:
        self.license_status = self.drm_client.get_license_status()
        self.state = MenuState.LICENSE_STATUS

    def draw(self) -> None:
        self.screen.fill(BLACK)

        if self.state == MenuState.START:
            self.draw_start()
        elif self.state == MenuState.LOGIN:
            self.draw_login()
        elif self.state == MenuState.REGISTER:
            self.draw_register()
        elif self.state == MenuState.MAIN:
            self.draw_main()
        elif self.state == MenuState.LICENSE:
            self.draw_license()
        elif self.state == MenuState.LICENSE_STATUS:
            self.draw_license_status()
        elif self.state == MenuState.MESSAGE:
            self.draw_message()

        pygame.display.flip()

    def draw_title(self, title: str, subtitle: str = "") -> None:
        title_surface = self.font_title.render(title, True, GREEN)
        self.screen.blit(title_surface, title_surface.get_rect(center=(WINDOW_WIDTH // 2, 70)))
        if subtitle:
            subtitle_surface = self.font_label.render(subtitle, True, WHITE)
            self.screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, 105)))

    def draw_start(self) -> None:
        self.draw_title("DRM ALWAYS-ONLINE", "Cliente de autenticación y licencias")
        for button in [
            Button(240, 175, 240, 50, "Iniciar sesión", lambda: None),
            Button(240, 245, 240, 50, "Registrar usuario", lambda: None),
            Button(240, 315, 240, 50, "Salir", lambda: None),
        ]:
            button.draw(self.screen, self.font_button)

    def draw_login(self) -> None:
        self.draw_title("INICIAR SESIÓN")
        self.login_user.draw(self.screen, self.font_label, self.font_text)
        self.login_password.draw(self.screen, self.font_label, self.font_text)
        for button in [
            Button(210, 330, 140, 48, "Entrar", lambda: None),
            Button(370, 330, 140, 48, "Volver", lambda: None),
        ]:
            button.draw(self.screen, self.font_button)

    def draw_register(self) -> None:
        self.draw_title("REGISTRAR USUARIO")
        self.register_user.draw(self.screen, self.font_label, self.font_text)
        self.register_email.draw(self.screen, self.font_label, self.font_text)
        self.register_password.draw(self.screen, self.font_label, self.font_text)
        for button in [
            Button(210, 380, 140, 48, "Registrar", lambda: None),
            Button(370, 380, 140, 48, "Volver", lambda: None),
        ]:
            button.draw(self.screen, self.font_button)

    def draw_main(self) -> None:
        self.draw_title("MENÚ DRM", "Gestión del producto protegido")
        for button in [
            Button(220, 145, 280, 48, "Usar producto", lambda: None),
            Button(220, 210, 280, 48, "Gestionar licencia", lambda: None),
            Button(220, 275, 280, 48, "Estado de licencia", lambda: None),
            Button(220, 340, 280, 48, "Cerrar sesión", lambda: None),
        ]:
            button.draw(self.screen, self.font_button)

    def draw_license(self) -> None:
        self.draw_title("GESTIÓN DE LICENCIA")

        status = self.cached_license_status or {}

        box_rect = pygame.Rect(120, 125, 480, 70)
        pygame.draw.rect(self.screen, DARK_GRAY, box_rect, border_radius=12)
        pygame.draw.rect(self.screen, WHITE, box_rect, 2, border_radius=12)

        if status.get("error") or not status.get("has_license"):
            text = "SIN LICENCIA"
            color = RED
        else:
            text = f"Licencia actual: {status.get('clave_licencia')} | Estado: {status.get('estado_licencia')}"
            color = GREEN

        text_surface = self.font_text.render(text, True, color)
        self.screen.blit(text_surface, text_surface.get_rect(center=box_rect.center))
        
        self.license_key.rect.x = 210
        self.license_key.rect.y = 245
        self.license_key.draw(self.screen, self.font_label, self.font_text)


        for button in [
            Button(135, 330, 200, 48, "Activar", lambda: None),
            Button(365, 330, 200, 48, "Eliminar", lambda: None),
            Button(260, 400, 200, 48, "Volver", lambda: None),
        ]:
            button.draw(self.screen, self.font_button)
            
            
    def draw_license_status(self) -> None:
            self.draw_title("ESTADO DE LICENCIA")
            status = getattr(self, "license_status", {})

            lines = []
            if status.get("error"):
                lines.append(f"Error: {status.get('error')}")
            elif not status.get("has_license"):
                lines.append("El usuario no tiene licencia asociada")
            else:
                lines.extend([
                    f"Clave: {status.get('clave_licencia')}",
                    f"Clase: {status.get('clase_licencia')}",
                    f"Estado: {status.get('estado_licencia')}",
                    f"Activación: {status.get('fecha_activacion')}",
                    f"Caducidad: {status.get('fecha_caducidad')}",
                    f"Dispositivos permitidos: {status.get('num_dispositivos')}",
                ])

            y = 145
            for line in lines:
                surface = self.font_text.render(line, True, WHITE)
                self.screen.blit(surface, (120, y))
                y += 34

            Button(260, 405, 200, 48, "Volver", lambda: None).draw(self.screen, self.font_button)

    def draw_wrapped_text(self, text: str, color, center_x: int, start_y: int, max_width: int, line_height: int = 28):
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if self.font_text.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        for i, line in enumerate(lines):
            surface = self.font_text.render(line, True, color)
            rect = surface.get_rect(center=(center_x, start_y + i * line_height))
            self.screen.blit(surface, rect)
    
    def draw_message(self) -> None:
        
        color = RED if self.message_is_error else GREEN

        self.draw_title(self.message_title)

        box_rect = pygame.Rect(70, 170, WINDOW_WIDTH - 140, 170)
        pygame.draw.rect(self.screen, DARK_GRAY, box_rect, border_radius=14)
        pygame.draw.rect(self.screen, WHITE, box_rect, 2, border_radius=14)

        self.draw_wrapped_text(
            self.message_body,
            color,
            WINDOW_WIDTH // 2,
            210,
            WINDOW_WIDTH - 180
        )

        Button(260, 380, 200, 48, "Aceptar", lambda: None).draw(self.screen, self.font_button)