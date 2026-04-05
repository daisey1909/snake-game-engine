"""
Snake Game Engine
-----------------
Technologies : Python, Pygame, OOP
Author       : Dibyashree Mahala

Controls (Start Screen):
  UP / DOWN arrows  — navigate difficulty
  ENTER             — confirm and start

Controls (In Game):
  Arrow Keys / WASD — move
  P or ESC          — pause
  ENTER             — restart (on game over screen)
"""

import pygame
import sys
import random
import json
import os

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
CELL       = 20
COLS       = 30
ROWS       = 24
WIDTH      = CELL * COLS
HEIGHT     = CELL * ROWS
HUD_HEIGHT = 50
WIN_W      = WIDTH
WIN_H      = HEIGHT + HUD_HEIGHT

TARGET_FPS = 60
SCORE_FILE = "highscore.json"

DIFFICULTIES     = ["Easy", "Medium", "Hard"]
DIFFICULTY_SPEED = {"Easy": 7, "Medium": 12, "Hard": 18}
DIFFICULTY_COLOR = {
    "Easy"  : (80,  220, 120),
    "Medium": (255, 200, 50),
    "Hard"  : (240, 80,  80),
}
DIFFICULTY_DESC = {
    "Easy"  : "Perfect for beginners",
    "Medium": "The classic challenge",
    "Hard"  : "Test your reflexes",
}

C_BG        = (15,  15,  25)
C_GRID      = (25,  25,  40)
C_HUD       = (10,  10,  20)
C_HEAD      = (80,  220, 120)
C_BODY      = (50,  170, 90)
C_BODY2     = (40,  140, 75)
C_FOOD      = (240, 80,  80)
C_FOOD_GLOW = (255, 140, 140)
C_BONUS     = (255, 200, 50)
C_DIM       = (100, 100, 120)
C_WHITE     = (255, 255, 255)
C_GREEN     = (80,  220, 120)
C_RED       = (240, 80,  80)
C_YELLOW    = (255, 200, 50)
C_PANEL     = (25,  25,  45)
C_BORDER    = (60,  60,  90)

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


# ─────────────────────────────────────────────────────────────────────────────
# CLASS: Snake
# ─────────────────────────────────────────────────────────────────────────────
class Snake:
    def __init__(self):
        cx, cy = COLS // 2, ROWS // 2
        self.body      = [(cx, cy), (cx-1, cy), (cx-2, cy)]
        self.direction = RIGHT
        self._next_dir = RIGHT
        self.grew      = False

    def set_direction(self, new_dir):
        if new_dir != OPPOSITE.get(self.direction):
            self._next_dir = new_dir

    def move(self):
        self.direction = self._next_dir
        hx, hy = self.body[0]
        dx, dy = self.direction
        self.body.insert(0, (hx + dx, hy + dy))
        if not self.grew:
            self.body.pop()
        else:
            self.grew = False

    def grow(self):
        self.grew = True

    def hits_wall(self):
        hx, hy = self.body[0]
        return not (0 <= hx < COLS and 0 <= hy < ROWS)

    def hits_self(self):
        return self.body[0] in self.body[1:]

    def is_dead(self):
        return self.hits_wall() or self.hits_self()

    def draw(self, surface):
        for i, (x, y) in enumerate(self.body):
            rect = pygame.Rect(x*CELL+1, y*CELL+1+HUD_HEIGHT, CELL-2, CELL-2)
            if i == 0:
                pygame.draw.rect(surface, C_HEAD, rect, border_radius=5)
                ox = CELL//4 if self.direction==LEFT else 3*CELL//4 if self.direction==RIGHT else CELL//2-3
                oy = CELL//4 if self.direction==UP   else 3*CELL//4 if self.direction==DOWN  else CELL//2-3
                pygame.draw.circle(surface, C_BG, (x*CELL+ox, y*CELL+HUD_HEIGHT+oy), 3)
            else:
                pygame.draw.rect(surface, C_BODY if i%2==0 else C_BODY2, rect, border_radius=3)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS: Food
