import pygame
import math
from settings import *
from utils import normalize_vector, distance

# Define player states
PLAYER_STATE_MOVING = 0
PLAYER_STATE_FIRING = 1

class Player:
    def __init__(self, pos, walls):
        self.pos = pos
        self.walls = walls
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.center = self.pos
        self.health = PLAYER_MAX_HEALTH
        self.velocity = [0, 0]
        self.current_velocity = [0, 0]  # Actual velocity with acceleration/deceleration
        self.laser_cooldown_timer = 0
        self.can_fire = True
        
        # State system
        self.state = PLAYER_STATE_MOVING
        
        # Invulnerability state
        self.invulnerable = False
        self.invulnerability_timer = 0
        self.invulnerability_duration = PLAYER_INVULNERABILITY_DURATION
        
    def move(self, dt, keys):
        # Only move if in moving state
        if self.state != PLAYER_STATE_MOVING:
            return
            
        # Get input direction
        input_dir = [0, 0]
        
        if keys[pygame.K_w]:
            input_dir[1] -= 1
        if keys[pygame.K_s]:
            input_dir[1] += 1
        if keys[pygame.K_a]:
            input_dir[0] -= 1
        if keys[pygame.K_d]:
            input_dir[0] += 1
            
        # Normalize input direction if moving diagonally
        if input_dir[0] != 0 or input_dir[1] != 0:
            input_dir = normalize_vector(input_dir)
            
        # Target velocity based on input
        target_velocity = [
            input_dir[0] * PLAYER_MAX_VELOCITY,
            input_dir[1] * PLAYER_MAX_VELOCITY
        ]
        
        # Apply acceleration or deceleration
        for i in range(2):  # For x and y components
            if abs(target_velocity[i]) > abs(self.current_velocity[i]):
                # Accelerate towards target velocity
                if target_velocity[i] > self.current_velocity[i]:
                    self.current_velocity[i] += PLAYER_ACCELERATION * dt * PLAYER_MAX_VELOCITY
                    if self.current_velocity[i] > target_velocity[i]:
                        self.current_velocity[i] = target_velocity[i]
                else:
                    self.current_velocity[i] -= PLAYER_ACCELERATION * dt * PLAYER_MAX_VELOCITY
                    if self.current_velocity[i] < target_velocity[i]:
                        self.current_velocity[i] = target_velocity[i]
            else:
                # Decelerate towards target velocity
                if target_velocity[i] > self.current_velocity[i]:
                    self.current_velocity[i] += PLAYER_DECELERATION * dt * PLAYER_MAX_VELOCITY
                    if self.current_velocity[i] > target_velocity[i]:
                        self.current_velocity[i] = target_velocity[i]
                else:
                    self.current_velocity[i] -= PLAYER_DECELERATION * dt * PLAYER_MAX_VELOCITY
                    if self.current_velocity[i] < target_velocity[i]:
                        self.current_velocity[i] = target_velocity[i]
                        
        # Calculate new position with current velocity and delta time
        if self.current_velocity[0] != 0 or self.current_velocity[1] != 0:
            new_x = self.pos[0] + self.current_velocity[0] * dt
            new_y = self.pos[1] + self.current_velocity[1] * dt
            
            # Check wall collision for X movement
            temp_rect = self.rect.copy()
            temp_rect.centerx = new_x
            
            if not any(temp_rect.colliderect(wall) for wall in self.walls):
                self.pos = (new_x, self.pos[1])
            else:
                # Hit wall, stop horizontal movement
                self.current_velocity[0] = 0
            
            # Check wall collision for Y movement
            temp_rect = self.rect.copy()
            temp_rect.centery = new_y
            
            if not any(temp_rect.colliderect(wall) for wall in self.walls):
                self.pos = (self.pos[0], new_y)
            else:
                # Hit wall, stop vertical movement
                self.current_velocity[1] = 0
            
            # Update rectangle position
            self.rect.center = self.pos
    
    def update_laser_cooldown(self, dt):
        if not self.can_fire:
            self.laser_cooldown_timer += dt
            if self.laser_cooldown_timer >= LASER_COOLDOWN:
                self.can_fire = True
                self.laser_cooldown_timer = 0
                print("Laser ready to fire again")
    
    def fire_laser(self, shay_pos):
        if self.can_fire:
            self.can_fire = False
            self.laser_cooldown_timer = 0
            print(f"Firing laser from {self.pos} to {shay_pos}")
            # Calculate direction vector from Ric to Shay
            direction = (shay_pos[0] - self.pos[0], shay_pos[1] - self.pos[1])
            # Return the direction for the laser to follow
            return direction
        else:
            print(f"Cannot fire yet. Cooldown: {self.laser_cooldown_timer:.2f}/{LASER_COOLDOWN}")
        return None
    
    def take_damage(self):
        # If invulnerable, don't take damage
        if self.invulnerable:
            return False
            
        # Take damage
        self.health -= 1
        
        return self.health <= 0
    
    def make_invulnerable(self):
        """Make the player invulnerable for the set duration"""
        self.invulnerable = True
        self.invulnerability_timer = 0
        
    def enter_firing_state(self):
        """Enter the firing state where player cannot move but shows laser indicator"""
        self.state = PLAYER_STATE_FIRING
        
    def enter_moving_state(self):
        """Enter the moving state where player can move but doesn't show laser indicator"""
        self.state = PLAYER_STATE_MOVING
        
    def is_in_firing_state(self):
        """Check if player is in firing state"""
        return self.state == PLAYER_STATE_FIRING
        
    def update(self, dt, keys, shay_pos):
        self.move(dt, keys)
        self.update_laser_cooldown(dt)
        
        # Update invulnerability
        if self.invulnerable:
            self.invulnerability_timer += dt
            if self.invulnerability_timer >= self.invulnerability_duration:
                self.invulnerable = False
        
        # Update rectangle position just to be sure
        self.rect.center = self.pos
        
    def draw(self, surface):
        # Draw the player character with alpha if invulnerable
        if self.invulnerable:
            # Create a surface with alpha
            alpha = 128 + int(127 * math.sin(self.invulnerability_timer * 10))  # Pulsing effect
            s = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
            s.fill((PLAYER_COLOR[0], PLAYER_COLOR[1], PLAYER_COLOR[2], alpha))
            surface.blit(s, (self.rect.x, self.rect.y))
        else:
            pygame.draw.rect(surface, PLAYER_COLOR, self.rect)
        
        # Draw velocity indicator (motion blur effect)
        if (abs(self.current_velocity[0]) > 50 or abs(self.current_velocity[1]) > 50):
            # Create a motion blur effect
            blur_length = math.sqrt(self.current_velocity[0]**2 + self.current_velocity[1]**2) / PLAYER_MAX_VELOCITY
            blur_alpha = int(150 * blur_length)  # More transparent for slower speeds
            
            # Normalize velocity for direction
            vel_dir = normalize_vector(self.current_velocity)
            
            # Draw blur trail behind player
            blur_surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
            blur_color = (PLAYER_COLOR[0], PLAYER_COLOR[1], PLAYER_COLOR[2], blur_alpha)
            
            # Draw a semi-transparent trail
            for i in range(1, 5):
                trail_pos = (
                    self.rect.centerx - vel_dir[0] * i * 5,
                    self.rect.centery - vel_dir[1] * i * 5
                )
                trail_size = PLAYER_SIZE - i * 3
                if trail_size > 10:  # Don't draw tiny trails
                    trail_rect = pygame.Rect(0, 0, trail_size, trail_size)
                    trail_rect.center = trail_pos
                    trail_alpha = blur_alpha - (i * 25)
                    if trail_alpha > 0:
                        trail_color = (PLAYER_COLOR[0], PLAYER_COLOR[1], PLAYER_COLOR[2], trail_alpha)
                        pygame.draw.rect(surface, trail_color, trail_rect)
        
        # Draw health indicators
        for i in range(self.health):
            health_rect = pygame.Rect(10 + i * 30, 10, 20, 20)
            pygame.draw.rect(surface, (255, 0, 0), health_rect)
        
        # Draw cooldown indicator
        if not self.can_fire:
            cooldown_percentage = self.laser_cooldown_timer / LASER_COOLDOWN
            cooldown_width = 40 * cooldown_percentage
            cooldown_rect = pygame.Rect(10, 40, cooldown_width, 10)
            pygame.draw.rect(surface, (150, 150, 255), cooldown_rect)
            pygame.draw.rect(surface, (100, 100, 200), pygame.Rect(10, 40, 40, 10), 1)
        
        # Debug - draw collision rect if debug is enabled
        if DEBUG_MODE:
            pygame.draw.rect(surface, DEBUG_COLOR, self.rect, 1)
            
            # Draw velocity vector
            vel_magnitude = math.sqrt(self.current_velocity[0]**2 + self.current_velocity[1]**2)
            if vel_magnitude > 5:
                vel_indicator_end = (
                    self.rect.centerx + self.current_velocity[0] * 0.1,
                    self.rect.centery + self.current_velocity[1] * 0.1
                )
                pygame.draw.line(surface, (255, 255, 0), self.rect.center, vel_indicator_end, 2) 