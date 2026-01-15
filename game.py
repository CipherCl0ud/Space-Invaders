import pygame
import random
import os
import math

# --- INITIALIZATION ---
pygame.init()
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Screen Setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders: ULTIMATE")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)

# --- ASSET LOADING ---
def load_sprite(filename, size, remove_black=True):
    path = os.path.join("assets", filename)
    if not os.path.exists(path):
        return None # Return None to trigger code-drawn fallbacks

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

# Fallbacks if images missing
if not player_img:
    player_img = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.polygon(player_img, (0, 255, 0), [(25, 0), (50, 50), (0, 50)])
if not enemy_img:
    enemy_img = pygame.Surface((40, 30), pygame.SRCALPHA)
    pygame.draw.rect(enemy_img, (255, 0, 0), (0, 0, 40, 30))

# Dark overlay for contrast
dark_overlay = pygame.Surface((WIDTH, HEIGHT))
dark_overlay.set_alpha(100) 
dark_overlay.fill((0, 0, 0))

# --- NEW CLASSES ---

class MysteryShip:
    def __init__(self):
        self.width = 60
        self.height = 30
        self.direction = random.choice([-1, 1])
        # Spawn off-screen left or right
        x = -60 if self.direction == 1 else WIDTH + 60
        self.rect = pygame.Rect(x, 45, self.width, self.height)
        self.speed = 3
        self.active = True

    def update(self):
        self.rect.x += self.speed * self.direction
        # Despawn if it leaves screen
        if (self.direction == 1 and self.rect.x > WIDTH) or \
           (self.direction == -1 and self.rect.right < 0):
            self.active = False

    def draw(self, surface):
        # Draw Red Saucer
        pygame.draw.ellipse(surface, (255, 0, 0), self.rect)
        pygame.draw.ellipse(surface, (255, 100, 100), (self.rect.x+15, self.rect.y-5, 30, 15))

class PowerUp:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        # Types: 'multi' (Yellow), 'shield' (Blue), 'speed' (Green)
        self.type = random.choice(['multi', 'shield', 'speed'])
        self.speed = 3

    def update(self):
        self.rect.y += self.speed

    def draw(self, surface):
        if self.type == 'multi':
            color = (255, 255, 0) # Yellow
            label = "M"
        elif self.type == 'shield':
            color = (0, 100, 255) # Blue
            label = "S"
        else:
            color = (0, 255, 100) # Green
            label = ">>"
            
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        # Small text inside
        text = pygame.font.Font(None, 20).render(label, True, (0,0,0))
        surface.blit(text, (self.rect.x + 5, self.rect.y + 4))

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = 20
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 3)

# --- GAME ENGINE ---

