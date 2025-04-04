import pygame
import sys
from settings import *
from player import Player, PLAYER_STATE_MOVING, PLAYER_STATE_FIRING
from shay import Shay
from laser import Laser
from enemy import EnemySpawner
from utils import distance

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.game_state = GAME_STATE_MENU
        self.debug_mode = DEBUG_MODE
        self.keys = {}
        self.setup_level()
        
    def setup_level(self):
        """Set up the game level and entities"""
        # Create walls (boundaries)
        self.walls = [
            pygame.Rect(0, 0, WIDTH, 20),  # Top wall
            pygame.Rect(0, 0, 20, HEIGHT),  # Left wall
            pygame.Rect(0, HEIGHT - 20, WIDTH, 20),  # Bottom wall
            pygame.Rect(WIDTH - 20, 0, 20, HEIGHT),  # Right wall
            
            # Add some obstacles in the level
            pygame.Rect(WIDTH // 4, HEIGHT // 3, 100, 100),
            pygame.Rect(WIDTH * 3 // 4 - 100, HEIGHT * 2 // 3 - 100, 100, 100),
            pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 - 50, 100, 20),
        ]
        
        # Create player and Shay
        player_pos = (WIDTH // 4, HEIGHT // 2)
        self.player = Player(player_pos, self.walls)
        
        shay_pos = (WIDTH * 3 // 4, HEIGHT // 2)
        self.shay = Shay(shay_pos)
        
        # Create laser
        self.laser = Laser()
        
        # Create enemy spawner
        self.enemy_spawner = EnemySpawner(self.walls)
        
        # Start first wave
        self.game_state = GAME_STATE_WAVE_TRANSITION
        
    def handle_event(self, event):
        """Handle pygame events"""
        if event.type == pygame.KEYDOWN:
            # Toggle debug mode
            if event.key == pygame.K_F1:
                self.debug_mode = not self.debug_mode
                print(f"Debug mode: {self.debug_mode}")
                
            # Skip wave (debug)
            if event.key == pygame.K_f and self.debug_mode:
                if self.game_state == GAME_STATE_PLAYING:
                    self.enemy_spawner.enemies = []
                    self.enemy_spawner.wave_enemies_left = 0
            
            # God mode toggle (debug)
            if event.key == pygame.K_g and self.debug_mode:
                if self.player.health < PLAYER_MAX_HEALTH:
                    self.player.health = PLAYER_MAX_HEALTH
                else:
                    self.player.health = 999
            
            # Restart after game over/victory
            if event.key == pygame.K_r and (self.game_state == GAME_STATE_GAME_OVER or 
                                           self.game_state == GAME_STATE_VICTORY):
                self.setup_level()
                
            # Start game from menu
            if event.key == pygame.K_SPACE and self.game_state == GAME_STATE_MENU:
                self.game_state = GAME_STATE_WAVE_TRANSITION
            
            # Handle spacebar press for entering firing state
            if event.key == pygame.K_SPACE and self.game_state == GAME_STATE_PLAYING:
                self.player.enter_firing_state()
                
        elif event.type == pygame.KEYUP:
            # Handle spacebar release for firing laser and returning to moving state
            if event.key == pygame.K_SPACE and self.game_state == GAME_STATE_PLAYING:
                # Only fire if player is in firing state (meaning they pressed space earlier)
                if self.player.is_in_firing_state() and self.player.can_fire:
                    print("Firing laser on space key release")
                    laser_direction = self.player.fire_laser(self.shay.pos)
                    
                    # If laser direction is valid, activate it
                    if laser_direction:
                        print(f"Game received laser direction: {laser_direction}")
                        hit_enemy = self.laser.fire(
                            self.player.pos, 
                            self.shay.pos, 
                            self.shay, 
                            self.walls, 
                            self.enemy_spawner.enemies
                        )
                        
                        # Handle enemy hit if any
                        if hit_enemy:
                            print(f"Hit enemy at {hit_enemy.pos}")
                            self.enemy_spawner.handle_laser_hit(hit_enemy)
                
                # Return to moving state
                self.player.enter_moving_state()
    
    def update(self, dt, keys=None, space_just_pressed=False):
        """Update game state and all entities"""
        # Get all pressed keys
        if keys is None:
            self.keys = pygame.key.get_pressed()
        else:
            self.keys = keys
        
        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        
        # Update based on game state
        if self.game_state == GAME_STATE_MENU:
            # Menu logic
            pass
            
        elif self.game_state == GAME_STATE_WAVE_TRANSITION or self.game_state == GAME_STATE_PLAYING:
            # Update Shay
            self.shay.update(dt, mouse_pos, self.keys)
            
            # Update player
            self.player.update(dt, self.keys, self.shay.pos)
            
            # Update laser visual effect
            self.laser.update(dt)
            
            # Update enemies if in playing state
            if self.game_state == GAME_STATE_PLAYING:
                player_hit, _ = self.enemy_spawner.update(
                    dt, 
                    self.player.pos, 
                    self.player.rect,
                    self.player.invulnerable
                )
                
                # Handle player-enemy collision
                if player_hit:
                    # If not invulnerable, take damage and become invulnerable
                    if not self.player.invulnerable:
                        game_over = self.player.take_damage()
                        if game_over:
                            self.game_state = GAME_STATE_GAME_OVER
                            return
                        self.player.make_invulnerable()
                        
                        # Find and destroy the colliding enemy
                        self._destroy_colliding_enemy()
            
            # Update enemy spawner for wave transitions
            else:
                player_hit, wave_result = self.enemy_spawner.update(
                    dt, 
                    self.player.pos, 
                    self.player.rect,
                    self.player.invulnerable  # Pass player invulnerability state
                )
                
                # Handle player-enemy collision during wave transition
                if player_hit:
                    # If not invulnerable, take damage and become invulnerable
                    if not self.player.invulnerable:
                        game_over = self.player.take_damage()
                        if game_over:
                            self.game_state = GAME_STATE_GAME_OVER
                            return
                        self.player.make_invulnerable()
                        
                        # Find and destroy the colliding enemy
                        self._destroy_colliding_enemy()
                
                # Check if wave transition is complete
                if wave_result is not None:
                    if wave_result:  # New wave started
                        print(f"Starting wave {self.enemy_spawner.current_wave}")
                        self.game_state = GAME_STATE_PLAYING
                        
                        # Make player briefly invulnerable when wave starts to avoid
                        # getting hit immediately at wave start
                        self.player.make_invulnerable()
                    else:  # No more waves, game won
                        self.game_state = GAME_STATE_VICTORY
            
            # Deactivate laser game logic after one frame, but let visual effect continue
            if self.laser.active:
                self.laser.deactivate()
    
    def draw(self):
        """Draw the game"""
        # Draw walls
        for wall in self.walls:
            pygame.draw.rect(self.screen, (100, 100, 100), wall)
        
        # Draw based on game state
        if self.game_state == GAME_STATE_MENU:
            # Draw menu
            font = pygame.font.SysFont('Arial', 36)
            title = font.render("Ric 'n' Shay", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
            
            font = pygame.font.SysFont('Arial', 24)
            start = font.render("Press SPACE to start", True, (200, 200, 200))
            self.screen.blit(start, (WIDTH // 2 - start.get_width() // 2, HEIGHT // 2))
            
            controls = font.render("W,A,S,D to move Ric, Mouse to move Shay", True, (200, 200, 200))
            self.screen.blit(controls, (WIDTH // 2 - controls.get_width() // 2, HEIGHT // 2 + 50))
            
            controls2 = font.render("Q,E to rotate ricochet angle, SPACE to fire", True, (200, 200, 200))
            self.screen.blit(controls2, (WIDTH // 2 - controls2.get_width() // 2, HEIGHT // 2 + 80))
            
        elif self.game_state == GAME_STATE_GAME_OVER:
            # Draw game over
            font = pygame.font.SysFont('Arial', 48)
            game_over = font.render("GAME OVER", True, (255, 50, 50))
            self.screen.blit(game_over, (WIDTH // 2 - game_over.get_width() // 2, HEIGHT // 3))
            
            font = pygame.font.SysFont('Arial', 24)
            restart = font.render("Press R to restart", True, (200, 200, 200))
            self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2))
            
            wave = font.render(f"You reached Wave {self.enemy_spawner.current_wave}", True, (200, 200, 200))
            self.screen.blit(wave, (WIDTH // 2 - wave.get_width() // 2, HEIGHT // 2 + 50))
            
        elif self.game_state == GAME_STATE_VICTORY:
            # Draw victory
            font = pygame.font.SysFont('Arial', 48)
            victory = font.render("VICTORY!", True, (50, 255, 50))
            self.screen.blit(victory, (WIDTH // 2 - victory.get_width() // 2, HEIGHT // 3))
            
            font = pygame.font.SysFont('Arial', 24)
            congrats = font.render("You defeated all 5 waves!", True, (200, 200, 200))
            self.screen.blit(congrats, (WIDTH // 2 - congrats.get_width() // 2, HEIGHT // 2))
            
            restart = font.render("Press R to play again", True, (200, 200, 200))
            self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 50))
            
        else:  # Playing or wave transition
            # Draw entities
            self.player.draw(self.screen)
            # Pass the player's firing state to Shay for drawing laser indicators
            self.shay.draw(self.screen, self.player.pos, self.player.is_in_firing_state())
            self.laser.draw(self.screen)
            self.enemy_spawner.draw(self.screen)
            
            # Draw HUD
            font = pygame.font.SysFont('Arial', 20)
            wave_text = f"Wave: {self.enemy_spawner.current_wave}/{TOTAL_WAVES}"
            wave_surf = font.render(wave_text, True, (200, 200, 200))
            self.screen.blit(wave_surf, (WIDTH - wave_surf.get_width() - 20, 15))
            
            enemies_text = f"Enemies: {len(self.enemy_spawner.enemies)} + {self.enemy_spawner.wave_enemies_left} remaining"
            enemies_surf = font.render(enemies_text, True, (200, 200, 200))
            self.screen.blit(enemies_surf, (WIDTH - enemies_surf.get_width() - 20, 40))
            
        # Draw debug info if enabled
        if self.debug_mode:
            font = pygame.font.SysFont('Arial', 14)
            debug_text = f"DEBUG MODE | FPS: {int(pygame.time.Clock().get_fps())} | F: Skip Wave | G: God Mode"
            debug_surf = font.render(debug_text, True, DEBUG_COLOR)
            self.screen.blit(debug_surf, (10, HEIGHT - 20)) 

    def _destroy_colliding_enemy(self):
        """Helper method to find and destroy the enemy that collided with the player"""
        # Find the closest enemy to the player
        min_distance = float('inf')
        colliding_enemy = None
        
        for enemy in self.enemy_spawner.enemies:
            dist = distance(enemy.pos, self.player.pos)
            if dist < min_distance:
                min_distance = dist
                colliding_enemy = enemy
        
        # If we found a close enemy, destroy it
        if colliding_enemy and min_distance < PLAYER_SIZE + ENEMY_SIZE:
            self.enemy_spawner.handle_player_collision(colliding_enemy) 