# ─────────────────────────────────────────────────────────────────────────────
class Food:
    BONUS_LIFETIME = 5.0

    def __init__(self):
        self.pos         = (0, 0)
        self.bonus_pos   = None
        self.bonus_timer = 0.0
        self._glow       = 0
        self._glow_dir   = 1

    def spawn(self, occupied):
        free = [(c, r) for c in range(COLS) for r in range(ROWS) if (c, r) not in occupied]
        self.pos = random.choice(free) if free else (1, 1)

    def maybe_spawn_bonus(self, occupied, score):
        if self.bonus_pos is None and score > 0 and score % 5 == 0:
            free = [(c, r) for c in range(COLS) for r in range(ROWS)
                    if (c, r) not in occupied and (c, r) != self.pos]
            if free:
                self.bonus_pos   = random.choice(free)
                self.bonus_timer = self.BONUS_LIFETIME

    def update(self, dt):
        if self.bonus_pos:
            self.bonus_timer -= dt
            if self.bonus_timer <= 0:
                self.bonus_pos = None
        self._glow += self._glow_dir * 4
        if self._glow >= 60 or self._glow <= 0:
            self._glow_dir *= -1

    def check_eat(self, head):
        if head == self.pos:
            return 1
        if self.bonus_pos and head == self.bonus_pos:
            self.bonus_pos = None
            return 3
        return 0

    def draw(self, surface):
        fx, fy = self.pos
        gs = pygame.Surface((CELL+4, CELL+4), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (*C_FOOD_GLOW, self._glow), gs.get_rect())
        surface.blit(gs, (fx*CELL-2, fy*CELL-2+HUD_HEIGHT))
        pygame.draw.rect(surface, C_FOOD,
                         pygame.Rect(fx*CELL+2, fy*CELL+2+HUD_HEIGHT, CELL-4, CELL-4),
                         border_radius=4)
        if self.bonus_pos:
            bx, by = self.bonus_pos
            pygame.draw.rect(surface, C_BONUS,
                             pygame.Rect(bx*CELL+1, by*CELL+1+HUD_HEIGHT, CELL-2, CELL-2),
                             border_radius=4)
            bar_w = int((self.bonus_timer / self.BONUS_LIFETIME) * (CELL - 2))
            pygame.draw.rect(surface, C_BONUS,
                             pygame.Rect(bx*CELL+1, by*CELL+HUD_HEIGHT-4, bar_w, 3))


