import pygame
import random
import os
import sys
import math

# --- INITIALIZATION ---
pygame.init()

# --- EXE COMPATIBILITY SETUP ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Screen Setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders: COMMANDER")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)

# --- HIGH SCORE SYSTEM ---
HIGHSCORE_FILE = "highscore.txt"

def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                return int(f.read())
        except:
            return 0
    return 0

def save_highscore(score):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(score))

# --- ASSET LOADING ---
def load_sprite(filename, size, remove_black=True):
    path = resource_path(os.path.join("assets", filename))
    if not os.path.exists(path): return None

    img = pygame.image.load(path)
    if remove_black:
        img = img.convert_alpha()
        w, h = img.get_size()
        for x in range(w):
            for y in range(h):
                if img.get_at((x, y))[:3] == (0, 0, 0):
                    img.set_at((x, y), (0, 0, 0, 0))
    else:
        img = img.convert() 
    return pygame.transform.smoothscale(img, size)

# Load Assets
bg_img = load_sprite("background.png", (WIDTH, HEIGHT), remove_black=False)
player_img = load_sprite("spaceship.png", (50, 50), remove_black=True)
enemy_img = load_sprite("enemy.png", (40, 30), remove_black=True)
boss_img = load_sprite("Boss.png", (150, 100), remove_black=True)

if not boss_img:
    boss_img = pygame.Surface((150, 100), pygame.SRCALPHA)
    pygame.draw.polygon(boss_img, (150, 0, 0), [(75, 100), (0, 0), (150, 0)])

# Dark overlay
dark_overlay = pygame.Surface((WIDTH, HEIGHT))
dark_overlay.set_alpha(80) 
dark_overlay.fill((0, 0, 0))

# --- CLASSES ---

class Particle:
    """ Advanced debris particle """
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        # Explosive velocity
        angle = random.uniform(0, 6.28)
        speed = random.uniform(2, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.life = random.randint(20, 40)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(3, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        
        # Friction (slow down)
        self.vx *= 0.95 
        self.vy *= 0.95
        
        self.life -= 1
        # Shrink over time
        if self.life < 10:
            self.size *= 0.9

    def draw(self, surface):
        if self.life > 0:
            # Fade out alpha
            alpha = int((self.life / self.max_life) * 255)
            # Create a temporary surface for transparency if needed, 
            # but usually solid circles look fine for pixel art style.
            # We will mix the color with white to make it look "hot" at the start
            c = self.color
            if self.life > self.max_life * 0.8:
                c = (255, 255, 255) # Flash white at birth
                
            pygame.draw.circle(surface, c, (int(self.x), int(self.y)), int(self.size))

class Shockwave:
    """ Expanding ring effect """
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = 5
        self.life = 15
        self.color = color
        self.width = 3

    def update(self):
        self.radius += 4 # Expand fast
        self.width = max(1, self.width - 0.2)
        self.life -= 1

    def draw(self, surface):
        if self.life > 0 and self.width > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius), int(self.width))

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 30)
        self.row_y = y 
        self.state = "formation" 
        self.vx = 0
        self.vy = 0

    def update(self, fleet_speed, fleet_dir, ship_x, ship_y):
        if self.state == "formation":
            self.rect.x += fleet_speed * fleet_dir
            # Wave Movement
            time_factor = pygame.time.get_ticks() / 300 
            wave_offset = math.sin(time_factor + self.rect.x * 0.02) * 15
            self.rect.y = self.row_y + wave_offset

        elif self.state == "diving":
            dx = ship_x - self.rect.x
            dy = ship_y - self.rect.y
            dist = math.hypot(dx, dy)
            if dist != 0:
                self.rect.x += (dx / dist) * 4
                self.rect.y += (dy / dist) * 4
            
            if self.rect.y > HEIGHT:
                self.rect.y = 0
                self.row_y = 0 
                self.state = "formation"

class Boss:
    def __init__(self, hp):
        self.rect = pygame.Rect(WIDTH//2 - 75, 50, 150, 100)
        self.hp = hp
        self.max_hp = hp
        self.speed = 3
        self.direction = 1
        self.shoot_timer = 0

    def update(self):
        self.rect.x += self.speed * self.direction
        self.rect.y = 50 + math.sin(pygame.time.get_ticks() / 500) * 20
        
        if self.rect.right > WIDTH or self.rect.left < 0:
            self.direction *= -1
        
        self.shoot_timer += 1

    def draw(self, surface):
        surface.blit(boss_img, (self.rect.x, self.rect.y))
        pygame.draw.rect(surface, (50, 50, 50), (self.rect.x, self.rect.y - 15, 150, 10))
        pct = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (255, 0, 0), (self.rect.x, self.rect.y - 15, 150 * pct, 10))