class Game:
    def __init__(self):
        self.bg_y = 0 
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.particles = []
        
        # New Feature Lists
        self.powerups = []
        self.ufo = None
        
        # Player Abilities
        self.shield_active = False
        self.multishot_active = False
        self.speed_boost_active = False
        self.ability_timer = 0
        
        self.setup_player()
        self.setup_level()

    def setup_player(self):
        self.ship_x = WIDTH // 2
        self.ship_y = HEIGHT - 70
        self.bullets = [] 

    def setup_level(self):
        self.enemies = []
        self.enemy_bullets = []
        self.fleet_direction = 1 
        self.fleet_speed = 2 + (self.level * 0.5)
        
        rows = 3 + (self.level // 2)
        cols = 8
        for row in range(min(rows, 6)):
            for col in range(cols):
                self.enemies.append(pygame.Rect(100 + col * 60, 50 + row * 50, 40, 30))

    def update(self):
        # Background Scroll
        self.bg_y += 0.7  
        if self.bg_y >= HEIGHT: self.bg_y = 0

        if self.game_over: return

        # --- PLAYER MOVEMENT ---
        speed = 8 if self.speed_boost_active else 5
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.ship_x > 0:
            self.ship_x -= speed
        if keys[pygame.K_RIGHT] and self.ship_x < WIDTH - 50:
            self.ship_x += speed

        # --- TIMERS ---
        if self.ability_timer > 0:
            self.ability_timer -= 1
            if self.ability_timer <= 0:
                self.multishot_active = False
                self.speed_boost_active = False

        # --- UFO SPAWNER ---
        if self.ufo is None and random.random() < 0.002: # 0.2% chance per frame
            self.ufo = MysteryShip()
        
        if self.ufo:
            self.ufo.update()
            if not self.ufo.active:
                self.ufo = None

        # --- BULLETS ---
        for b in self.bullets[:]:
            b.y -= 10
            if b.y < 0: self.bullets.remove(b)

        # --- FLEET ---
        move_down = False
        for enemy in self.enemies:
            enemy.x += self.fleet_speed * self.fleet_direction
            if enemy.right >= WIDTH or enemy.left <= 0:
                move_down = True

        if move_down:
            self.fleet_direction *= -1
            for enemy in self.enemies:
                enemy.y += 20
                if self.fleet_direction == 1: enemy.x += 5
                else: enemy.x -= 5

        # Enemy Shooting
        if self.enemies and random.random() < 0.02:
            shooter = random.choice(self.enemies)
            self.enemy_bullets.append(pygame.Rect(shooter.centerx, shooter.bottom, 6, 15))

        self.check_collisions()

        # Update Particles & Powerups
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles: p.update()
        
        self.powerups = [p for p in self.powerups if p.rect.y < HEIGHT]
        for p in self.powerups: p.update()

        # Levels
        if not self.enemies:
            self.level += 1
            self.setup_level()

        # Game Over Check
        for enemy in self.enemies:
            if enemy.bottom > self.ship_y:
                self.lives = 0
                self.game_over = True

    def check_collisions(self):
        # 1. Player Bullets vs Enemies / UFO
        for b in self.bullets[:]:
            b_rect = pygame.Rect(b.x, b.y, 4, 10)
            hit = False
            
            # Hit UFO?
            if self.ufo and b_rect.colliderect(self.ufo.rect):
                self.score += 500
                self.create_explosion(self.ufo.rect.centerx, self.ufo.rect.centery, (255, 0, 0))
                self.ufo = None
                self.bullets.remove(b)
                continue

            # Hit Enemy?
            for enemy in self.enemies[:]:
                if b_rect.colliderect(enemy):
                    self.enemies.remove(enemy)
                    self.score += 10
                    self.create_explosion(enemy.centerx, enemy.centery, (0, 255, 255))
                    
                    # POWER UP DROP (10% Chance)
                    if random.random() < 0.1:
                        self.powerups.append(PowerUp(enemy.centerx, enemy.centery))
                    
                    hit = True
                    break
            if hit: self.bullets.remove(b)

        # 2. Player vs PowerUps
        player_rect = pygame.Rect(self.ship_x, self.ship_y, 50, 50)
        for p in self.powerups[:]:
            if player_rect.colliderect(p.rect):
                if p.type == 'multi':
                    self.multishot_active = True
                    self.ability_timer = 600 # 10 seconds
                elif p.type == 'speed':
                    self.speed_boost_active = True
                    self.ability_timer = 600
                elif p.type == 'shield':
                    self.shield_active = True
                
                self.powerups.remove(p)

        # 3. Enemy Bullet vs Player
        for b in self.enemy_bullets[:]:
            b.y += 5
            if b.colliderect(player_rect):
                self.enemy_bullets.remove(b)
                
                if self.shield_active:
                    self.shield_active = False # Shield absorbs hit
                    self.create_explosion(self.ship_x + 25, self.ship_y + 25, (100, 100, 255))
                else:
                    self.lives -= 1
                    self.create_explosion(self.ship_x + 25, self.ship_y + 25, (255, 0, 0))
                    if self.lives <= 0:
                        self.game_over = True
            elif b.y > HEIGHT:
                self.enemy_bullets.remove(b)

    def create_explosion(self, x, y, color):
        for _ in range(15):
            self.particles.append(Particle(x, y, color))

    def draw(self):
        # Background
        if bg_img:
            screen.blit(bg_img, (0, self.bg_y))
            screen.blit(bg_img, (0, self.bg_y - HEIGHT))
        else:
            screen.fill((10, 10, 30))
        screen.blit(dark_overlay, (0, 0))

        # Game Objects
        screen.blit(player_img, (self.ship_x, self.ship_y))
        
        # Shield Visual
        if self.shield_active:
            pygame.draw.circle(screen, (0, 100, 255), (self.ship_x+25, self.ship_y+25), 35, 2)

        for enemy in self.enemies:
            screen.blit(enemy_img, (enemy.x, enemy.y))

        if self.ufo:
            self.ufo.draw(screen)

        for p in self.powerups:
            p.draw(screen)

        for b in self.bullets:
            pygame.draw.rect(screen, (255, 255, 0) if self.multishot_active else (0, 255, 255), (b.x, b.y, 4, 10))
        for b in self.enemy_bullets:
            pygame.draw.rect(screen, (255, 50, 50), b)

        for p in self.particles:
            p.draw(screen)

        # UI
        screen.blit(font.render(f"SCORE: {self.score}", True, (255, 255, 255)), (10, 10))
        screen.blit(font.render(f"LEVEL: {self.level}", True, (0, 255, 0)), (WIDTH - 150, 10))
        
        # Ability Text
        if self.ability_timer > 0:
            if self.multishot_active:
                screen.blit(font.render("MULTI-SHOT", True, (255, 255, 0)), (WIDTH//2 - 60, HEIGHT - 30))
            if self.speed_boost_active:
                screen.blit(font.render("SPEED BOOST", True, (0, 255, 100)), (WIDTH//2 - 60, HEIGHT - 30))

        # Lives
        for i in range(self.lives):
            pygame.draw.polygon(screen, (0, 255, 0), [
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
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game.game_over:
                # MULTI SHOT LOGIC
                bullets_to_fire = []
                if game.multishot_active:
                     bullets_to_fire = [
                         pygame.Rect(game.ship_x + 23, game.ship_y, 4, 10),
                         pygame.Rect(game.ship_x + 8, game.ship_y + 10, 4, 10),
                         pygame.Rect(game.ship_x + 38, game.ship_y + 10, 4, 10)
                     ]
                else:
                    bullets_to_fire = [pygame.Rect(game.ship_x + 23, game.ship_y, 4, 10)]

                if len(game.bullets) < 10: # Increased bullet limit for fun
                    game.bullets.extend(bullets_to_fire)
                    
            if event.key == pygame.K_r and game.game_over:
                game.reset_game()

    game.update()
    game.draw()

pygame.quit()