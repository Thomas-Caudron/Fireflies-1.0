import pygame, random, math
pygame.init()
pygame.mixer.init()

# ======================
# FENÊTRE + CONSTANTES
# ======================
W, H = 1024, 600
FPS = 60
BG = (10, 10, 20)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Fireflies")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 32)
big = pygame.font.SysFont(None, 64)

TEXTS = {
 "fr": {
   "title": "Attrape les lucioles",
   "intro1": "Une nuit, les lucioles ont disparu...",
   "intro2": "Tu dois les retrouver avant l'aube.",
   "tutorial": "Flèches/QD pour bouger, Espace pour sauter.",
   "win": "Tu as ramené la lumière !"
 },
 "en": {
   "title": "Catch the fireflies",
   "intro1": "One night, the fireflies vanished...",
   "intro2": "You must find them before dawn.",
   "tutorial": "Arrows/AD to move, Space to jump.",
   "win": "You brought the light back!"
 }
}

langs = ["fr", "en"]
lang = "en"   # langue par défaut

# ======================
# AUDIO
# ======================
music_lobby = "lobby.mp3"
music_game = "game.mp3"

jump_sound = pygame.mixer.Sound("jump.mp3")
jump_sound.set_volume(0.5)

death_sound = pygame.mixer.Sound("death.mp3")
death_sound.set_volume(0.6)

def play_music(path, volume=0.6):
    pygame.mixer.music.stop()
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)

# ======================
# ASSETS
# ======================
projectile_imgs = [
    pygame.image.load("proj1.png").convert_alpha(),
    pygame.image.load("proj2.png").convert_alpha(),
    pygame.image.load("proj3.png").convert_alpha(),
    pygame.image.load("proj4.png").convert_alpha(),
    pygame.image.load("proj5.png").convert_alpha()
]

skins = [
 pygame.image.load("player1.png").convert_alpha(),
 pygame.image.load("player2.png").convert_alpha(),
 pygame.image.load("player3.png").convert_alpha()
]
skin_index = 0
current_skin = skins[0]

lamp_img = pygame.image.load("lamp.png").convert_alpha()
cinematic_bg = pygame.transform.scale(
    pygame.image.load("cinematic_bg.png"),
    (W, H)
)