class MysteryShip:
    def __init__(self):
        self.width = 60
        self.height = 30
        self.direction = random.choice([-1, 1])
        x = -60 if self.direction == 1 else WIDTH + 60
        self.rect = pygame.Rect(x, 45, self.width, self.height)
        self.speed = 3
        self.active = True

    def update(self):
        self.rect.x += self.speed * self.direction
        if (self.direction == 1 and self.rect.x > WIDTH) or \
           (self.direction == -1 and self.rect.right < 0):
            self.active = False

    def draw(self, surface):
        pygame.draw.ellipse(surface, (255, 0, 0), self.rect)
        pygame.draw.ellipse(surface, (50, 255, 255), (self.rect.centerx-10, self.rect.y-5, 20, 15))

class PowerUp:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.type = random.choice(['multi', 'shield', 'speed'])
        self.speed = 3

    def update(self):
        self.rect.y += self.speed

    def draw(self, surface):
        if self.type == 'multi': color = (255, 255, 0); char = "M"
        elif self.type == 'shield': color = (0, 100, 255); char = "S"
        else: color = (0, 255, 100); char = ">>"
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        surface.blit(pygame.font.Font(None,20).render(char, True, (0,0,0)), (self.rect.x+4, self.rect.y+4))

# --- GAME ENGINE ---

