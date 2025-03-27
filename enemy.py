import pygame
import math
import random
from settings import *
from utils import normalize_vector, vector_to_angle, vector_from_angle

class Enemy:
    def __init__(self, pos, speed, wave_num):
        self.pos = pos
        self.speed = speed
        self.wave_num = wave_num
        self.rect = pygame.Rect(0, 0, ENEMY_SIZE, ENEMY_SIZE)
        self.rect.center = self.pos
        self.color = ENEMY_COLORS[min(wave_num - 1, len(ENEMY_COLORS) - 1)]
        
        # Set random vulnerable angle (the back of the enemy)
        self.movement_angle = random.uniform(0, 360)
        self.vulnerable_angle = (self.movement_angle + 180) % 360
        
        # State management
        self.STATE_IDLE = 0
        self.STATE_MOVING = 1
        self.STATE_DYING = 2
        self.state = self.STATE_MOVING
        self.death_timer = 0
        self.death_duration = 0.5  # seconds
    
    def update(self, dt, player_pos):
        if self.state == self.STATE_DYING:
            self.death_timer += dt
            if self.death_timer >= self.death_duration:
                return True  # Enemy should be removed
            return False
            
        if self.state == self.STATE_IDLE:
            return False
            
        # Calculate direction to player
        direction = (player_pos[0] - self.pos[0], player_pos[1] - self.pos[1])
        direction = normalize_vector(direction)
        
        # Update movement angle
        self.movement_angle = vector_to_angle(direction)
        self.vulnerable_angle = (self.movement_angle + 180) % 360
        
        # Move towards player
        self.pos = (
            self.pos[0] + direction[0] * self.speed * dt,
            self.pos[1] + direction[1] * self.speed * dt
        )
        self.rect.center = self.pos
        
        # Check if collided with player
        return False
    
    def check_player_collision(self, player_rect, player_invulnerable=False):
        """Check if enemy has collided with the player"""
        return self.rect.colliderect(player_rect) if self.state == self.STATE_MOVING else False
    
    def hit(self):
        """Enemy is hit by laser from vulnerable direction"""
        self.state = self.STATE_DYING
        self.death_timer = 0
        return True
    
    def draw(self, surface):
        # Draw enemy with different appearance based on state
        if self.state == self.STATE_DYING:
            # Draw death animation (pulsing/fading)
            alpha = int(255 * (1 - self.death_timer / self.death_duration))
            size_mod = int(ENEMY_SIZE * (1 + self.death_timer / self.death_duration))
            
            # Create a surface with per-pixel alpha
            s = pygame.Surface((size_mod, size_mod), pygame.SRCALPHA)
            s.fill((self.color[0], self.color[1], self.color[2], alpha))
            surface.blit(s, (self.pos[0] - size_mod // 2, self.pos[1] - size_mod // 2))
        else:
            # Draw regular enemy
            pygame.draw.rect(surface, self.color, self.rect)
            
            # Draw arrow indicating direction
            center = self.rect.center
            front_point = (
                center[0] + math.cos(math.radians(self.movement_angle)) * ENEMY_SIZE * 0.5,
                center[1] + math.sin(math.radians(self.movement_angle)) * ENEMY_SIZE * 0.5
            )
            
            left_point = (
                center[0] + math.cos(math.radians(self.movement_angle - 140)) * ENEMY_SIZE * 0.3,
                center[1] + math.sin(math.radians(self.movement_angle - 140)) * ENEMY_SIZE * 0.3
            )
            
            right_point = (
                center[0] + math.cos(math.radians(self.movement_angle + 140)) * ENEMY_SIZE * 0.3,
                center[1] + math.sin(math.radians(self.movement_angle + 140)) * ENEMY_SIZE * 0.3
            )
            
            pygame.draw.polygon(surface, (255, 255, 255), [front_point, left_point, right_point])
        
        # Debug - show vulnerable arc if debug is enabled
        if DEBUG_MODE:
            arc_center = self.rect.center
            start_angle = (self.vulnerable_angle - VULNERABLE_ARC_SIZE / 2) % 360
            end_angle = (self.vulnerable_angle + VULNERABLE_ARC_SIZE / 2) % 360
            
            # Draw vulnerable direction with a colored arc
            pygame.draw.arc(
                surface,
                DEBUG_COLOR,
                pygame.Rect(
                    arc_center[0] - ENEMY_SIZE,
                    arc_center[1] - ENEMY_SIZE,
                    ENEMY_SIZE * 2,
                    ENEMY_SIZE * 2
                ),
                math.radians(start_angle),
                math.radians(end_angle),
                3
            )

class EnemySpawner:
    def __init__(self, walls):
        self.walls = walls
        self.current_wave = 0
        self.enemies = []
        self.spawn_timer = 0
        self.wave_enemies_left = 0
        self.wave_transition_timer = 0
        self.in_wave_transition = True
    
    def start_wave(self):
        """Start a new wave of enemies"""
        self.current_wave += 1
        if self.current_wave > TOTAL_WAVES:
            return False  # No more waves, game is won
            
        # Calculate number of enemies for this wave
        num_enemies = ENEMY_COUNT_BASE + (self.current_wave - 1) * ENEMY_COUNT_INCREASE
        self.wave_enemies_left = num_enemies
        
        # Calculate spawn delay for this wave
        self.spawn_delay = max(0.5, SPAWN_DELAY_BASE - (self.current_wave - 1) * SPAWN_DELAY_DECREASE)
        
        # Calculate enemy speed for this wave
        self.enemy_speed = ENEMY_BASE_SPEED * (ENEMY_SPEED_INCREASE ** (self.current_wave - 1))
        
        # Reset timers
        self.spawn_timer = 0
        self.wave_transition_timer = 0
        self.in_wave_transition = False
        
        return True
    
    def start_wave_transition(self):
        """Begin transition to next wave"""
        self.wave_transition_timer = 0
        self.in_wave_transition = True
    
    def update(self, dt, player_pos, player_rect, player_invulnerable=False):
        """Update enemy spawning and all existing enemies"""
        # Handle wave transition
        if self.in_wave_transition:
            self.wave_transition_timer += dt
            if self.wave_transition_timer >= WAVE_TRANSITION_TIME:
                return self.start_wave()
            return None
            
        # Check if wave is complete
        if self.wave_enemies_left <= 0 and len(self.enemies) == 0:
            self.start_wave_transition()
            return None
            
        # Update spawn timer
        self.spawn_timer += dt
        
        # Spawn new enemy if it's time and we have enemies left to spawn
        if self.spawn_timer >= self.spawn_delay and self.wave_enemies_left > 0:
            self.spawn_enemy(player_pos)
            self.spawn_timer = 0
            self.wave_enemies_left -= 1
            
        # Update all enemies
        player_hit = False
        enemies_to_remove = []
        
        for enemy in self.enemies:
            should_remove = enemy.update(dt, player_pos)
            
            if should_remove:
                enemies_to_remove.append(enemy)
            elif enemy.check_player_collision(player_rect):
                if not player_invulnerable:
                    # Only register a hit if player is not invulnerable
                    player_hit = True
        
        # Remove dead enemies
        for enemy in enemies_to_remove:
            if enemy in self.enemies:  # Ensure it's still in the list
                self.enemies.remove(enemy)
                
        return player_hit
    
    def spawn_enemy(self, player_pos):
        """Spawn a new enemy at a random position away from the player"""
        # Don't spawn too close to player
        min_distance = 200
        max_tries = 50
        
        for _ in range(max_tries):
            # Pick a random position at the edge of the screen
            side = random.randint(0, 3)
            if side == 0:  # Top
                pos = (random.randint(50, WIDTH - 50), 50)
            elif side == 1:  # Right
                pos = (WIDTH - 50, random.randint(50, HEIGHT - 50))
            elif side == 2:  # Bottom
                pos = (random.randint(50, WIDTH - 50), HEIGHT - 50)
            else:  # Left
                pos = (50, random.randint(50, HEIGHT - 50))
                
            # Check if position is far enough from player
            dist = math.sqrt((pos[0] - player_pos[0])**2 + (pos[1] - player_pos[1])**2)
            if dist >= min_distance:
                # Check if position doesn't collide with walls
                temp_rect = pygame.Rect(0, 0, ENEMY_SIZE, ENEMY_SIZE)
                temp_rect.center = pos
                
                if not any(temp_rect.colliderect(wall) for wall in self.walls):
                    # Valid position, create enemy
                    enemy = Enemy(pos, self.enemy_speed, self.current_wave)
                    self.enemies.append(enemy)
                    return
        
        # If we couldn't find a valid position after max_tries, spawn anyway at a random edge
        side = random.randint(0, 3)
        if side == 0:
            pos = (random.randint(50, WIDTH - 50), 50)
        elif side == 1:
            pos = (WIDTH - 50, random.randint(50, HEIGHT - 50))
        elif side == 2:
            pos = (random.randint(50, WIDTH - 50), HEIGHT - 50)
        else:
            pos = (50, random.randint(50, HEIGHT - 50))
            
        enemy = Enemy(pos, self.enemy_speed, self.current_wave)
        self.enemies.append(enemy)
    
    def handle_laser_hit(self, enemy):
        """Enemy was hit by laser"""
        if enemy in self.enemies:
            enemy.hit()
            
    def draw(self, surface):
        """Draw all enemies"""
        for enemy in self.enemies:
            enemy.draw(surface)
            
        # Draw wave information
        font = pygame.font.SysFont('Arial', 20)
        if self.in_wave_transition and self.current_wave < TOTAL_WAVES:
            wave_text = f"WAVE {self.current_wave + 1}"
            text_surf = font.render(wave_text, True, (255, 255, 255))
            surface.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, HEIGHT // 2 - 50))
            
            # Draw countdown
            time_left = max(0, WAVE_TRANSITION_TIME - self.wave_transition_timer)
            count_text = f"{time_left:.1f}"
            count_surf = font.render(count_text, True, (255, 255, 255))
            surface.blit(count_surf, (WIDTH // 2 - count_surf.get_width() // 2, HEIGHT // 2)) 