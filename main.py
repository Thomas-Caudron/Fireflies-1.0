# Improved main.py

import pygame
import random

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLATFORM_COLOR = (0, 255, 0)
MOVING_PLATFORM_COLOR = (255, 0, 0)
DECORATIVE_PLATFORM_COLOR = (0, 0, 255)
FPS = 60

# Initialize Pygame
pygame.init()

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Fireflies')

# Player properties
player_pos = [400, 300]
player_speed = 5
score = 0

# Platforms
platforms = []

# Create platforms with progressive difficulty
for i in range(5):
    platforms.append(pygame.Rect(random.randint(0, SCREEN_WIDTH - 100), random.randint(100, SCREEN_HEIGHT - 50), 100, 10))

# Function for player movement
def move_player(keys):
    global player_pos
    if keys[pygame.K_LEFT]:
        player_pos[0] -= player_speed
    if keys[pygame.K_RIGHT]:
        player_pos[0] += player_speed

# Function to check collisions
def check_collisions():
    global score
    player_rect = pygame.Rect(player_pos[0], player_pos[1], 50, 50)
    for platform in platforms:
        if player_rect.colliderect(platform):
            score += 1

# Main game loop
running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get keys pressed
    keys = pygame.key.get_pressed()
    move_player(keys)
    check_collisions()

    # Fill screen
    screen.fill((0, 0, 0))  # Black background 

    # Draw platforms
    for platform in platforms:
        pygame.draw.rect(screen, PLATFORM_COLOR, platform)

    # Display score
    font = pygame.font.Font(None, 36)
    text = font.render(f'Score: {score}', True, (255, 255, 255))
    screen.blit(text, (10, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()