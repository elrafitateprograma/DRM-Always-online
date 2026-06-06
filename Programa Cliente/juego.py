import pygame
import random
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Callable

# --- Configuración general ---
GRID_SIZE = 8
CELL_SIZE = 64
BOARD_SIZE = GRID_SIZE * CELL_SIZE
FPS = 3
WINDOW_WIDTH = BOARD_SIZE
WINDOW_HEIGHT = BOARD_SIZE + 120

# Colores
BLACK = (18, 18, 18)
DARK_GRAY = (35, 35, 35)
LIGHT_GRAY = (70, 70, 70)
WHITE = (240, 240, 240)
GREEN = (70, 200, 110)
GREEN_HEAD = (110, 235, 145)
RED = (220, 70, 70)
YELLOW = (245, 220, 110)
BLUE = (90, 140, 220)


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    WIN = auto()
    LOSE = auto()
    DRM_ERROR = auto()


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def vector(self):
        return self.value


@dataclass(frozen=True)
class Position:
    x: int
    y: int

    def moved(self, direction: Direction) -> "Position":
        dx, dy = direction.vector
        return Position(self.x + dx, self.y + dy)


class SnakeGame:
    def __init__( self, on_return_to_drm: Optional[Callable[[], None]] = None, license_expiration_text: str = "Caducidad de licencia no disponible") -> None:
        pygame.init()
        pygame.display.set_caption("Snake DRM")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("Arial", 34, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)

        
        self.on_return_to_drm = on_return_to_drm
        self.license_expiration_text = license_expiration_text
        self.state = GameState.MENU
        self.running = True
        self.return_to_drm_requested = False
        self.menu_index = 0
        self.menu_options = ["Iniciar juego", "Volver al menú DRM"]

        self.snake: list[Position] = []
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.apple = Position(0, 0)
        self.score = 0

        self.drm_error_code = ""
        self.drm_error_message = ""

        self.reset_game()

    def reset_game(self) -> None:
        center = GRID_SIZE // 2
        self.snake = [Position(center, center)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.score = 0
        self.apple = self.spawn_apple()

    def spawn_apple(self) -> Position:
        free_positions = [
            Position(x, y)
            for x in range(GRID_SIZE)
            for y in range(GRID_SIZE)
            if Position(x, y) not in self.snake
        ]
        return random.choice(free_positions)

    def force_close_by_drm(self, error_code: str, message: str = "La sesión DRM ha dejado de ser válida") -> None:
        
        self.drm_error_code = error_code
        self.drm_error_message = message
        self.state = GameState.DRM_ERROR

    def request_return_to_drm(self) -> None:
       
        self.return_to_drm_requested = True
        self.running = False
        if self.on_return_to_drm:
            self.on_return_to_drm()

    def handle_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type != pygame.KEYDOWN:
                continue

            if self.state == GameState.MENU:
                self.handle_menu_input(event.key)
            elif self.state == GameState.PLAYING:
                self.handle_playing_input(event.key)
            elif self.state in (GameState.WIN, GameState.LOSE, GameState.DRM_ERROR):
                self.handle_end_input(event.key)

    def handle_menu_input(self, key: int) -> None:
        if key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % len(self.menu_options)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % len(self.menu_options)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.menu_index == 0:
                self.reset_game()
                self.state = GameState.PLAYING
            else:
                self.request_return_to_drm()

    def handle_playing_input(self, key: int) -> None:
        opposite = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }

        new_direction = None
        if key in (pygame.K_UP, pygame.K_w):
            new_direction = Direction.UP
        elif key in (pygame.K_DOWN, pygame.K_s):
            new_direction = Direction.DOWN
        elif key in (pygame.K_LEFT, pygame.K_a):
            new_direction = Direction.LEFT
        elif key in (pygame.K_RIGHT, pygame.K_d):
            new_direction = Direction.RIGHT
        elif key == pygame.K_ESCAPE:
            self.state = GameState.MENU
            return

        if new_direction and len(self.snake) == 1:
            self.next_direction = new_direction
        elif new_direction and new_direction != opposite[self.direction]:
            self.next_direction = new_direction

    def handle_end_input(self, key: int) -> None:
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            self.state = GameState.MENU
        elif key == pygame.K_ESCAPE:
            self.request_return_to_drm()

    def update(self) -> None:
        if self.state != GameState.PLAYING:
            return

        self.direction = self.next_direction
        new_head = self.snake[0].moved(self.direction)

       
        if not (0 <= new_head.x < GRID_SIZE and 0 <= new_head.y < GRID_SIZE):
            self.state = GameState.LOSE
            return

        
        if new_head in self.snake:
            self.state = GameState.LOSE
            return

        self.snake.insert(0, new_head)

        
        if new_head == self.apple:
            self.score += 1
            if len(self.snake) == GRID_SIZE * GRID_SIZE:
                self.state = GameState.WIN
                return
            self.apple = self.spawn_apple()
        else:
            self.snake.pop()

    def draw(self) -> None:
        self.screen.fill(BLACK)

        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_board()
            self.draw_status_bar("Juego en curso")
        elif self.state == GameState.WIN:
            self.draw_board()
            self.draw_overlay("Has ganado", "Pulsa ENTER para volver al menú")
        elif self.state == GameState.LOSE:
            self.draw_board()
            self.draw_overlay("Has perdido", "Pulsa ENTER para volver al menú")
        elif self.state == GameState.DRM_ERROR:
            self.draw_board()
            self.draw_overlay(
                "Error DRM",
                "Pulsa ESC para volver al menú DRM"
                )

        pygame.display.flip()

    def draw_board(self) -> None:
        board_rect = pygame.Rect(0, 0, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(self.screen, DARK_GRAY, board_rect)

        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, LIGHT_GRAY, rect, 1)

        
        apple_rect = pygame.Rect(
            self.apple.x * CELL_SIZE + 12,
            self.apple.y * CELL_SIZE + 12,
            CELL_SIZE - 24,
            CELL_SIZE - 24,
        )
        pygame.draw.ellipse(self.screen, RED, apple_rect)

        
        for index, segment in enumerate(self.snake):
            padding = 8
            rect = pygame.Rect(
                segment.x * CELL_SIZE + padding,
                segment.y * CELL_SIZE + padding,
                CELL_SIZE - padding * 2,
                CELL_SIZE - padding * 2,
            )
            color = GREEN_HEAD if index == 0 else GREEN
            pygame.draw.rect(self.screen, color, rect, border_radius=10)

        status = f"Longitud: {len(self.snake)} / {GRID_SIZE * GRID_SIZE}"
        self.draw_status_bar(status)

    def draw_status_bar(self, status_text: str) -> None:
        bar_rect = pygame.Rect(0, BOARD_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT - BOARD_SIZE)
        pygame.draw.rect(self.screen, BLACK, bar_rect)
        pygame.draw.line(self.screen, WHITE, (0, BOARD_SIZE), (WINDOW_WIDTH, BOARD_SIZE), 2)

        score_text = self.font_small.render(f"Puntuación: {self.score}", True, WHITE)
        status_text_surface = self.font_small.render(status_text, True, YELLOW)
        controls_text = self.font_small.render("Flechas/WASD para mover | ESC menú", True, WHITE)

        self.screen.blit(score_text, (20, BOARD_SIZE + 18))
        self.screen.blit(status_text_surface, (20, BOARD_SIZE + 45))
        self.screen.blit(controls_text, (WINDOW_WIDTH - 285, BOARD_SIZE + 32))

    def draw_menu(self) -> None:
        title = self.font_large.render("SNAKE DRM", True, GREEN_HEAD)
        subtitle = self.font_small.render("Producto protegido por DRM always-online", True, WHITE)
        expiration = self.font_small.render(self.license_expiration_text, True, YELLOW)

        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 105)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 140)))
        self.screen.blit(expiration, expiration.get_rect(center=(WINDOW_WIDTH // 2, 170)))

        for index, option in enumerate(self.menu_options):
            selected = index == self.menu_index
            color = YELLOW if selected else WHITE
            background = BLUE if selected else DARK_GRAY

            option_rect = pygame.Rect(WINDOW_WIDTH // 2 - 170, 230 + index * 80, 340, 55)
            pygame.draw.rect(self.screen, background, option_rect, border_radius=12)
            pygame.draw.rect(self.screen, WHITE, option_rect, 2, border_radius=12)

            text_surface = self.font_medium.render(option, True, color)
            self.screen.blit(text_surface, text_surface.get_rect(center=option_rect.center))

        hint = self.font_small.render("ENTER para seleccionar", True, WHITE)
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 420)))
    
    def draw_wrapped_text(self, text: str, color, center_x: int, start_y: int, max_width: int, line_height: int = 24):
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if self.font_small.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        for i, line in enumerate(lines):
            surface = self.font_small.render(line, True, color)
            rect = surface.get_rect(center=(center_x, start_y + i * line_height))
            self.screen.blit(surface, rect)

    def draw_overlay(self, title: str, subtitle: str) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect(45, 170, WINDOW_WIDTH - 90, 190)
        pygame.draw.rect(self.screen, DARK_GRAY, box_rect, border_radius=16)
        pygame.draw.rect(self.screen, WHITE, box_rect, 2, border_radius=16)

        title_surface = self.font_large.render(title, True, YELLOW)
        self.screen.blit(title_surface, title_surface.get_rect(center=(WINDOW_WIDTH // 2, 215)))

        self.draw_wrapped_text(
            subtitle,
            WHITE,
            WINDOW_WIDTH // 2,
            265,
            WINDOW_WIDTH - 130
        )

        if self.state == GameState.DRM_ERROR and self.drm_error_message:
            self.draw_wrapped_text(
                self.drm_error_message,
                WHITE,
                WINDOW_WIDTH // 2,
                315,
                WINDOW_WIDTH - 130
            )
    def run(self) -> bool:
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        return self.return_to_drm_requested


if __name__ == "__main__":
    SnakeGame().run()
