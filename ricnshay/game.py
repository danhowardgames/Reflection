import pygame
import sys
from settings import *
from player import Player
from shay import Shay
from laser import Laser
from enemy import EnemySpawner

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
    
    def update(self, dt):
        """Update game state and all entities"""
        # Get all pressed keys
        self.keys = pygame.key.get_pressed()
        
        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        
        # Update based on game state
        if self.game_state == GAME_STATE_MENU:
            # Menu logic
            pass
            
        elif self.game_state == GAME_STATE_WAVE_TRANSITION or self.game_state == GAME_STATE_PLAYING:
            # Update Shay
            self.shay.update(dt, mouse_pos, self.keys)
            
            # Update player and get laser direction if fired
            laser_direction = self.player.update(dt, self.keys, self.shay.pos)
            
            # If laser was fired, activate it
            if laser_direction:
                hit_enemy = self.laser.fire(
                    self.player.pos, 
                    self.shay.pos, 
                    self.shay, 
                    self.walls, 
                    self.enemy_spawner.enemies
                )
                
                # Handle enemy hit if any
                if hit_enemy:
                    self.enemy_spawner.handle_laser_hit(hit_enemy)
            
            # Update enemies if in playing state
            if self.game_state == GAME_STATE_PLAYING:
                player_hit = self.enemy_spawner.update(dt, self.player.pos, self.player.rect)
                
                # Check if player was hit
                if player_hit:
                    game_over = self.player.take_damage()
                    if game_over:
                        self.game_state = GAME_STATE_GAME_OVER
            
            # Update enemy spawner for wave transitions
            else:
                wave_result = self.enemy_spawner.update(dt, self.player.pos, self.player.rect)
                
                # If wave has started, change state
                if wave_result is not None:
                    if wave_result:  # New wave started
                        self.game_state = GAME_STATE_PLAYING
                    else:  # No more waves, game won
                        self.game_state = GAME_STATE_VICTORY
            
            # Deactivate laser after one frame
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
            self.shay.draw(self.screen, self.player.pos)
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