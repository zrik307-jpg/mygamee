import math
import random
import pygame

# Инициализация Pygame
pygame.init()

# Режим на весь экран
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
TARGET_FPS = 60

# Каталог тем для заднего фона и живых обоев
THEMES = [
    {
        "name": "Cyber Dark",
        "bg": (18, 22, 34),
        "grid": (28, 35, 52),
        "out": (10, 13, 20),
        "particle": (100, 200, 255),
    },
    {
        "name": "Neon Matrix",
        "bg": (10, 25, 18),
        "grid": (18, 45, 32),
        "out": (5, 12, 8),
        "particle": (50, 255, 120),
    },
    {
        "name": "Sunset Glow",
        "bg": (32, 16, 28),
        "grid": (52, 28, 45),
        "out": (15, 8, 14),
        "particle": (255, 140, 200),
    },
]

# Игровые параметры
CELL_SIZE = 20
WORLD_CENTER = (WIDTH // 2, HEIGHT // 2)

# Состояния игры
STATE_INTRO = 0
STATE_MENU = 1
STATE_SKINS = 2
STATE_THEMES = 3
STATE_GAME = 4
STATE_VICTORY = 5
STATE_DEFEAT = 6

# Шрифты
FONT_TITLE = pygame.font.SysFont("Arial", 32, bold=True)
FONT_SUB = pygame.font.SysFont("Arial", 20, bold=True)
FONT_HUGE = pygame.font.SysFont("Arial", 75, bold=True)
FONT_BRAND = pygame.font.SysFont("Arial", 40, bold=True)

# Живые скины с палитрами свечения
PALETTES = {
    "red": {
        "main": (255, 60, 90),
        "trail": (255, 120, 150),
        "dark": (180, 20, 50),
    },
    "blue": {
        "main": (0, 168, 255),
        "trail": (100, 210, 255),
        "dark": (0, 100, 180),
    },
    "yellow": {
        "main": (255, 190, 0),
        "trail": (255, 220, 120),
        "dark": (190, 130, 0),
    },
    "purple": {
        "main": (180, 50, 220),
        "trail": (220, 140, 255),
        "dark": (120, 20, 160),
    },
}

SKINS = [
    {
        "name": "Cyber Red",
        "palette": PALETTES["red"],
        "price": 0,
        "unlocked": True,
    },
    {
        "name": "Neon Blue",
        "palette": PALETTES["blue"],
        "price": 100,
        "unlocked": False,
    },
    {
        "name": "Solar Gold",
        "palette": PALETTES["yellow"],
        "price": 250,
        "unlocked": False,
    },
    {
        "name": "Void Purple",
        "palette": PALETTES["purple"],
        "price": 500,
        "unlocked": False,
    },
]


def draw_bold_text(surface, text, font, color, center):
  render = font.render(text, True, color)
  rect = render.get_rect(center=center)
  surface.blit(render, rect)


class Camera:

  def __init__(self):
    self.x = 0
    self.y = 0

  def update(self, target_x, target_y):
    self.x += (target_x - WIDTH // 2 - self.x) * 0.1
    self.y += (target_y - HEIGHT // 2 - self.y) * 0.1

  def apply(self, pos):
    return (int(pos[0] - self.x), int(pos[1] - self.y))


class DynamicJoystick:

  def __init__(self):
    self.active = False
    self.start_pos = (0, 0)
    self.current_pos = (0, 0)
    self.vector = (0, -1)

  def handle_event(self, event):
    if event.type == pygame.MOUSEBUTTONDOWN:
      self.active = True
      self.start_pos = event.pos
      self.current_pos = event.pos
      self.vector = (0, 0)
    elif event.type == pygame.MOUSEBUTTONUP and self.active:
      self.active = False
      self.vector = (0, -1)
    elif event.type == pygame.MOUSEMOTION and self.active:
      self.current_pos = event.pos
      dx = self.current_pos[0] - self.start_pos[0]
      dy = self.current_pos[1] - self.start_pos[1]
      dist = math.hypot(dx, dy)
      if dist > 5:
        self.vector = (dx / dist, dy / dist)

  def draw(self, surface):
    if self.active:
      pygame.draw.circle(surface, (40, 50, 70), self.start_pos, 52, 2)
      pygame.draw.circle(surface, (70, 90, 130), self.start_pos, 50, 3)
      pygame.draw.circle(surface, (100, 130, 180), self.current_pos, 25)
      pygame.draw.circle(
          surface, (255, 255, 255), self.current_pos, 25, 2
      )


class Character:

  def __init__(self, x, y, name, palette, current_level, is_bot=False):
    self.x = x
    self.y = y
    self.name = name
    self.palette = palette
    self.is_bot = is_bot
    self.alive = True
    self.angle = -math.pi / 2

    base_speed = 2.8 if is_bot else 3.4
    self.speed = base_speed

    self.territory = set()
    self.grid_trail = []
    self.smooth_trail = []
    self.bot_timer = 0

    start_cx = int(x // CELL_SIZE)
    start_cy = int(y // CELL_SIZE)
    for dx in range(-6, 7):
      for dy in range(-6, 7):
        self.territory.add((start_cx + dx, start_cy + dy))

  def update(self, joystick=None, target_player=None):
    if not self.alive:
      return

    if self.is_bot:
      self.bot_timer += 1
      if len(self.grid_trail) > 10:
        if self.territory:
          bx = sum(c[0] for c in self.territory) / len(self.territory) * CELL_SIZE
          by = sum(c[1] for c in self.territory) / len(self.territory) * CELL_SIZE
          target_angle = math.atan2(by - self.y, bx - self.x)
          diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
          self.angle += max(-0.08, min(0.08, diff))
      else:
        if self.bot_timer % 80 == 0:
          self.angle += random.choice([-1.5, 1.5])
        else:
          self.angle += math.sin(self.bot_timer * 0.04) * 0.03
    else:
      if joystick and joystick.vector != (0, 0):
        target_angle = math.atan2(joystick.vector[1], joystick.vector[0])
        diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += max(-0.12, min(0.12, diff))

    self.x += math.cos(self.angle) * self.speed
    self.y += math.sin(self.angle) * self.speed

    current_cell = (int(self.x // CELL_SIZE), int(self.y // CELL_SIZE))

    if current_cell not in self.territory:
      if not self.grid_trail or self.grid_trail[-1] != current_cell:
        self.grid_trail.append(current_cell)
        self.smooth_trail.append((self.x, self.y))
    else:
      if self.grid_trail:
        self.territory.update(self.grid_trail)
        self._fill_territory()
        self.grid_trail.clear()
        self.smooth_trail.clear()

  def _fill_territory(self):
    if not self.territory:
      return
    min_x = min(c[0] for c in self.territory) - 25
    max_x = max(c[0] for c in self.territory) + 25
    min_y = min(c[1] for c in self.territory) - 25
    max_y = max(c[1] for c in self.territory) + 25

    outside = set()
    queue = [(min_x, min_y)]
    outside.add((min_x, min_y))

    while queue:
      cx, cy = queue.pop(0)
      for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
        if min_x <= nx <= max_x and min_y <= ny <= max_y:
          if (nx, ny) not in self.territory and (nx, ny) not in outside:
            outside.add((nx, ny))
            queue.append((nx, ny))

    all_captured = set()
    for x in range(min_x, max_x + 1):
      for y in range(min_y, max_y + 1):
        if (x, y) not in outside:
          all_captured.add((x, y))
    self.territory = all_captured

  def draw_cube(self, surface, camera, override_pos=None, override_size=None):
    pos = override_pos if override_pos else camera.apply((self.x, self.y))
    # Анимация живого скина (пульсация)
    pulse = math.sin(pygame.time.get_ticks() * 0.012) * 3
    size = int(
        (override_size if override_size else CELL_SIZE * 2.2)
        + (0 if override_pos else pulse)
    )

    pygame.draw.rect(
        surface,
        (5, 5, 12),
        (pos[0] - size // 2 + 3, pos[1] - size // 2 + 8, size, size),
        border_radius=12,
    )
    pygame.draw.rect(
        surface,
        self.palette["dark"],
        (pos[0] - size // 2, pos[1] - size // 2 + 4, size, size),
        border_radius=12,
    )
    pygame.draw.rect(
        surface,
        self.palette["main"],
        (pos[0] - size // 2, pos[1] - size // 2, size, size),
        border_radius=12,
    )
    pygame.draw.rect(
        surface,
        (255, 255, 255),
        (pos[0] - size // 2, pos[1] - size // 2, size, size),
        2,
        border_radius=12,
    )

  def draw_trail(self, surface, camera):
    if len(self.smooth_trail) > 1:
      points = [camera.apply(p) for p in self.smooth_trail]
      pygame.draw.lines(
          surface, self.palette["trail"], False, points, max(6, CELL_SIZE)
      )

  def draw_territory(self, surface, camera):
    for cx, cy in self.territory:
      wx = cx * CELL_SIZE
      wy = cy * CELL_SIZE
      pos = camera.apply((wx, wy))
      if (
          -CELL_SIZE <= pos[0] <= WIDTH + CELL_SIZE
          and -CELL_SIZE <= pos[1] <= HEIGHT + CELL_SIZE
      ):
        pygame.draw.rect(
            surface,
            self.palette["main"],
            (pos[0], pos[1], CELL_SIZE, CELL_SIZE),
        )
        import sys

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Paper.io 2 - NIRAG AI Ultimate Edition")
CLOCK = pygame.time.Clock()

current_level = 1
player_coins_balance = 200
selected_skin_idx = 0
selected_theme_idx = 0
WORLD_RADIUS = 600

particles = [
    {
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "speed": random.uniform(0.5, 1.5),
        "size": random.randint(2, 5),
    }
    for _ in range(40)
]


def reset_game():
  global WORLD_RADIUS
  WORLD_RADIUS = 650
  player_palette = SKINS[selected_skin_idx]["palette"]
  player = Character(
      WORLD_CENTER[0], WORLD_CENTER[1] + 250, "YOU", player_palette, 1, is_bot=False
  )

  bots = []
  bot_colors = [PALETTES["blue"], PALETTES["yellow"], PALETTES["purple"]]
  for i in range(2):
    angle = (2 * math.pi / 2) * i
    bx = WORLD_CENTER[0] + math.cos(angle) * 380
    by = WORLD_CENTER[1] + math.sin(angle) * 380
    bots.append(
        Character(
            bx,
            by,
            f"BOT {i+1}",
            bot_colors[i % len(bot_colors)],
            1,
            is_bot=True,
        )
    )

  return player, bots, DynamicJoystick(), Camera()


player, bots, joystick, camera = reset_game()
current_state = STATE_INTRO
intro_start_ticks = pygame.time.get_ticks()

play_btn_rect = (WIDTH // 2 - 190, int(HEIGHT * 0.54), 380, 80)
skins_btn_rect = (WIDTH // 2 - 140, int(HEIGHT * 0.67), 280, 50)
themes_btn_rect = (WIDTH // 2 - 140, int(HEIGHT * 0.75), 280, 50)

skin_menu_view_idx = 0
theme_menu_view_idx = 0

running = True
while running:
  CLOCK.tick(TARGET_FPS)
  theme = THEMES[selected_theme_idx]

  for p in particles:
    p["y"] += p["speed"]
    if p["y"] > HEIGHT:
      p["y"] = 0
      p["x"] = random.randint(0, WIDTH)

  if current_state == STATE_INTRO:
    elapsed_sec = (pygame.time.get_ticks() - intro_start_ticks) / 1000.0
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
        current_state = STATE_MENU

    SCREEN.fill((12, 16, 26))
    cx, cy = WIDTH // 2, HEIGHT // 2
    draw_bold_text(
        SCREEN,
        "NIRAG AI STUDIOS",
        FONT_TITLE,
        (100, 200, 255),
        (cx, cy - 100),
    )
    draw_bold_text(
        SCREEN,
        "Игра создана командой NIRAG AI",
        FONT_SUB,
        (220, 225, 235),
        (cx, cy - 30),
    )
    draw_bold_text(
        SCREEN,
        "Основатель: Леончиков Ярослав",
        FONT_TITLE,
        (255, 100, 150),
        (cx, cy + 25),
    )
    draw_bold_text(
        SCREEN,
        "Нажмите куда угодно для старта",
        FONT_SUB,
        (140, 150, 170),
        (cx, cy + 140),
    )

    if elapsed_sec >= 4.5:
      current_state = STATE_MENU

  elif current_state == STATE_MENU:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      elif event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos
        bx, by, bw, bh = play_btn_rect
        if bx <= mx <= bx + bw and by <= my <= by + bh:
          player, bots, joystick, camera = reset_game()
          current_state = STATE_GAME
        elif (
            skins_btn_rect[0] <= mx <= skins_btn_rect[0] + skins_btn_rect[2]
            and skins_btn_rect[1]
            <= my
            <= skins_btn_rect[1] + skins_btn_rect[3]
        ):
          skin_menu_view_idx = selected_skin_idx
          current_state = STATE_SKINS
        elif (
            themes_btn_rect[0] <= mx <= themes_btn_rect[0] + themes_btn_rect[2]
            and themes_btn_rect[1]
            <= my
            <= themes_btn_rect[1] + themes_btn_rect[3]
        ):
          theme_menu_view_idx = selected_theme_idx
          current_state = STATE_THEMES

    SCREEN.fill(theme["bg"])
    for p in particles:
      pygame.draw.circle(
          SCREEN, theme["particle"], (p["x"], int(p["y"])), p["size"]
      )

    for x in range(0, WIDTH, 50):
      pygame.draw.line(SCREEN, theme["grid"], (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 50):
      pygame.draw.line(SCREEN, theme["grid"], (0, y), (WIDTH, y), 1)

    card_w, card_h = 240, 50
    cx, cy = WIDTH // 2, int(HEIGHT * 0.10)
    pygame.draw.rect(
        SCREEN,
        (25, 32, 48),
        (cx - card_w // 2, cy - card_h // 2, card_w, card_h),
        border_radius=20,
    )
    pygame.draw.circle(SCREEN, (255, 215, 0), (cx - 75, cy), 16)
    draw_bold_text(
        SCREEN,
        str(player_coins_balance),
        FONT_TITLE,
        (255, 255, 255),
        (cx + 15, cy),
    )

    title_center = (WIDTH // 2, int(HEIGHT * 0.32))
    draw_bold_text(
        SCREEN,
        "PAPER.IO 2",
        FONT_HUGE,
        (10, 15, 25),
        (title_center[0] + 4, title_center[1] + 4),
    )
    draw_bold_text(
        SCREEN,
        "PAPER.IO 2",
        FONT_HUGE,
        SKINS[selected_skin_idx]["palette"]["main"],
        title_center,
    )

    bx, by, bw, bh = play_btn_rect
    pygame.draw.rect(
        SCREEN, (20, 110, 60), (bx, by + 5, bw, bh), border_radius=25
    )
    pygame.draw.rect(SCREEN, (46, 204, 113), (bx, by, bw, bh), border_radius=25)
    pygame.draw.rect(
        SCREEN, (255, 255, 255), (bx, by, bw, bh), 4, border_radius=25
    )
    draw_bold_text(
        SCREEN, "ИГРАТЬ", FONT_TITLE, (255, 255, 255), (bx + bw // 2, by + bh // 2)
    )

    sx, sy, sw, sh = skins_btn_rect
    pygame.draw.rect(
        SCREEN, (0, 130, 210), (sx, sy, sw, sh), border_radius=20
    )
    draw_bold_text(
        SCREEN,
        "МАГАЗИН СКИНОВ",
        FONT_SUB,
        (255, 255, 255),
        (sx + sw // 2, sy + sh // 2),
    )

    tx, ty, tw, th = themes_btn_rect
    pygame.draw.rect(
        SCREEN, (130, 40, 200), (tx, ty, tw, th), border_radius=20
    )
    draw_bold_text(
        SCREEN,
        "КАТАЛОГ ТЕМ",
        FONT_SUB,
        (255, 255, 255),
        (tx + tw // 2, ty + th // 2),
    )

  elif current_state == STATE_SKINS:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      elif event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos
        if math.hypot(mx - (WIDTH // 2 - 160), my - int(HEIGHT * 0.38)) < 45:
          skin_menu_view_idx = (skin_menu_view_idx - 1) % len(SKINS)
        elif math.hypot(mx - (WIDTH // 2 + 160), my - int(HEIGHT * 0.38)) < 45:
          skin_menu_view_idx = (skin_menu_view_idx + 1) % len(SKINS)
        elif (
            WIDTH // 2 - 130 <= mx <= WIDTH // 2 + 130
            and int(HEIGHT * 0.65) <= my <= int(HEIGHT * 0.65) + 55
        ):
          skin = SKINS[skin_menu_view_idx]
          if skin["unlocked"]:
            selected_skin_idx = skin_menu_view_idx
          elif player_coins_balance >= skin["price"]:
            player_coins_balance -= skin["price"]
            skin["unlocked"] = True
            selected_skin_idx = skin_menu_view_idx
        elif (
            WIDTH // 2 - 100 <= mx <= WIDTH // 2 + 100
            and int(HEIGHT * 0.80) <= my <= int(HEIGHT * 0.80) + 55
        ):
          current_state = STATE_MENU

    SCREEN.fill(theme["bg"])
    draw_bold_text(
        SCREEN,
        "ВЫБОР ЖИВОГО СКИНА",
        FONT_TITLE,
        (230, 240, 255),
        (WIDTH // 2, int(HEIGHT * 0.12)),
    )

    skin = SKINS[skin_menu_view_idx]
    preview_char = Character(0, 0, "", skin["palette"], 1)
    preview_char.draw_cube(
        SCREEN, None, override_pos=(WIDTH // 2, int(HEIGHT * 0.38)), override_size=90
    )

    draw_bold_text(
        SCREEN,
        skin["name"],
        FONT_TITLE,
        skin["palette"]["main"],
        (WIDTH // 2, int(HEIGHT * 0.52)),
    )
    draw_bold_text(
        SCREEN,
        "<",
        FONT_BRAND,
        (200, 210, 225),
        (WIDTH // 2 - 160, int(HEIGHT * 0.38)),
    )
    draw_bold_text(
        SCREEN,
        ">",
        FONT_BRAND,
        (200, 210, 225),
        (WIDTH // 2 + 160, int(HEIGHT * 0.38)),
    )

    btn_w, btn_h = 260, 55
    bx, by = WIDTH // 2 - btn_w // 2, int(HEIGHT * 0.65)
    if skin["unlocked"]:
      txt = (
          "ВЫБРАНО" if skin_menu_view_idx == selected_skin_idx else "ВЫБРАТЬ"
      )
      pygame.draw.rect(
          SCREEN, (46, 204, 113), (bx, by, btn_w, btn_h), border_radius=25
      )
      draw_bold_text(
          SCREEN, txt, FONT_SUB, (255, 255, 255), (WIDTH // 2, by + btn_h // 2)
      )
    else:
      pygame.draw.rect(
          SCREEN, (255, 171, 0), (bx, by, btn_w, btn_h), border_radius=25
      )
      draw_bold_text(
          SCREEN,
          f"КУПИТЬ ({skin['price']})",
          FONT_SUB,
          (255, 255, 255),
          (WIDTH // 2, by + btn_h // 2),
      )

    back_w, back_h = 200, 55
    pygame.draw.rect(
        SCREEN,
        (240, 60, 80),
        (WIDTH // 2 - back_w // 2, int(HEIGHT * 0.80), back_w, back_h),
        border_radius=25,
    )
    draw_bold_text(
        SCREEN,
        "НАЗАД",
        FONT_SUB,
        (255, 255, 255),
        (WIDTH // 2, int(HEIGHT * 0.80) + back_h // 2),
    )

  elif current_state == STATE_THEMES:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      elif event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos
        if math.hypot(mx - (WIDTH // 2 - 160), my - int(HEIGHT * 0.38)) < 45:
          theme_menu_view_idx = (theme_menu_view_idx - 1) % len(THEMES)
        elif math.hypot(mx - (WIDTH // 2 + 160), my - int(HEIGHT * 0.38)) < 45:
          theme_menu_view_idx = (theme_menu_view_idx + 1) % len(THEMES)
        elif (
            WIDTH // 2 - 130 <= mx <= WIDTH // 2 + 130
            and int(HEIGHT * 0.65) <= my <= int(HEIGHT * 0.65) + 55
        ):
          selected_theme_idx = theme_menu_view_idx
        elif (
            WIDTH // 2 - 100 <= mx <= WIDTH // 2 + 100
            and int(HEIGHT * 0.80) <= my <= int(HEIGHT * 0.80) + 55
        ):
          current_state = STATE_MENU

    SCREEN.fill(theme["bg"])
    draw_bold_text(
        SCREEN,
        "КАТАЛОГ ТЕМ И ОБОЕВ",
        FONT_TITLE,
        (230, 240, 255),
        (WIDTH // 2, int(HEIGHT * 0.12)),
    )

    curr_theme = THEMES[theme_menu_view_idx]
    draw_bold_text(
        SCREEN,
        curr_theme["name"],
        FONT_BRAND,
        curr_theme["particle"],
        (WIDTH // 2, int(HEIGHT * 0.38)),
    )
    draw_bold_text(
        SCREEN,
        "<",
        FONT_BRAND,
        (200, 210, 225),
        (WIDTH // 2 - 160, int(HEIGHT * 0.38)),
    )
    draw_bold_text(
        SCREEN,
        ">",
        FONT_BRAND,
        (200, 210, 225),
        (WIDTH // 2 + 160, int(HEIGHT * 0.38)),
    )

    btn_w, btn_h = 260, 55
    bx, by = WIDTH // 2 - btn_w // 2, int(HEIGHT * 0.65)
    txt = (
        "АКТИВНО"
        if theme_menu_view_idx == selected_theme_idx
        else "УСТАНОВИТЬ ТЕМУ"
    )
    pygame.draw.rect(
        SCREEN, (46, 204, 113), (bx, by, btn_w, btn_h), border_radius=25
    )
    draw_bold_text(
        SCREEN, txt, FONT_SUB, (255, 255, 255), (WIDTH // 2, by + btn_h // 2)
    )

    back_w, back_h = 200, 55
    pygame.draw.rect(
        SCREEN,
        (240, 60, 80),
        (WIDTH // 2 - back_w // 2, int(HEIGHT * 0.80), back_w, back_h),
        border_radius=25,
    )
    draw_bold_text(
        SCREEN,
        "НАЗАД",
        FONT_SUB,
        (255, 255, 255),
        (WIDTH // 2, int(HEIGHT * 0.80) + back_h // 2),
    )

  elif current_state == STATE_GAME:
    all_chars = [player] + bots

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      if player.alive:
        joystick.handle_event(event)
      elif event.type == pygame.MOUSEBUTTONDOWN:
        current_state = STATE_MENU

    if player.alive:
      player.update(joystick)
      camera.update(player.x, player.y)

    for bot in bots:
      if bot.alive:
        bot.update(None, target_player=player)

    total_world_cells = max(1, int(math.pi * (WORLD_RADIUS / CELL_SIZE) ** 2))

    for char in all_chars:
      if not char.alive:
        continue
      for target in all_chars:
        if not target.alive:
          continue
        char_cell = (int(char.x // CELL_SIZE), int(char.y // CELL_SIZE))

        # Перехват чужих клеток при заходе на чужую территорию
        if char == player and target != player:
          if char_cell in target.territory:
            target.territory.remove(char_cell)
            player.territory.add(char_cell)

    # ПРОВЕРКА ВЫХОДА ЗА ГРАНИЦЫ МИРА (ЕДИНСТВЕННАЯ СМЕРТЬ ИГРОКА)
    dist_from_world_center = math.hypot(
        player.x - WORLD_CENTER[0], player.y - WORLD_CENTER[1]
    )
    if dist_from_world_center > WORLD_RADIUS:
      player.alive = False

    # Считаем проценты захвата
    player_percent = int((len(player.territory) / total_world_cells) * 100)
    bot_percents = [
        int((len(b.territory) / total_world_cells) * 100)
        for b in bots
        if b.alive
    ]

    # ИГРА ЗАКАНЧИВАЕТСЯ ТОЛЬКО ПОСЛЕ 75% КАРТЫ
    if player_percent >= 75:
      current_state = STATE_VICTORY
    elif not player.alive:
      current_state = STATE_DEFEAT
    elif any(bp >= 75 for bp in bot_percents):
      current_state = STATE_DEFEAT

    SCREEN.fill(theme["out"])

    center_s = camera.apply(WORLD_CENTER)
    pygame.draw.circle(SCREEN, theme["bg"], center_s, WORLD_RADIUS)
    pygame.draw.circle(SCREEN, (220, 70, 90), center_s, WORLD_RADIUS, 6)

    for char in all_chars:
      if char.alive:
        char.draw_territory(SCREEN, camera)
    for char in all_chars:
      if char.alive:
        char.draw_trail(SCREEN, camera)
    for char in all_chars:
      if char.alive:
        char.draw_cube(SCREEN, camera)

    # ШКАЛА ПРОЦЕНТОВ (ЦЕЛЬ: 75%)
    bar_w, bar_h = 400, 24
    bar_x, bar_y = WIDTH // 2 - bar_w // 2, 25
    pygame.draw.rect(
        SCREEN,
        (40, 45, 60),
        (bar_x, bar_y, bar_w, bar_h),
        border_radius=12,
    )
    fill_w = int(bar_w * min(1.0, player_percent / 75.0))
    pygame.draw.rect(
        SCREEN,
        SKINS[selected_skin_idx]["palette"]["main"],
        (bar_x, bar_y, fill_w, bar_h),
        border_radius=12,
    )
    pygame.draw.rect(
        SCREEN,
        (255, 255, 255),
        (bar_x, bar_y, bar_w, bar_h),
        2,
        border_radius=12,
    )
    draw_bold_text(
        SCREEN,
        f"ВАШ ЗАХВАТ: {player_percent}% / 75%",
        FONT_SUB,
        (255, 255, 255),
        (WIDTH // 2, bar_y + bar_h // 2),
    )

    if player.alive:
      joystick.draw(SCREEN)

  elif current_state in (STATE_VICTORY, STATE_DEFEAT):
    is_win = current_state == STATE_VICTORY
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      elif event.type == pygame.MOUSEBUTTONDOWN:
        if is_win:
          player_coins_balance += 150
        player, bots, joystick, camera = reset_game()
        current_state = STATE_MENU

    SCREEN.fill(theme["bg"])
    cx, cy = WIDTH // 2, HEIGHT // 2
    if is_win:
      draw_bold_text(
          SCREEN,
          "ПОБЕДА! ВЫ ЗАХВАТИЛИ 75%!",
          FONT_BRAND,
          (46, 204, 113),
          (cx, cy - 60),
      )
      draw_bold_text(
          SCREEN,
          "Награда: +150 монет",
          FONT_TITLE,
          (255, 215, 0),
          (cx, cy),
      )
    else:
      draw_bold_text(
          SCREEN,
          "ВЫ ВЫШЛИ ЗА ГРАНИЦЫ МИРА!",
          FONT_BRAND,
          (255, 60, 90),
          (cx, cy - 40),
      )

    draw_bold_text(
        SCREEN,
        "Нажмите куда угодно для возврата в меню",
        FONT_SUB,
        (180, 190, 210),
        (cx, cy + 60),
    )

  pygame.display.flip()

pygame.quit()
sys.exit()