class Game:
    def __init__(self):
        self.bg_y = 0 
        self.high_score = load_highscore()
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.particles = []
        self.shockwaves = [] # New list for rings
        self.powerups = []
        self.ufo = None
        self.boss = None  
        self.shield_active = False
        self.multishot_active = False
        self.speed_boost_active = False
        self.ability_timer = 0
        self.shake_timer = 0 # Screen shake
        self.setup_player()
        self.setup_level()

    def setup_player(self):
        self.ship_x = WIDTH // 2
        self.ship_y = HEIGHT - 70
        self.bullets = [] 

    def setup_level(self):
        self.enemies = []
        self.enemy_bullets = []
        self.ufo = None
        # Keep particles/shockwaves for transition effect
        
        if self.level % 5 == 0:
            self.boss = Boss(100 + (self.level * 10))
            self.enemies = [] 
        else:
            self.boss = None
            self.fleet_direction = 1 
            self.fleet_speed = 2 + (self.level * 0.5)
            rows = 3 + (self.level // 2)
            cols = 8
            for row in range(min(rows, 6)):
                for col in range(cols):
                    self.enemies.append(Enemy(100 + col * 60, 50 + row * 50))

    def shoot(self):
        if self.game_over: return
        if self.multishot_active:
             bullets_to_fire = [
                 pygame.Rect(self.ship_x + 23, self.ship_y, 4, 10),
                 pygame.Rect(self.ship_x + 8, self.ship_y + 10, 4, 10),
                 pygame.Rect(self.ship_x + 38, self.ship_y + 10, 4, 10)
             ]
             self.bullets.extend(bullets_to_fire)
        else:
            if len(self.bullets) < 5:
                self.bullets.append(pygame.Rect(self.ship_x + 23, self.ship_y, 4, 10))

    def create_explosion(self, x, y, color, intensity=1):
        """ Creates particles and a shockwave """
        # Shockwave Ring
        self.shockwaves.append(Shockwave(x, y, (255, 255, 255)))
        
        # Debris
        count = 20 * intensity
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
            
        # Screen Shake (only for player or high intensity)
        if intensity > 1 or color == (255, 50, 50): 
            self.shake_timer = 10 * intensity

    def update(self):
        self.bg_y += 0.5  
        if self.bg_y >= HEIGHT: self.bg_y = 0
        
        if self.score > self.high_score: self.high_score = self.score
        if self.game_over: return

        # Decrease Shake
        if self.shake_timer > 0:
            self.shake_timer -= 1

        speed = 9 if self.speed_boost_active else 5
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.ship_x > 0:
            self.ship_x -= speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.ship_x < WIDTH - 50:
            self.ship_x += speed

        if self.ability_timer > 0:
            self.ability_timer -= 1
            if self.ability_timer <= 0:
                self.multishot_active = False
                self.speed_boost_active = False

        if self.boss:
            self.boss.update()
            if self.boss.shoot_timer > 60:
                self.boss.shoot_timer = 0
                self.enemy_bullets.append(pygame.Rect(self.boss.rect.centerx, self.boss.rect.bottom, 8, 20))
                self.enemy_bullets.append(pygame.Rect(self.boss.rect.left + 20, self.boss.rect.bottom, 8, 20))
                self.enemy_bullets.append(pygame.Rect(self.boss.rect.right - 20, self.boss.rect.bottom, 8, 20))
                
            if self.boss.hp <= 0:
                self.score += 1000
                self.create_explosion(self.boss.rect.centerx, self.boss.rect.centery, (255, 200, 0), intensity=3)
                self.boss = None
                self.level += 1
                self.setup_level()
        
        else:
            if random.random() < 0.005:
                formation_enemies = [e for e in self.enemies if e.state == "formation"]
                if formation_enemies:
                    diver = random.choice(formation_enemies)
                    diver.state = "diving"

            move_down = False
            for enemy in self.enemies:
                enemy.update(self.fleet_speed, self.fleet_direction, self.ship_x, self.ship_y)
                if enemy.state == "formation":
                    if enemy.rect.right >= WIDTH or enemy.rect.left <= 0:
                        move_down = True
            
            if move_down:
                self.fleet_direction *= -1
                for enemy in self.enemies:
                    if enemy.state == "formation":
                        enemy.row_y += 20 
                        enemy.rect.x += 5 * self.fleet_direction

            if self.ufo is None and random.random() < 0.002:
                self.ufo = MysteryShip()
            if self.ufo:
                self.ufo.update()
                if not self.ufo.active: self.ufo = None

            if self.enemies and random.random() < 0.02:
                shooter = random.choice(self.enemies)
                self.enemy_bullets.append(pygame.Rect(shooter.rect.centerx, shooter.rect.bottom, 6, 15))

            if not self.enemies:
                self.level += 1
                self.setup_level()

            for enemy in self.enemies:
                if enemy.rect.bottom > self.ship_y:
                    self.lives = 0
                    self.game_over = True
                    save_highscore(self.high_score)

        for b in self.bullets[:]:
            b.y -= 10
            if b.y < 0: self.bullets.remove(b)
            
        # Update particles & shockwaves
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles: p.update()
        
        self.shockwaves = [s for s in self.shockwaves if s.life > 0]
        for s in self.shockwaves: s.update()
        
        self.powerups = [p for p in self.powerups if p.rect.y < HEIGHT]
        for p in self.powerups: p.update()

        self.check_collisions()

    def check_collisions(self):
        player_rect = pygame.Rect(self.ship_x, self.ship_y, 50, 50)

        for b in self.bullets[:]:
            b_rect = pygame.Rect(b.x, b.y, 4, 10)
            hit = False
            
            if self.boss and b_rect.colliderect(self.boss.rect):
                self.boss.hp -= 1
                # Small spark on hit
                self.create_explosion(b.x, b.y, (255, 100, 0), intensity=0.2)
                self.bullets.remove(b)
                continue

            if self.ufo and b_rect.colliderect(self.ufo.rect):
                self.score += 500
                self.create_explosion(self.ufo.rect.centerx, self.ufo.rect.centery, (255, 0, 0), intensity=2)
                self.ufo = None
                self.bullets.remove(b)
                continue

            for enemy in self.enemies[:]:
                if b_rect.colliderect(enemy.rect):
                    self.enemies.remove(enemy)
                    self.score += 10
                    # Standard Cyan Explosion
                    self.create_explosion(enemy.rect.centerx, enemy.rect.centery, (0, 255, 255), intensity=1)
                    if random.random() < 0.1: self.powerups.append(PowerUp(enemy.rect.centerx, enemy.rect.centery))
                    hit = True
                    break
            if hit: self.bullets.remove(b)

        for b in self.enemy_bullets[:]:
            b.y += 5
            if b.colliderect(player_rect):
                self.enemy_bullets.remove(b)
                if self.shield_active:
                    self.shield_active = False 
                    self.create_explosion(self.ship_x + 25, self.ship_y + 25, (0, 100, 255), intensity=1)
                else:
                    self.lives -= 1
                    # Red Player Explosion
                    self.create_explosion(self.ship_x + 25, self.ship_y + 25, (255, 50, 50), intensity=2)
                    if self.lives <= 0: 
                        self.game_over = True
                        save_highscore(self.high_score)
            elif b.y > HEIGHT:
                self.enemy_bullets.remove(b)

        for enemy in self.enemies[:]:
            if enemy.state == "diving" and player_rect.colliderect(enemy.rect):
                self.enemies.remove(enemy)
                self.lives -= 1
                self.create_explosion(self.ship_x + 25, self.ship_y + 25, (255, 50, 50), intensity=2)
                if self.lives <= 0: 
                    self.game_over = True
                    save_highscore(self.high_score)

        for p in self.powerups[:]:
            if player_rect.colliderect(p.rect):
                if p.type == 'multi':
                    self.multishot_active = True
                    self.ability_timer = 600
                elif p.type == 'speed':
                    self.speed_boost_active = True
                    self.ability_timer = 600
                elif p.type == 'shield':
                    self.shield_active = True
                self.powerups.remove(p)

    def draw(self):
        # Screen Shake Offset
        shake_x, shake_y = 0, 0
        if self.shake_timer > 0:
            shake_x = random.randint(-4, 4)
            shake_y = random.randint(-4, 4)

        if bg_img:
            screen.blit(bg_img, (0 + shake_x, self.bg_y + shake_y))
            screen.blit(bg_img, (0 + shake_x, self.bg_y - HEIGHT + shake_y))
        else:
            screen.fill((10, 10, 30))
        
        # Draw everything with offset if needed, but usually just shaking BG is enough
        # to convey the feeling without breaking UI alignment
        screen.blit(dark_overlay, (0, 0))

        if player_img: screen.blit(player_img, (self.ship_x, self.ship_y))
        else: pygame.draw.rect(screen, (0, 255, 0), (self.ship_x, self.ship_y, 50, 50))

        if self.shield_active:
            pygame.draw.circle(screen, (0, 100, 255), (self.ship_x+25, self.ship_y+25), 40, 2)

        if self.boss:
            self.boss.draw(screen)
        else:
            for enemy in self.enemies:
                if enemy_img: screen.blit(enemy_img, (enemy.rect.x, enemy.rect.y))
                else: pygame.draw.rect(screen, (255, 0, 0), enemy.rect)

        if self.ufo: self.ufo.draw(screen)
        for p in self.powerups: p.draw(screen)

        for b in self.bullets:
            color = (255, 255, 0) if self.multishot_active else (0, 255, 255)
            pygame.draw.rect(screen, color, (b.x, b.y, 4, 10))
        for b in self.enemy_bullets:
            pygame.draw.rect(screen, (255, 50, 50), b)
        
        # Draw Explosions (Particles & Shockwaves)
        for s in self.shockwaves: s.draw(screen)
        for p in self.particles: p.draw(screen)

        screen.blit(font.render(f"SCORE: {self.score}", True, (255, 255, 255)), (10, 10))
        screen.blit(font.render(f"HI-SCORE: {self.high_score}", True, (255, 215, 0)), (300, 10))
        screen.blit(font.render(f"LEVEL: {self.level}", True, (0, 255, 0)), (WIDTH - 130, 10))
        
        if self.ability_timer > 0:
            if self.multishot_active:
                screen.blit(font.render("MULTI-SHOT", True, (255, 255, 0)), (WIDTH//2 - 70, HEIGHT - 30))
            elif self.speed_boost_active:
                screen.blit(font.render("SPEED BOOST", True, (0, 255, 100)), (WIDTH//2 - 70, HEIGHT - 30))

        for i in range(self.lives):
            pygame.draw.polygon(screen, (200, 50, 50), [
                (20 + i*30, 50), (30 + i*30, 70), (10 + i*30, 70)
            ])

        if self.game_over:
            over_text = big_font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(over_text, (WIDTH//2 - 150, HEIGHT//2 - 50))
            restart_text = font.render("Press R to Restart", True, (200, 200, 200))
            screen.blit(restart_text, (WIDTH//2 - 100, HEIGHT//2 + 20))

        pygame.display.flip()

# --- MAIN LOOP ---
game = Game()
running = True

while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            save_highscore(game.high_score)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: game.shoot()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE: game.shoot()
            if event.key == pygame.K_r and game.game_over: game.reset_game()

    game.update()
    game.draw()

pygame.quit()
sys.exit()