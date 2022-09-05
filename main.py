import pygame
import random
import math
import os

DISPLAY = [12*64, 12*64]
CELL_SIZE = 12
FPS = 120

GRAY = (150, 150, 150)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BULLET_RED = (180, 0, 0)
BULLET_GREEN = (0, 180, 0)
BULLET_BLUE = (0, 0, 180)
BULLET_YELLOW = (180, 180, 0)


cheats = False
cheat_keys = (pygame.K_l, pygame.K_o, pygame.K_h)

bullet_speed = CELL_SIZE // (FPS / 30)                                      # Не рекомендую ставить больше размера клетки
bullet_speed = CELL_SIZE if bullet_speed > CELL_SIZE else bullet_speed
bullet_size = 1                                                             # Размер относительно размера клетки
rate_of_fire = FPS // 30                                                    # Столько кадров требуется на 1 выстрел, минимум 1
rate_of_fire = 1 if rate_of_fire < 1 else rate_of_fire
bullet_glow_size = bullet_size * CELL_SIZE * 3                              # Размер свечения снаряда, последнее число - относительно размера снаряда
bullet_brightness = 80                                                      # Яркость свечения снаряда от 0 до 255
add_bullet_glow = True                                                      # Если указать False, свечения снарядов не будет
                                                                            # Производительность существенно вырастет

game_speed = 10 * 30 // FPS
max_game_speed = 50 * 30 // FPS
game_speed_count = 0
game_speed_limit = 500 * FPS // 30

winner_animation_speed = 4 * 30 // FPS      # Выше 255 ставить нет смысла, но даже это уже извращенство
winner_alpha_range = 180, 255

angle_range = -5, 95
angle = angle_range[0]
angle_change_speed = 0.8 * 30 / FPS

cannon_length = 4                # Относительно размера снаряда (Примерно от центра башни)   На момент 01:28 20.11.2021 лучше не трогать
                                 # Она ломается, код вращения взял из интернета, потому что стандартные линии работают очень и очень плохо
old_music = []
all_music = os.listdir("music/")
if "desktop.ini" in all_music:
    del all_music[all_music.index("desktop.ini")]
music_volume = 30                # В процентах
music_paused = False

icon_file = "circle.png"

display_changed = False


def create_circle_image(color):
    w, h = CELL_SIZE * bullet_size, CELL_SIZE * bullet_size
    r, g, b = color
    image = pygame.transform.scale(pygame.image.load("circle.png"), (w, h))

    for x in range(w):
        for y in range(h):
            a = image.get_at((x, y))[3]                       # Перебираю каждый пиксель и закрашиваю в необходимый цвет
            image.set_at((x, y), pygame.Color(r, g, b, a))

    return image


