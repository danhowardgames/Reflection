import pygame
import math
from settings import *
from utils import normalize_vector, rotate_vector, vector_to_angle, vector_from_angle

class Shay:
    def __init__(self, pos):
        self.pos = pos
        self.rect = pygame.Rect(0, 0, SHAY_SIZE, SHAY_SIZE)
        self.rect.center = self.pos
        self.target_pos = pos
        self.ricochet_angle = 0  # Current ricochet angle modifier in degrees
        
    def follow_mouse(self, dt, mouse_pos):
        # Set target position to mouse position
        self.target_pos = mouse_pos
        
        # Calculate direction vector to target
        direction = (
            self.target_pos[0] - self.pos[0],
            self.target_pos[1] - self.pos[1]
        )
        
        # Move smoothly towards target if not already at target
        dist = math.sqrt(direction[0]**2 + direction[1]**2)
        if dist > 5:  # Only move if far enough from target
            # Normalize direction and apply smooth follow
            direction = normalize_vector(direction)
            
            # Apply smooth movement
            self.pos = (
                self.pos[0] + direction[0] * dist * SHAY_FOLLOW_SPEED * dt,
                self.pos[1] + direction[1] * dist * SHAY_FOLLOW_SPEED * dt
            )
            
            # Update rectangle position
            self.rect.center = self.pos
    
    def modify_ricochet_angle(self, clockwise=True):
        # Modify ricochet angle by the increment
        if clockwise:
            self.ricochet_angle += RICOCHET_ANGLE_INCREMENT
        else:
            self.ricochet_angle -= RICOCHET_ANGLE_INCREMENT
            
        # Wrap around 360 degrees
        self.ricochet_angle %= 360
    
    def calculate_ricochet_vector(self, incoming_vector, player_pos):
        # Calculate normal vector (perpendicular to the surface of Shay)
        # Simplified as vector from Shay to incoming laser source
        incoming_dir = normalize_vector(incoming_vector)
        normal = (-incoming_dir[0], -incoming_dir[1])  # Inverse of incoming direction
        
        # Calculate reflection using the formula: r = v - 2(v·n)n
        dot_product = incoming_vector[0] * normal[0] + incoming_vector[1] * normal[1]
        reflected = (
            incoming_vector[0] - 2 * dot_product * normal[0],
            incoming_vector[1] - 2 * dot_product * normal[1]
        )
        
        # Apply ricochet angle modification
        return rotate_vector(reflected, self.ricochet_angle)
    
    def update(self, dt, mouse_pos, keys):
        self.follow_mouse(dt, mouse_pos)
        
        # Handle ricochet angle modification
        if keys[pygame.K_q]:  # Counter-clockwise rotation
            self.modify_ricochet_angle(clockwise=False)
        elif keys[pygame.K_e]:  # Clockwise rotation
            self.modify_ricochet_angle(clockwise=True)
    
    def draw(self, surface, player_pos):
        # Draw Shay
        pygame.draw.rect(surface, SHAY_COLOR, self.rect)
        
        # Calculate and draw ricochet indicator
        if player_pos:
            # Direction from player to Shay
            to_shay_dir = (self.pos[0] - player_pos[0], self.pos[1] - player_pos[1])
            to_shay_dir = normalize_vector(to_shay_dir)
            
            # Calculate ricochet direction
            ricochet_dir = self.calculate_ricochet_vector(to_shay_dir, player_pos)
            
            # Draw line from player to Shay
            pygame.draw.line(
                surface,
                LASER_INDICATOR_COLOR,
                player_pos,
                self.pos,
                LASER_INDICATOR_WIDTH
            )
            
            # Draw ricochet line from Shay outward
            end_point = (
                self.pos[0] + ricochet_dir[0] * 200,
                self.pos[1] + ricochet_dir[1] * 200
            )
            pygame.draw.line(
                surface,
                LASER_INDICATOR_COLOR,
                self.pos,
                end_point,
                LASER_INDICATOR_WIDTH
            )
            
        # Debug - show angle value
        if DEBUG_MODE:
            pygame.draw.rect(surface, DEBUG_COLOR, self.rect, 1)
            font = pygame.font.SysFont('Arial', 12)
            angle_text = font.render(f"{self.ricochet_angle:.1f}°", True, DEBUG_COLOR)
            surface.blit(angle_text, (self.pos[0] + 20, self.pos[1] - 20)) 