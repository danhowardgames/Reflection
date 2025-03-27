import pygame
import math
from settings import *
from utils import normalize_vector, distance

class Player:
    def __init__(self, pos, walls):
        self.pos = pos
        self.walls = walls
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.center = self.pos
        self.health = PLAYER_MAX_HEALTH
        self.velocity = [0, 0]
        self.laser_cooldown_timer = 0
        self.can_fire = True
        
    def move(self, dt, keys):
        # Reset velocity
        self.velocity = [0, 0]
        
        # Check input
        if keys[pygame.K_w]:
            self.velocity[1] -= 1
        if keys[pygame.K_s]:
            self.velocity[1] += 1
        if keys[pygame.K_a]:
            self.velocity[0] -= 1
        if keys[pygame.K_d]:
            self.velocity[0] += 1
            
        # Normalize velocity if moving diagonally
        if self.velocity[0] != 0 or self.velocity[1] != 0:
            self.velocity = normalize_vector(self.velocity)
            
            # Calculate new position with speed and delta time
            new_x = self.pos[0] + self.velocity[0] * PLAYER_SPEED * dt
            new_y = self.pos[1] + self.velocity[1] * PLAYER_SPEED * dt
            
            # Check wall collision for X movement
            temp_rect = self.rect.copy()
            temp_rect.centerx = new_x
            
            if not any(temp_rect.colliderect(wall) for wall in self.walls):
                self.pos = (new_x, self.pos[1])
            
            # Check wall collision for Y movement
            temp_rect = self.rect.copy()
            temp_rect.centery = new_y
            
            if not any(temp_rect.colliderect(wall) for wall in self.walls):
                self.pos = (self.pos[0], new_y)
            
            # Update rectangle position
            self.rect.center = self.pos
    
    def update_laser_cooldown(self, dt):
        if not self.can_fire:
            self.laser_cooldown_timer += dt
            if self.laser_cooldown_timer >= LASER_COOLDOWN:
                self.can_fire = True
                self.laser_cooldown_timer = 0
    
    def fire_laser(self, shay_pos):
        if self.can_fire:
            self.can_fire = False
            self.laser_cooldown_timer = 0
            # Calculate direction vector from Ric to Shay
            direction = (shay_pos[0] - self.pos[0], shay_pos[1] - self.pos[1])
            # Return the direction for the laser to follow
            return direction
        return None
    
    def take_damage(self):
        self.health -= 1
        return self.health <= 0
    
    def update(self, dt, keys, shay_pos):
        self.move(dt, keys)
        self.update_laser_cooldown(dt)
        
        # Fire laser if the space key is pressed
        laser_direction = None
        if keys[pygame.K_SPACE]:
            laser_direction = self.fire_laser(shay_pos)
        
        return laser_direction
    
    def draw(self, surface):
        # Draw the player character
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect)
        
        # Draw health indicators
        for i in range(self.health):
            health_rect = pygame.Rect(10 + i * 30, 10, 20, 20)
            pygame.draw.rect(surface, (255, 0, 0), health_rect)
        
        # Debug - draw collision rect if debug is enabled
        if DEBUG_MODE:
            pygame.draw.rect(surface, DEBUG_COLOR, self.rect, 1) 