# ─────────────────────────────────────────────────────────────────────────────
# CLASS: ScoreBoard
# ─────────────────────────────────────────────────────────────────────────────
class ScoreBoard:
    def __init__(self):
        self.score      = 0
        self.high_score = self._load()

    def add(self, pts):
        self.score += pts
        if self.score > self.high_score:
            self.high_score = self.score

    def reset(self):
        self.score = 0

    def save(self):
        try:
            with open(SCORE_FILE, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except IOError:
            pass

    def _load(self):
        if os.path.exists(SCORE_FILE):
            try:
                with open(SCORE_FILE) as f:
                    return json.load(f).get("high_score", 0)
            except Exception:
                pass
        return 0

    def draw(self, surface, font):
        pygame.draw.rect(surface, C_HUD, (0, 0, WIN_W, HUD_HEIGHT))
        pygame.draw.line(surface, C_BORDER, (0, HUD_HEIGHT), (WIN_W, HUD_HEIGHT), 1)
        sc = font.render(f"SCORE  {self.score:04d}", True, C_GREEN)
        hi = font.render(f"BEST   {self.high_score:04d}", True, C_YELLOW)
        surface.blit(sc, (16, HUD_HEIGHT//2 - sc.get_height()//2))
        surface.blit(hi, (WIN_W - hi.get_width() - 16,
                          HUD_HEIGHT//2 - hi.get_height()//2))


# ─────────────────────────────────────────────────────────────────────────────
# CLASS: GameEngine
# ─────────────────────────────────────────────────────────────────────────────
class GameEngine:
    STATE_START     = "start"
    STATE_PLAYING   = "playing"
    STATE_PAUSED    = "paused"
    STATE_GAME_OVER = "game_over"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake Game Engine  —  Dibyashree Mahala")
        self.screen  = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
        self.canvas  = pygame.Surface((WIN_W, WIN_H))  # fixed-size canvas, scaled to window
        self.clock   = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("consolas", 34, bold=True)
        self.font_md = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_sm = pygame.font.SysFont("consolas", 14)

        self.menu_index   = 1       # default: Medium
        self._pulse       = 0.0
        self._pulse_dir   = 1

        self.difficulty  = DIFFICULTIES[self.menu_index]
        self.state       = self.STATE_START
        self._tick_accum = 0.0

        self.snake = Snake()
        self.food  = Food()
        self.food.spawn(self.snake.body)
        self.board = ScoreBoard()

    @property
    def tick_interval(self):
        return 1.0 / DIFFICULTY_SPEED[self.difficulty]

    def _new_game(self):
        self.difficulty  = DIFFICULTIES[self.menu_index]
        self.snake       = Snake()
        self.food        = Food()
        self.food.spawn(self.snake.body)
        self.board.reset()
        self._tick_accum = 0.0
        self.state       = self.STATE_PLAYING

    # ── main loop ──────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            self._handle_events()
            if self.state == self.STATE_PLAYING:
                self._update(dt)
            # Pulse animation for start screen
            self._pulse += self._pulse_dir * dt * 150
            if self._pulse >= 255 or self._pulse <= 40:
                self._pulse_dir *= -1
            self._draw()

        pygame.quit()
        sys.exit()

    # ── events ─────────────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.board.save()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _on_key(self, key):
        if self.state == self.STATE_START:
            if key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % len(DIFFICULTIES)
            elif key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % len(DIFFICULTIES)
            elif key == pygame.K_RETURN:
                self._new_game()

        elif self.state == self.STATE_PLAYING:
            DIR_MAP = {
                pygame.K_UP: UP,      pygame.K_w: UP,
                pygame.K_DOWN: DOWN,  pygame.K_s: DOWN,
                pygame.K_LEFT: LEFT,  pygame.K_a: LEFT,
                pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
            }
            if key in DIR_MAP:
                self.snake.set_direction(DIR_MAP[key])
            elif key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = self.STATE_PAUSED

        elif self.state == self.STATE_PAUSED:
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = self.STATE_PLAYING

        elif self.state == self.STATE_GAME_OVER:
            if key == pygame.K_RETURN:
                self._new_game()
            elif key == pygame.K_ESCAPE:
                self.board.save()
                self.state = self.STATE_START

    # ── update ─────────────────────────────────────────────────────────────
    def _update(self, dt):
        self._tick_accum += dt
        self.food.update(dt)
        while self._tick_accum >= self.tick_interval:
            self._tick_accum -= self.tick_interval
            self._logic_tick()

    def _logic_tick(self):
        self.snake.move()
        if self.snake.is_dead():
            self.board.save()
            self.state = self.STATE_GAME_OVER
            return
        pts = self.food.check_eat(self.snake.body[0])
        if pts:
            self.snake.grow()
            self.board.add(pts)
            if pts == 1:
                self.food.spawn(self.snake.body)
                self.food.maybe_spawn_bonus(self.snake.body, self.board.score)

    # ── draw ───────────────────────────────────────────────────────────────
    def _draw(self):
        # All drawing goes to the fixed-size canvas
        self.canvas.fill(C_BG)
        self._draw_grid()

        if self.state == self.STATE_START:
            self._draw_start_screen()
        elif self.state in (self.STATE_PLAYING, self.STATE_PAUSED):
            self.food.draw(self.canvas)
            self.snake.draw(self.canvas)
            self.board.draw(self.canvas, self.font_md)
            if self.state == self.STATE_PAUSED:
                self._draw_overlay("PAUSED", "Press P or ESC to resume")
        elif self.state == self.STATE_GAME_OVER:
            self.food.draw(self.canvas)
            self.snake.draw(self.canvas)
            self.board.draw(self.canvas, self.font_md)
            self._draw_game_over()

        # Scale canvas to actual window size (keeps aspect ratio, adds black bars)
        win_w, win_h = self.screen.get_size()
        scale = min(win_w / WIN_W, win_h / WIN_H)
        scaled_w = int(WIN_W * scale)
        scaled_h = int(WIN_H * scale)
        scaled   = pygame.transform.smoothscale(self.canvas, (scaled_w, scaled_h))
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2
        self.screen.fill((0, 0, 0))
        self.screen.blit(scaled, (offset_x, offset_y))

        pygame.display.flip()

    def _draw_grid(self):
        for x in range(0, WIDTH + 1, CELL):
            pygame.draw.line(self.canvas, C_GRID, (x, HUD_HEIGHT), (x, WIN_H))
        for y in range(HUD_HEIGHT, WIN_H + 1, CELL):
            pygame.draw.line(self.canvas, C_GRID, (0, y), (WIDTH, y))

    # ── start screen ───────────────────────────────────────────────────────
    def _draw_start_screen(self):
        # Title
        title = self.font_lg.render("SNAKE GAME ENGINE", True, C_GREEN)
        self.canvas.blit(title, (WIN_W//2 - title.get_width()//2, 40))
        sub = self.font_sm.render("by Dibyashree Mahala", True, C_DIM)
        self.canvas.blit(sub, (WIN_W//2 - sub.get_width()//2, 84))

        # Difficulty panel
        panel_w = 360
        panel_h = 190
        panel_x = WIN_W//2 - panel_w//2
        panel_y = 118

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((*C_PANEL, 230))
        self.canvas.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.canvas, C_BORDER,
                         (panel_x, panel_y, panel_w, panel_h), 1, border_radius=6)

        hdr = self.font_sm.render("SELECT DIFFICULTY", True, C_DIM)
        self.canvas.blit(hdr, (WIN_W//2 - hdr.get_width()//2, panel_y + 12))

        option_h = 48
        for i, diff in enumerate(DIFFICULTIES):
            oy       = panel_y + 44 + i * option_h
            color    = DIFFICULTY_COLOR[diff]
            selected = (i == self.menu_index)

            row_rect = (panel_x + 10, oy, panel_w - 20, option_h - 6)

            if selected:
                # Filled highlight
                hl = pygame.Surface((panel_w - 20, option_h - 6), pygame.SRCALPHA)
                r, g, b = color
                hl.fill((r, g, b, 45))
                self.canvas.blit(hl, (panel_x + 10, oy))
                pygame.draw.rect(self.canvas, color, row_rect, 2, border_radius=4)

                # Animated arrow
                alpha  = max(40, min(255, int(self._pulse)))
                tri_x  = panel_x + 18
                tri_cy = oy + (option_h - 6)//2
                tri_pts = [(tri_x, tri_cy - 7), (tri_x, tri_cy + 7), (tri_x + 12, tri_cy)]
                arr_s   = pygame.Surface((14, 16), pygame.SRCALPHA)
                local_pts = [(0, 1), (0, 13), (12, 7)]
                pygame.draw.polygon(arr_s, (*color, alpha), local_pts)
                self.canvas.blit(arr_s, (tri_x, tri_cy - 7))

            # Difficulty name
            name_col = color if selected else C_DIM
            name_t   = self.font_md.render(diff.upper(), True, name_col)
            cy_text  = oy + (option_h - 6)//2 - name_t.get_height()//2
            self.canvas.blit(name_t, (panel_x + 38, cy_text))

            # Description on the right
            desc_col = (190, 190, 210) if selected else C_DIM
            desc_t   = self.font_sm.render(DIFFICULTY_DESC[diff], True, desc_col)
            self.canvas.blit(desc_t, (panel_x + panel_w - desc_t.get_width() - 14,
                                      oy + (option_h - 6)//2 - desc_t.get_height()//2))

        # Nav hint below panel
        nav = self.font_sm.render(
            "UP / DOWN  to navigate    ENTER  to start", True, C_DIM
        )
        self.canvas.blit(nav, (WIN_W//2 - nav.get_width()//2, panel_y + panel_h + 12))

        # Controls
        ctrl_y = panel_y + panel_h + 44
        for i, line in enumerate([
            "Arrow Keys / WASD  —  Move snake",
            "P or ESC           —  Pause game",
        ]):
            t = self.font_sm.render(line, True, C_DIM)
            self.canvas.blit(t, (WIN_W//2 - t.get_width()//2, ctrl_y + i * 20))

        # Bonus tip
        tip = self.font_sm.render(
            "Golden food = 3 pts — but disappears fast!", True, C_YELLOW
        )
        self.canvas.blit(tip, (WIN_W//2 - tip.get_width()//2, ctrl_y + 48))

        # High score
        hi = self.font_md.render(f"HIGH SCORE   {self.board.high_score:04d}", True, C_YELLOW)
        self.canvas.blit(hi, (WIN_W//2 - hi.get_width()//2, ctrl_y + 80))

        # Pulsing start prompt
        alpha   = max(40, min(255, int(self._pulse)))
        start_s = pygame.Surface(
            (self.font_md.size(">> PRESS ENTER TO PLAY <<")[0],
             self.font_md.size("A")[1]),
            pygame.SRCALPHA
        )
        r, g, b = C_GREEN
        prompt  = self.font_md.render(">> PRESS ENTER TO PLAY <<", True, (r, g, b, alpha))
        self.canvas.blit(prompt, (WIN_W//2 - prompt.get_width()//2, ctrl_y + 114))

    def _draw_overlay(self, title, subtitle):
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        self.canvas.blit(ov, (0, 0))
        t  = self.font_lg.render(title, True, C_WHITE)
        st = self.font_sm.render(subtitle, True, C_DIM)
        self.canvas.blit(t,  (WIN_W//2 - t.get_width()//2,  WIN_H//2 - 30))
        self.canvas.blit(st, (WIN_W//2 - st.get_width()//2, WIN_H//2 + 20))

    def _draw_game_over(self):
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        self.canvas.blit(ov, (0, 0))

        diff_color = DIFFICULTY_COLOR[self.difficulty]
        items = [
            (self.font_lg.render("GAME  OVER", True, C_RED),                             46),
            (self.font_sm.render(f"Difficulty : {self.difficulty}", True, diff_color),   28),
            (self.font_md.render(f"Score  :  {self.board.score}",   True, C_WHITE),      32),
            (self.font_md.render(f"Best   :  {self.board.high_score}", True, C_YELLOW),  36),
            (self.font_sm.render("ENTER — Play Again      ESC — Main Menu", True, C_DIM), 0),
        ]
        cy = WIN_H//2 - 95                                                
        for surf, gap in items:
            self.canvas.blit(surf, (WIN_W//2 - surf.get_width()//2, cy))
            cy += surf.get_height() + gap

        
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = GameEngine()
    engine.run()