# ======================
# JOUEUR
# ======================
player = pygame.Rect(W//2, 500-40, 40, 40)
vy = 0
on_ground = False
jumps_left = 2

player_anim_t = 0

# ======================
# DEATH SCREEN
# ======================
class DeathScreen:
    def __init__(self):
        self.alpha = 0
        self.done = False
        self.timer = 0

    def reset(self):
        self.alpha = 0
        self.done = False
        self.timer = 0

    def update(self, temp, player):
        self.alpha = min(255, self.alpha + 8)
        fade = pygame.Surface((W, H), pygame.SRCALPHA)
        fade.fill((0, 0, 0, self.alpha))
        temp.blit(fade, (0, 0))

        if self.alpha < 40:
            flash = pygame.Surface((W, H))
            flash.fill((255, 255, 255))
            temp.blit(flash, (0, 0))

        for _ in range(3):
            particles.append(Particle(player.x + 20, player.y + 20))

        # Texte traduit
        death_text = "TU ES MORT" if lang == "fr" else "YOU DIED"

        scale = 1 + (self.alpha / 255) * 0.4
        fnt = pygame.font.SysFont(None, int(80 * scale))
        t = fnt.render(death_text, True, (255, 60, 60))
        temp.blit(t, (W//2 - t.get_width()//2, H//2 - t.get_height()//2))

        if self.alpha >= 255:
            self.timer += 1
            if self.timer > 60:
                self.done = True

death_screen = DeathScreen()

# ======================
# PARTICULES
# ======================
class Particle:
    def __init__(s, x, y):
        s.x, s.y = x, y
        s.vx = random.uniform(-2, 2)
        s.vy = random.uniform(-3, -1)
        s.life = random.randint(20, 40)
        s.color = (255, random.randint(150, 255), 50)

    def update(s):
        s.x += s.vx
        s.y += s.vy
        s.vy += 0.1
        s.life -= 1

    def draw(s, win):
        if s.life > 0:
            pygame.draw.circle(win, s.color, (int(s.x), int(s.y)), 3)

particles = []

# ======================
# SCREEN SHAKE
# ======================
shake = 0
screen_shake = 0

def add_shake(a):
    global shake, screen_shake
    shake = max(shake, a)
    screen_shake = max(screen_shake, a)

# ======================
# PLATEFORMES
# ======================
class Platform:
    def __init__(s, x, y, w, h, t="fixed", rng=0, spd=0):
        s.x, s.y, s.w, s.h = x, y, w, h
        s.t = t
        s.rng = rng
        s.spd = spd
        s.ox, s.oy = x, y
        s.tt = random.uniform(0, 1000)

    def update(s):
        s.tt += s.spd
        if s.t == "horizontal":
            s.x = s.ox + math.sin(s.tt * 0.01) * s.rng
        elif s.t == "vertical":
            s.y = s.oy + math.sin(s.tt * 0.01) * s.rng

    def draw(s, win):
        pygame.draw.rect(win, (80,80,120), (s.x, s.y, s.w, s.h))

platforms = []

# ======================
# LAMPADAIRE
# ======================
lamp_anim_t = 0

class Lamp:
    def __init__(s, x, y):
        s.x, s.y = x, y
        s.on = False

    def draw(s, win):
        global lamp_anim_t
        lamp_anim_t += 0.1

        pulse = 1 + math.sin(lamp_anim_t) * 0.15
        base_scale = 0.20

        w = int(lamp_img.get_width() * base_scale * pulse)
        h = int(lamp_img.get_height() * base_scale * pulse)

        scaled = pygame.transform.smoothscale(lamp_img, (w, h))
        win.blit(scaled, (s.x - w//2, s.y - h))

lamp = None

# ======================
# LUCIOLES & PROJECTILES
# ======================
class Fly:
    def __init__(s, x, y, high=False):
        s.x, s.y = x, y
        s.by = y
        s.high = high
        s.t = random.uniform(0, 1000)

    def update(s):
        s.t += 0.08
        s.y = s.by + math.sin(s.t) * 6

    def draw(s, win):
        c = (255,255,120) if not s.high else (255,80,80)
        pygame.draw.circle(win, c, (int(s.x), int(s.y)), 6)

flies = []
projectiles = []
projectile_timer = 0

class Projectile:
    def __init__(s, x, y, target_x, target_y):
        s.x = x
        s.y = y

        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)

        speed = 3
        s.vx = dx / dist * speed
        s.vy = dy / dist * speed

        original = random.choice(projectile_imgs)

        scale = 1 / 20
        w = int(original.get_width() * scale)
        h = int(original.get_height() * scale)

        s.base_img = pygame.transform.smoothscale(original, (w, h))

        s.angle = math.degrees(math.atan2(-dy, dx)) - 90
        s.img = pygame.transform.rotate(s.base_img, s.angle)

        s.w = s.img.get_width()
        s.h = s.img.get_height()

    def update(s):
        s.x += s.vx
        s.y += s.vy

    def draw(s, win):
        win.blit(s.img, (int(s.x - s.w/2), int(s.y - s.h/2)))

    def rect(s):
        return pygame.Rect(s.x - s.w/2, s.y - s.h/2, s.w, s.h)

# ======================
# NIVEAUX
# ======================
levels = [{} for _ in range(5)]

# ======================
# UTILITAIRES
# ======================
def find_valid_lamp_position():
    valid = [p for p in platforms if 200 < p.y < 450]
    if valid:
        p = random.choice(valid)
        return p.x + p.w//2, p.y - 40
    return 800, 300

def generate_flies_procedural():
    res = []
    for i in range(4):
        x = random.randint(150, W-150)
        y = random.randint(150, 350)
        res.append(Fly(x, y, high=(i == 3)))
    return res

# ======================
# LOAD
# ======================
def load():
    global lamp, platforms, flies, flash_msg, flash_timer

    flash_msg = ""
    flash_timer = 0
    platforms.clear()
    flies.clear()
    lamp = None

    NB_PLAT = 7
    FIRST_Y = 420

    MIN_DY = -110 
    MAX_DY = -70

    MIN_DX = -220
    MAX_DX = 220

    MIN_DIST = 90

    def too_close(x, y, w, h):
        rect = pygame.Rect(x, y, w, h)
        for p in platforms:
            other = pygame.Rect(p.x, p.y, p.w, p.h)
            if rect.colliderect(other.inflate(MIN_DIST, MIN_DIST)):
                return True
        return False

    w = random.randint(100, 160)
    x = random.randint(80, W - 80 - w)
    y = FIRST_Y
    platforms.append(Platform(x, y, w, 20))

    for i in range(1, NB_PLAT):
        prev = platforms[-1]

        for _ in range(50):
            dx = random.randint(MIN_DX, MAX_DX)
            dy = random.randint(MIN_DY, MAX_DY)

            w = random.randint(100, 160)
            x = prev.x + dx
            y = prev.y + dy

            x = max(50, min(W - 50 - w, x))
            y = max(80, min(420, y))

            if not too_close(x, y, w, 20):
                platforms.append(Platform(x, y, w, 20))
                break

    DECOR_COUNT = random.randint(5, 9)

    for _ in range(DECOR_COUNT):
        for _ in range(40):
            w = random.randint(60, 120)
            x = random.randint(40, W - 40 - w)
            y = random.randint(120, 520)

            if not too_close(x, y, w, 20):
                p = Platform(x, y, w, 20)
                p.decor = True
                platforms.append(p)
                break

    for i, p in enumerate(platforms[:NB_PLAT]):
        fx = p.x + p.w // 2
        fy = p.y - 20
        flies.append(Fly(fx, fy, high=(i == NB_PLAT - 1)))

# ======================
# ÉTATS
# ======================
lvl = 0
state = "menu"
intro_timer = 0
intro_flies = []
intro_darkness = 0
intro_text_surface = None

show_tuto = True
tuto_timer = 0

flash_msg = ""
flash_timer = 0

time_scale = 1.0
run = True
last_music = ""

# ======================
# MENU
# ======================
menu_button = pygame.Rect(W//2 - 100, H//2 + 120, 200, 60)
menu_hover = False

def draw_menu(surface):
    surface.fill((10,10,18))

    title = big.render(TEXTS[lang]["title"], True, (255,255,255))
    surface.blit(title, (W//2 - title.get_width()//2, 80))

    base_h = 120
    scale = base_h / current_skin.get_height()
    img = pygame.transform.smoothscale(
        current_skin,
        (int(current_skin.get_width()*scale), int(current_skin.get_height()*scale))
    )
    surface.blit(img, (W//2 - img.get_width()//2, H//2 - img.get_height()//2 - 40))

    left = big.render("<", True, (255,255,255))
    right = big.render(">", True, (255,255,255))
    surface.blit(left, (W//2 - 180, H//2 - 20))
    surface.blit(right, (W//2 + 150, H//2 - 20))

    txt_skin = font.render(f"Skin {skin_index+1}", True, (255,255,255))
    surface.blit(txt_skin, (W//2 - txt_skin.get_width()//2, H//2 + 80))

    color = (60,60,100) if not menu_hover else (90,90,140)
    pygame.draw.rect(surface, color, menu_button, border_radius=12)
    pygame.draw.rect(surface, (255,255,255), menu_button, 3, border_radius=12)
    txt = font.render("JOUER", True, (255,255,255))
    surface.blit(txt, (menu_button.x + 45, menu_button.y + 20))

    lang_txt = font.render(f"Langue : {lang.upper()} (TAB)", True, (200,200,200))
    surface.blit(lang_txt, (20, H - 50))

# ======================
# INTRO
# ======================
def update_intro(temp):
    global intro_timer, intro_darkness, intro_text_surface, state, last_music

    if last_music != "game":
        play_music(music_game)
        last_music = "game"

    intro_timer += 1
    temp.blit(cinematic_bg, (0,0))

    intro_darkness = min(220, intro_darkness + 1.2)
    dark = pygame.Surface((W, H), pygame.SRCALPHA)
    dark.fill((0,0,0,int(intro_darkness)))
    temp.blit(dark, (0,0))

    if random.random() < 0.05:
        intro_flies.append(Fly(random.randint(200,800), random.randint(200,500)))

    for f in intro_flies:
        f.update()
        f.draw(temp)

    if intro_timer < 180:
        text = TEXTS[lang]["intro1"]
        prog = intro_timer / 180
    else:
        text = TEXTS[lang]["intro2"]
        prog = (intro_timer - 180) / 180

    scale = 1 + prog * 0.6
    fnt = pygame.font.SysFont(None, int(50 * scale))
    intro_text_surface = fnt.render(text, True, (255,255,255))

    if intro_timer > 360:
        state = "game"
        load()
        
# ======================
# BOUCLE PRINCIPALE
# ======================
while run:
    dt_raw = clock.tick(FPS) / 1000
    dt = dt_raw * time_scale
    time_scale += (1.0 - time_scale) * 0.1

    temp = pygame.Surface((W, H))
    temp.fill(BG)

    # ======================
    # EVENTS
    # ======================
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False

        # MENU
        elif e.type == pygame.KEYDOWN and state == "menu":
            if e.key == pygame.K_TAB:
                lang = langs[(langs.index(lang)+1) % len(langs)]
            elif e.key == pygame.K_LEFT:
                skin_index = (skin_index - 1) % len(skins)
                current_skin = skins[skin_index]
            elif e.key == pygame.K_RIGHT:
                skin_index = (skin_index + 1) % len(skins)
                current_skin = skins[skin_index]
            else:
                state = "intro"
                intro_timer = 0
                intro_darkness = 0
                intro_flies = []

        elif e.type == pygame.MOUSEBUTTONDOWN and state == "menu":
            if menu_button.collidepoint(e.pos):
                state = "intro"
                intro_timer = 0
                intro_darkness = 0
                intro_flies = []

        # INTRO skip
        elif e.type == pygame.KEYDOWN and state == "intro":
            state = "game"
            load()

    # ======================
    # MENU
    # ======================
    if state == "menu":
        if last_music != "menu":
            play_music(music_lobby)
            last_music = "menu"

        mx, my = pygame.mouse.get_pos()
        menu_hover = menu_button.collidepoint(mx, my)
        draw_menu(temp)

    # ======================
    # INTRO
    # ======================
    elif state == "intro":
        update_intro(temp)

    # ======================
    # GAME
    # ======================
    elif state == "game":

        # Musique du jeu
        if last_music != "game":
            play_music(music_game)
            last_music = "game"

        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_q]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump = keys[pygame.K_SPACE] or keys[pygame.K_z] or keys[pygame.K_w]

        # Déplacement horizontal
        if left:
            player.x -= 5
        if right:
            player.x += 5
        player.x = max(0, min(W - player.width, player.x))

        # Gravité
        vy += 0.5
        player.y += vy

        # Sol
        if player.bottom >= 500:
            player.bottom = 500
            vy = 0
            on_ground = True
            jumps_left = 2
        else:
            on_ground = False

        # ======================
        # COLLISIONS PLATEFORMES
        # ======================
        for p in platforms:
            if hasattr(p, "decor"):
                continue

            ox, oy = p.x, p.y
            p.update()
            p.draw(temp)

            rect = pygame.Rect(p.x, p.y, p.w, p.h)
            rect_old = pygame.Rect(ox, oy, p.w, p.h)

            if player.colliderect(rect):
                if vy >= 0:
                    if player.bottom <= rect_old.top + 5:
                        player.bottom = p.y
                        vy = 0
                        on_ground = True
                        jumps_left = 2

        # ======================
        # SAUT
        # ======================
        if jump:
            if on_ground:
                vy = -12
                on_ground = False
                jumps_left = 1
                jump_sound.play()
            elif jumps_left > 0:
                vy = -10
                jumps_left -= 1
                jump_sound.play()
                add_shake(3)
                for _ in range(8):
                    particles.append(Particle(player.x+20, player.y+20))

        # ======================
        # LUCIOLES
        # ======================
        for f in flies[:]:
            f.update()
            f.draw(temp)

            if player.colliderect(pygame.Rect(f.x-10, f.y-10, 20, 20)):
                flies.remove(f)
                for _ in range(12):
                    particles.append(Particle(f.x, f.y))
                add_shake(6)

                if f.high:
                    flash_timer = 10

                if not flies and lamp is None:
                    lamp = Lamp(*find_valid_lamp_position())
                    flash_msg = "VITE, trouve le réverbère!" if lang == "fr" else "HURRY, find the lamp post!"
                    flash_timer = 120

        if flash_timer > 0 and lamp:
            t = big.render(flash_msg, True, (255,200,50))
            temp.blit(t, (W//2 - t.get_width()//2, 200))
            flash_timer -= 1

        # ======================
        # LAMPADAIRE
        # ======================
        if lamp:
            lamp.draw(temp)
            if not flies and player.colliderect(pygame.Rect(lamp.x-20, lamp.y-80, 40, 80)):
                lamp.on = True
                lvl += 1
                if lvl < len(levels):
                    load()
                else:
                    state = "win"

        # ======================
        # PROJECTILES
        # ======================
        projectile_timer += 1

        if projectile_timer > 90:
            projectile_timer = 0

            side = random.choice(["left", "right", "top", "bottom"])

            if side == "left":
                sx = -40
                sy = random.randint(0, H)
            elif side == "right":
                sx = W + 40
                sy = random.randint(0, H)
            elif side == "top":
                sx = random.randint(0, W)
                sy = -40
            else:
                sx = random.randint(0, W)
                sy = H + 40

            tx = player.x + player.width // 2
            ty = player.y + player.height // 2

            projectiles.append(Projectile(sx, sy, tx, ty))

        for pr in projectiles[:]:
            pr.update()
            pr.draw(temp)

            # Collision → écran de mort stylé
            if pr.rect().colliderect(player):
                death_sound.play()
                death_screen.reset()
                state = "dead"
                break

            # Suppression hors écran
            if pr.x < -100 or pr.x > W+100 or pr.y < -100 or pr.y > H+100:
                projectiles.remove(pr)

        # ======================
        # JOUEUR PULSANT
        # ======================
        player_anim_t += 0.12
        pulse = 1 + math.sin(player_anim_t) * 0.12

        BASE = 0.35 * pulse
        img = current_skin

        w = int(img.get_width() * BASE)
        h = int(img.get_height() * BASE)
        sc = pygame.transform.smoothscale(img, (w, h))

        temp.blit(sc, (
            player.x + player.width//2 - w//2,
            player.y + player.height - h + 42
        ))

        # TUTO
        if show_tuto:
            t = font.render(TEXTS[lang]["tutorial"], True, (255,255,255))
            temp.blit(t, (200, 50))
            tuto_timer += 1
            if tuto_timer > 300:
                show_tuto = False

    # ======================
    # DEAD — écran de mort stylé
    # ======================
    elif state == "dead":
        death_screen.update(temp, player)

        if death_screen.done:
            projectiles.clear()
            projectile_timer = 0
            state = "menu"

    # ======================
    # WIN
    # ======================
    elif state == "win":
        temp.fill((255,255,255))
        win_text = TEXTS[lang]["win"]
        t = big.render(win_text, True, (40,40,80))
        temp.blit(t, (W//2 - t.get_width()//2, H//2 - t.get_height()//2))

    # ======================
    # PARTICULES
    # ======================
    for p in particles[:]:
        p.update()
        p.draw(temp)
        if p.life <= 0:
            particles.remove(p)

    # ======================
    # SCREEN SHAKE
    # ======================
    if screen_shake > 0:
        ox = random.randint(-int(screen_shake), int(screen_shake))
        oy = random.randint(-int(screen_shake), int(screen_shake))
        screen_shake = max(screen_shake - 1, 0)
    else:
        ox = random.randint(-int(shake), int(shake))
        oy = random.randint(-int(shake), int(shake))

    shake *= 0.85

    # ======================
    # AFFICHAGE FINAL
    # ======================
    screen.blit(temp, (ox, oy))

    if state == "intro" and intro_text_surface:
        screen.blit(intro_text_surface,
                    (W//2 - intro_text_surface.get_width()//2, 250))

    pygame.display.flip()

pygame.quit()