def create_bullet_glow(color):
    w, h = bullet_glow_size, bullet_glow_size
    r, g, b = color
    image = pygame.transform.scale(pygame.image.load("circle.png"), (w, h))

    for x in range(w):
        for y in range(h):
            a = image.get_at((x, y))[3]                       # Перебираю каждый пиксель и закрашиваю в указанный цвет, учитывая прозрачность
            if a != 0:
                a = round(abs(1 - ((w // 2 - x)**2 + (h // 2 - y)**2)**0.5 / (bullet_glow_size//2)) * bullet_brightness)
            image.set_at((x, y), pygame.Color(r, g, b, a))

    return image



class Cell(pygame.sprite.Sprite):
    def __init__(self, x_pos, y_pos):
        pygame.sprite.Sprite.__init__(self)
        self.ind = y_pos // CELL_SIZE * DISPLAY[0] // CELL_SIZE + x_pos // CELL_SIZE   # Определение уникального индекса, не знаю зачем на момент 23:42 10.11.21
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.tower_cell = False

        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))

        if self.x_pos < DISPLAY[0] // 2 and self.y_pos < DISPLAY[1] // 2:         # Начальное заполнение цветов
            self.color = RED
            self.team = "red"

        elif self.x_pos >= DISPLAY[0] // 2 and self.y_pos < DISPLAY[1] // 2:
            self.color = BLUE
            self.team = "blue"

        elif self.x_pos < DISPLAY[0] // 2 and self.y_pos >= DISPLAY[1] // 2:
            self.color = YELLOW
            self.team = "yellow"

        else:
            self.color = GREEN
            self.team = "green"

        CELLS[self.team] += 1

        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x_pos, y_pos)

        if self.ind == DISPLAY[0]/CELL_SIZE + 1:
            self.tower_cell = "red"

        elif self.ind == DISPLAY[0]/CELL_SIZE*2-2:
            self.tower_cell = "blue"

        elif self.ind == (DISPLAY[1]/CELL_SIZE - 2)*DISPLAY[0]/CELL_SIZE + 1:
            self.tower_cell = "yellow"

        elif self.ind == (DISPLAY[1]/CELL_SIZE - 1)*DISPLAY[0]/CELL_SIZE - 2:
            self.tower_cell = "green"


    def refill(self, color):
        self.color = color
        CELLS[self.team] -= 1
        self.team = color__team[color]
        CELLS[self.team] += 1
        self.image.fill(self.color)
        if self.tower_cell:
            for tower in tower_sprites.sprites():
                if tower.team == self.tower_cell:
                    tower.dead = True

            self.tower_cell = False


class Bullet(pygame.sprite.Sprite):
    def __init__(self, color):
        pygame.sprite.Sprite.__init__(self)
        self.deleted = False
        self.color = color
        self.image = bullet_images[(BULLET_RED, BULLET_GREEN, BULLET_BLUE, BULLET_YELLOW).index(self.color)]
        self.w, self.h = CELL_SIZE * bullet_size, CELL_SIZE * bullet_size
        self.rect = self.image.get_rect()

        if color == BULLET_RED:
            self.team = "red"
            self.tower = tower_sprites.sprites()[0]
            self.angle_shift = 0

        elif color == BULLET_GREEN:
            self.team = "green"
            self.tower = tower_sprites.sprites()[1]
            self.angle_shift = 180

        elif color == BULLET_BLUE:
            self.team = "blue"
            self.tower = tower_sprites.sprites()[2]
            self.angle_shift = 90

        elif color == BULLET_YELLOW:
            self.team = "yellow"
            self.tower = tower_sprites.sprites()[3]
            self.angle_shift = -90

        self.angle = angle + self.angle_shift
        while self.angle < 0:
            self.angle += 360
        while self.angle > 360:
            self.angle -= 360

        self.rect.center = self.tower.rect.center[0] + CELL_SIZE * bullet_size * (cannon_length-1) * math.cos(math.radians(self.angle)), self.tower.rect.center[1] + CELL_SIZE * bullet_size * (cannon_length-1) * math.sin(math.radians(self.angle))

        self.x_speed = bullet_speed * math.cos(math.radians(self.angle))
        self.y_speed = bullet_speed * math.sin(math.radians(self.angle))
        self.x_pos, self.y_pos = self.rect.x - bullet_size / 2, self.rect.y - bullet_size / 2

        if add_bullet_glow:
            bullet_glow_sprites.add(Bullet_glow(self))

    def update(self):
        self.x_pos += self.x_speed
        self.y_pos += self.y_speed

        if self.x_pos < 1:
            self.x_pos = 1
        elif self.x_pos + self.w > DISPLAY[0]-1:
            self.x_pos = DISPLAY[0] - self.w - 1

        if self.y_pos < 1:
            self.y_pos = 1
        elif self.y_pos + self.h > DISPLAY[1]-1:
            self.y_pos = DISPLAY[1] - self.h - 1

        self.rect.x, self.rect.y = self.x_pos, self.y_pos

        self.top_ind = self.rect.y // CELL_SIZE * DISPLAY[0] // CELL_SIZE + (self.rect.x + self.w//2) // CELL_SIZE
        self.bottom_ind = (self.rect.y + self.h) // CELL_SIZE * DISPLAY[0] // CELL_SIZE + (self.rect.x + self.w//2) // CELL_SIZE
        self.left_ind = (self.rect.y + self.h//2) // CELL_SIZE * DISPLAY[0] // CELL_SIZE + self.rect.x // CELL_SIZE
        self.right_ind = (self.rect.y + self.h//2) // CELL_SIZE * DISPLAY[0] // CELL_SIZE + (self.rect.x + self.w) // CELL_SIZE
        self.ind = (self.rect.y + self.h//2) // CELL_SIZE * DISPLAY[0] // CELL_SIZE + (self.rect.x + self.w//2) // CELL_SIZE

        for ind in (self.ind, self.top_ind, self.bottom_ind, self.left_ind, self.right_ind):
            cell = all_cells[ind]

            if self.team != cell.team:
                if self.team == "red":
                    cell.refill(RED)

                elif self.team == "green":
                    cell.refill(GREEN)

                elif self.team == "blue":
                    cell.refill(BLUE)

                elif self.team == "yellow":
                    cell.refill(YELLOW)

                bullet_sprites.remove(self)
                self.deleted = True
                break

        if self.rect.right >= DISPLAY[0] - 1 or self.rect.left <= 1:
            self.x_speed = -self.x_speed                                     # Обработка отскоков

        if self.rect.bottom >= DISPLAY[1] - 1 or self.rect.top <= 1:
            self.y_speed = -self.y_speed


class Bullet_glow(pygame.sprite.Sprite):
    def __init__(self, bullet):
        pygame.sprite.Sprite.__init__(self)
        self.bullet = bullet
        self.image = bullet_glow
        self.rect = self.image.get_rect()
        self.rect.center = self.bullet.rect.center

    def update(self):
        if self.bullet.deleted:
            bullet_glow_sprites.remove(self)
        self.rect.center = self.bullet.rect.center


class Tower(pygame.sprite.Sprite):
    def __init__(self, team):
        pygame.sprite.Sprite.__init__(self)
        self.color = GRAY
        self.team = team
        self.dead = False

        self.multiply_count = 1000
        self.multiply = 0
        self.release_count = 1000
        self.release = 0
        self.bullets = 1
        self.shooting = False

        w, h = int(CELL_SIZE*3), int(CELL_SIZE*3)
        self.image = pygame.transform.scale(pygame.image.load("circle.png"), (w, h))
        r, g, b = self.color

        for x in range(w):
            for y in range(h):
                a = self.image.get_at((x, y))[3]                       # Перебираю каждый пиксель и закрашиваю в серый цвет
                self.image.set_at((x, y), pygame.Color(r, g, b, a))

        self.rect = self.image.get_rect()
        if self.team == "red":
            self.rect.topleft = (0, 0)

        elif self.team == "blue":
            self.rect.topleft = (DISPLAY[0]-3*CELL_SIZE, 0)

        elif self.team == "yellow":
            self.rect.topleft = (0, DISPLAY[1]-3*CELL_SIZE)

        elif self.team == "green":
            self.rect.topleft = (DISPLAY[0]-3*CELL_SIZE, DISPLAY[1]-3*CELL_SIZE)

    def update(self):
        if self.dead:
            self.image.fill((0, 0, 0, 0))

        elif self.shooting:
            self.shoot()

        else:
            self.multiply += random.randint(2, game_speed)
            self.release += random.randint(2, game_speed)

            if self.multiply >= self.multiply_count:
                self.bullets *= 2
                self.multiply = 0
                self.release = 0

            if self.release >= self.release_count:
                self.rate_of_fire_count = 0
                self.shooting = True
                self.multiply = 0
                self.release = 0

    def shoot(self):
        if self.rate_of_fire_count % rate_of_fire == 0:
            bullet_sprites.add(Bullet(team__bullet_color[self.team]))

            self.bullets -= 1
            self.rate_of_fire_count += 1

            if self.bullets == 0:
                self.shooting = False
                self.bullets = 1
        else:
            self.rate_of_fire_count += 1


class Cannon(pygame.sprite.Sprite):
    def __init__(self, team):
        pygame.sprite.Sprite.__init__(self)
        self.team = team
        if team == "red":
            self.tower = tower_sprites.sprites()[0]
            self.angle_shift = 0
        elif team == "green":
            self.tower = tower_sprites.sprites()[1]
            self.angle_shift = 180
        elif team == "blue":
            self.tower = tower_sprites.sprites()[2]
            self.angle_shift = 90
        elif team == "yellow":
            self.tower = tower_sprites.sprites()[3]
            self.angle_shift = -90

        pos = self.tower.rect.center

        self.image = pygame.Surface((bullet_size * CELL_SIZE * cannon_length, round(bullet_size * CELL_SIZE * 1.2)), pygame.SRCALPHA)
        self.image.fill(GRAY)

        self.orig_image = self.image
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.offset = pygame.math.Vector2(CELL_SIZE*1.5, 0)

    def update(self):
        if self.tower.dead:
            self.image.set_alpha(0)

        else:
            self.angle = angle + self.angle_shift
            self.image = pygame.transform.rotozoom(self.orig_image, -self.angle, 1)

            offset_rotated = self.offset.rotate(self.angle)

            self.rect = self.image.get_rect(center=self.pos+offset_rotated)


class Percent_text(pygame.sprite.Sprite):
    def __init__(self, team):
        pygame.sprite.Sprite.__init__(self)
        self.team = team
        self.color = GRAY

        for tower in tower_sprites.sprites():
            if self.team == tower.team:
                self.tower = tower
                break

        self.font = pygame.font.SysFont('verdana', int(DISPLAY[1] / 23.77))
        self.image = self.font.render(str(round(CELLS[self.team]/((DISPLAY[0]*DISPLAY[1])/CELL_SIZE**2)*100, 2))+"%", True, self.color)
        self.rect = self.image.get_rect()

        if self.team == "red":
            self.rect.topleft = (CELL_SIZE * 6, CELL_SIZE)

        elif self.team == "blue":
            self.rect.topright = (DISPLAY[0] - CELL_SIZE * 6, CELL_SIZE)

        elif self.team == "yellow":
            self.rect.bottomleft = (CELL_SIZE * 6, DISPLAY[1] - CELL_SIZE)

        elif self.team == "green":
            self.rect.bottomright = (DISPLAY[0] - CELL_SIZE * 6, DISPLAY[1] - CELL_SIZE)

    def update(self):
        self.image = self.font.render(str(round(CELLS[self.team]/((DISPLAY[0]*DISPLAY[1])/CELL_SIZE**2)*100, 2))+"%", True, self.color)

        if self.tower.dead:
            self.image.set_alpha(120)

        if self.team in ("blue", "green"):
            self.rect = self.image.get_rect()

            if self.team == "blue":
                self.rect.topright = (DISPLAY[0] - CELL_SIZE * 6, CELL_SIZE)

            elif self.team == "green":
                self.rect.bottomright = (DISPLAY[0] - CELL_SIZE * 6, DISPLAY[1] - CELL_SIZE)


class Bullet_text(pygame.sprite.Sprite):
    def __init__(self, team):
        pygame.sprite.Sprite.__init__(self)
        self.team = team
        self.color = GRAY

        for tower in tower_sprites.sprites():
            if self.team == tower.team:
                self.tower = tower
                break

        self.font = pygame.font.SysFont('verdana', int(DISPLAY[1] / 9.24))
        self.image = self.font.render(str(self.tower.bullets), True, self.color)
        self.rect = self.image.get_rect()

        if self.team == "red":
            self.rect.center = (DISPLAY[0] // 4, DISPLAY[1] // 4)

        elif self.team == "blue":
            self.rect.center = (DISPLAY[0] * 3 // 4, DISPLAY[1] // 4)

        elif self.team == "yellow":
            self.rect.center = (DISPLAY[0] // 4, DISPLAY[1] * 3 // 4)

        elif self.team == "green":
            self.rect.center = (DISPLAY[0] * 3 // 4, DISPLAY[1] * 3 // 4)

    def update(self):
        self.image = self.font.render(str(self.tower.bullets), True, self.color)

        if self.tower.dead:
            self.image.set_alpha(120)

        self.rect = self.image.get_rect()

        if self.team == "red":
            self.rect.center = (DISPLAY[0] // 4, DISPLAY[1] // 4)

        elif self.team == "blue":
            self.rect.center = (DISPLAY[0] * 3 // 4, DISPLAY[1] // 4)

        elif self.team == "yellow":
            self.rect.center = (DISPLAY[0] // 4, DISPLAY[1] * 3 // 4)

        elif self.team == "green":
            self.rect.center = (DISPLAY[0] * 3 // 4, DISPLAY[1] * 3 // 4)


class Winner_text(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.color = GRAY
        self.flag = False
        self.alpha_up = True
        self.draw_count = 0
        self.font = pygame.font.SysFont('verdana', int(DISPLAY[1] / 4.92), True)
        self.image = self.font.render("WINNER", True, self.color)
        self.image.set_alpha(0)
        self.rect = self.image.get_rect()
        self.rect.center = (DISPLAY[0] // 2, DISPLAY[1] // 2)

    def update(self):
        global running


        if self.flag:
            if self.alpha_up:
                self.draw_count += winner_animation_speed
                if self.draw_count >= winner_alpha_range[1]:
                    self.alpha_up = False
            
            else:
                self.draw_count -= winner_animation_speed
                if self.draw_count <= winner_alpha_range[0]:
                    self.alpha_up = True
                    
            self.image = self.font.render("WINNER", True, self.color)
            self.image.set_alpha(self.draw_count)
        else:
            self.dead_count = 0

            for tower in tower_sprites.sprites():
                if tower.dead:
                    self.dead_count += 1

                else:
                    self.color = team__bullet_color[tower.team]

            self.image = self.font.render("WINNER", True, self.color)
            self.image.set_alpha(0)

            if self.dead_count == len(tower_sprites.sprites()) - 1:
                self.flag = True
                running = False
                tower_sprites.update()


while True:
    if DISPLAY[0] % (CELL_SIZE * 2) != 0:   # По необходимости подгоняю разрешение, если его выбрали косячно, чтобы игра не ломалась
        DISPLAY[0] -= 1
        display_changed = True
        continue
    if DISPLAY[1] % (CELL_SIZE * 2) != 0:
        DISPLAY[1] -= 1
        display_changed = True
        continue
    break
if display_changed:
    print("\nРазрешение экрана было изменено для избежания проблем с логикой игры\nТекущее равно:", DISPLAY)

icon = pygame.image.load(icon_file)
ico_size = icon.get_rect().size
for x in range(ico_size[0]):
    for y in range(ico_size[1]):
        a = icon.get_at((x, y))[3]                       # Определяю иконку, перебирая каждый пиксель и закрашивая в необходимый цвет
        if x < ico_size[0] // 2 and y < ico_size[1] // 2:
            r, g, b = RED

        elif x >= ico_size[0] // 2 and y < ico_size[1] // 2:
            r, g, b = BLUE

        elif x < ico_size[0] // 2 and y >= ico_size[1] // 2:
            r, g, b = YELLOW

        else:
            r, g, b = GREEN
        icon.set_at((x, y), pygame.Color(r, g, b, a))


if add_bullet_glow:
    bullet_glow = create_bullet_glow(WHITE)

bullet_images = [create_circle_image(color) for color in (BULLET_RED, BULLET_GREEN, BULLET_BLUE, BULLET_YELLOW)]
CELLS = {"red": 0, "green": 0, "blue": 0, "yellow": 0}
team__bullet_color = {"red" : BULLET_RED, "green" : BULLET_GREEN, "blue" : BULLET_BLUE, "yellow" : BULLET_YELLOW}
color__team = {RED : "red", GREEN : "green", BLUE : "blue", YELLOW : "yellow"}
team__color = {"red": RED, "green": GREEN, "blue": BLUE, "yellow": YELLOW}


pygame.init()

pygame.mixer.init()
pygame.mixer.music.set_volume(music_volume / 100)

pygame.font.init()
screen = pygame.display.set_mode(DISPLAY)
pygame.display.set_caption("MoR")
clock = pygame.time.Clock()
pygame.display.set_icon(icon)


cell_sprites = pygame.sprite.Group()
bullet_sprites = pygame.sprite.Group()
bullet_glow_sprites = pygame.sprite.Group()
tower_sprites = pygame.sprite.Group()
cannon_sprites = pygame.sprite.Group()
team_text_sprites = pygame.sprite.Group()
winner_text_sprite = pygame.sprite.Group()

for i in range(0, DISPLAY[1], CELL_SIZE):
    for j in range(0, DISPLAY[0], CELL_SIZE):
        cell_sprites.add(Cell(x_pos = j, y_pos = i))

for team in ("red", "green", "blue", "yellow"):
    tower_sprites.add(Tower(team))
    cannon_sprites.add(Cannon(team))
    team_text_sprites.add(Percent_text(team))
    team_text_sprites.add(Bullet_text(team))
winner_text_sprite.add(Winner_text())


all_cells = cell_sprites.sprites()
running = True
while True:
    clock.tick(FPS)

    if game_speed < max_game_speed:
        game_speed_count += 1
        if game_speed_count > game_speed_limit:
            game_speed += 1
            game_speed_count = 0

    for key in cheat_keys:
        if not pygame.key.get_pressed()[key]:
            break
    else:
        cheats = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                pygame.quit()
                quit()
            elif event.key == pygame.K_p:
                if not music_paused:
                    pygame.mixer.music.pause()
                elif music_paused:
                    pygame.mixer.music.unpause()
                music_paused = not music_paused

            elif cheats:
                if event.key == pygame.K_r:
                    tower_sprites.sprites()[0].dead = True
                elif event.key == pygame.K_g:
                    tower_sprites.sprites()[1].dead = True
                elif event.key == pygame.K_b:
                    tower_sprites.sprites()[2].dead = True
                elif event.key == pygame.K_y:
                    tower_sprites.sprites()[3].dead = True

                elif event.key == pygame.K_KP7:
                    tower_sprites.sprites()[0].bullets *= 2
                elif event.key == pygame.K_KP3:
                    tower_sprites.sprites()[1].bullets *= 2
                elif event.key == pygame.K_KP9:
                    tower_sprites.sprites()[2].bullets *= 2
                elif event.key == pygame.K_KP1:
                    tower_sprites.sprites()[3].bullets *= 2

    angle += angle_change_speed
    if angle <= angle_range[0] or angle >= angle_range[1]:
        angle = angle_range[0] if angle < angle_range[0] else angle_range[1] if angle > angle_range[1] else angle
        angle_change_speed = -angle_change_speed
    
    if running:
        tower_sprites.update()
        bullet_sprites.update()
        bullet_glow_sprites.update()
        cannon_sprites.update()
        team_text_sprites.update()
    winner_text_sprite.update()

    cell_sprites.draw(screen)
    bullet_glow_sprites.draw(screen)
    bullet_sprites.draw(screen)
    tower_sprites.draw(screen)
    cannon_sprites.draw(screen)
    team_text_sprites.draw(screen)
    winner_text_sprite.draw(screen)

    if not pygame.mixer.music.get_busy() and not music_paused:
        new_music = random.choice(all_music)

        while new_music in old_music:
            new_music = random.choice(all_music)

        pygame.mixer.music.load("music/" + new_music)
        pygame.mixer.music.play()
        old_music.append(new_music)

        if len(old_music) == len(all_music):
            old_music = []

    pygame.display.flip()
