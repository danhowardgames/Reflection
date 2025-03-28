import pygame
import math
from settings import *
from utils import normalize_vector, raycast, vector_to_angle, is_angle_in_arc

class Laser:
    def __init__(self):
        self.active = False
        self.start_pos = None
        self.shay_pos = None
        self.ricochet_pos = None
        self.end_pos = None
        self.hit_object = None
        self.ricochet_direction = None
        self.display_duration = LASER_DISPLAY_DURATION
        self.display_timer = 0
        self.visual_active = False
    
    def fire(self, player_pos, shay_pos, shay, walls, enemies):
        """Fire a laser from player to shay, then ricochet according to shay's settings"""
        print(f"Laser firing from {player_pos} to {shay_pos}")
        self.active = True
        self.visual_active = True
        self.display_timer = 0
        self.start_pos = player_pos
        self.shay_pos = shay_pos
        
        # Check if laser hits Shay
        if not self._calculate_path_to_shay(walls):
            # Didn't hit Shay, laser terminates early
            print("Laser blocked before reaching Shay")
            self.active = False
            return None
        
        # Calculate ricochet direction using Shay's algorithm
        direction_to_shay = (shay_pos[0] - player_pos[0], shay_pos[1] - player_pos[1])
        self.ricochet_direction = shay.calculate_ricochet_vector(direction_to_shay, player_pos)
        print(f"Ricochet direction: {self.ricochet_direction}")
        
        # Cast ray from Shay in the ricochet direction
        hit_pos, hit_obj = raycast(self.shay_pos, self.ricochet_direction, walls)
        self.end_pos = hit_pos
        self.hit_object = hit_obj
        print(f"Ricochet end point: {self.end_pos}")
        
        # Check if any enemies were hit by the ricochet and update laser endpoint
        hit_enemy, blocked_at = self._check_enemy_hits(enemies)
        if blocked_at:
            # Update the laser endpoint if it was blocked by an enemy
            self.end_pos = blocked_at
            
        if hit_enemy:
            print(f"Hit enemy with laser at {hit_enemy.pos}")
        
        return hit_enemy
    
    def _calculate_path_to_shay(self, walls):
        """Calculate if laser from player to Shay hits any walls"""
        direction_to_shay = (self.shay_pos[0] - self.start_pos[0], self.shay_pos[1] - self.start_pos[1])
        hit_pos, hit_obj = raycast(self.start_pos, direction_to_shay, walls)
        
        # If we hit something that's not near Shay's position, the laser didn't reach Shay
        dist_to_shay = pygame.math.Vector2(self.shay_pos[0] - self.start_pos[0], 
                                           self.shay_pos[1] - self.start_pos[1]).length()
        dist_to_hit = pygame.math.Vector2(hit_pos[0] - self.start_pos[0], 
                                          hit_pos[1] - self.start_pos[1]).length()
        
        # Allow a small margin of error
        if dist_to_hit < dist_to_shay - 5:
            # Hit something before reaching Shay
            print(f"Laser hit wall at {hit_pos} before reaching Shay")
            self.end_pos = hit_pos
            self.hit_object = hit_obj
            return False
        
        return True
    
    def _check_enemy_hits(self, enemies):
        """Check if the ricochet laser hits any enemies from their vulnerable direction
        
        Returns:
            tuple: (hit_enemy, blocked_position) - The enemy hit from vulnerable side (or None), 
                   and the position where the laser was blocked (or None)
        """
        if not self.active or not self.ricochet_direction:
            return None, None
        
        # Create a rect to represent the path of the laser for initial filtering
        line_rect = pygame.Rect(
            min(self.shay_pos[0], self.end_pos[0]),
            min(self.shay_pos[1], self.end_pos[1]),
            abs(self.end_pos[0] - self.shay_pos[0]) or 1,  # Ensure non-zero width
            abs(self.end_pos[1] - self.shay_pos[1]) or 1   # Ensure non-zero height
        )
        
        # Sort enemies by distance from Shay to check closest ones first
        sorted_enemies = sorted(enemies, key=lambda e: 
            pygame.math.Vector2(e.pos[0] - self.shay_pos[0], e.pos[1] - self.shay_pos[1]).length_squared())
        
        closest_hit_enemy = None
        closest_hit_pos = None
        closest_distance = float('inf')
        
        for enemy in sorted_enemies:
            # Skip enemies that are definitely not in the laser path
            if not line_rect.colliderect(enemy.rect):
                continue
                
            # Skip enemies in dying state
            if enemy.state == enemy.STATE_DYING:
                continue
                
            # Calculate more precise collision by checking if the enemy is between shay and end position
            enemy_center = enemy.rect.center
            
            # Calculate vector from Shay to enemy
            shay_to_enemy = (enemy_center[0] - self.shay_pos[0], enemy_center[1] - self.shay_pos[1])
            
            # Calculate vector from Shay to end position
            shay_to_end = (self.end_pos[0] - self.shay_pos[0], self.end_pos[1] - self.shay_pos[1])
            
            # Calculate projection of shay_to_enemy onto laser direction
            laser_len_squared = shay_to_end[0]**2 + shay_to_end[1]**2
            if laser_len_squared < 0.0001:  # Avoid division by zero
                continue
                
            projection = (shay_to_enemy[0] * shay_to_end[0] + shay_to_enemy[1] * shay_to_end[1]) / laser_len_squared
            
            # Enemy is not between Shay and end position
            if projection <= 0 or projection >= 1:
                continue
                
            # Calculate closest point on laser to enemy
            closest_point = (
                self.shay_pos[0] + projection * shay_to_end[0],
                self.shay_pos[1] + projection * shay_to_end[1]
            )
            
            # Distance from closest point to enemy center
            dist_to_enemy = pygame.math.Vector2(closest_point[0] - enemy_center[0], 
                                               closest_point[1] - enemy_center[1]).length()
            
            # Check if closest point is close enough to enemy (half the size plus a small buffer)
            collision_threshold = ENEMY_SIZE / 2 + 2  # Half enemy size plus small buffer
            if dist_to_enemy <= collision_threshold:
                # Calculate distance from Shay to this hit point
                dist_from_shay = pygame.math.Vector2(closest_point[0] - self.shay_pos[0], 
                                                   closest_point[1] - self.shay_pos[1]).length()
                
                # Only consider this hit if it's closer than any previous hit
                if dist_from_shay < closest_distance:
                    closest_distance = dist_from_shay
                    closest_hit_pos = closest_point
                    
                    # Check if hit is from enemy's vulnerable direction
                    incoming_angle = vector_to_angle(
                        (-self.ricochet_direction[0], -self.ricochet_direction[1])
                    )
                    
                    print(f"Laser hit enemy - incoming angle: {incoming_angle}, vulnerable angle: {enemy.vulnerable_angle}")
                    
                    if is_angle_in_arc(incoming_angle, enemy.vulnerable_angle, VULNERABLE_ARC_SIZE):
                        # Enemy is hit from vulnerable direction
                        print("Enemy hit from vulnerable angle!")
                        closest_hit_enemy = enemy
                    else:
                        # Enemy blocks laser but is not destroyed
                        print("Enemy hit but not from vulnerable angle, laser blocked")
                        closest_hit_enemy = None
        
        # Return the closest enemy hit (if any)
        return closest_hit_enemy, closest_hit_pos
    
    def deactivate(self):
        """Turn off the laser game logic (but keep visual effect until timer expires)"""
        self.active = False
    
    def draw(self, surface):
        """Draw the laser beam"""
        if not self.visual_active or not self.start_pos or not self.shay_pos:
            return
        
        # Calculate pulse effect based on timer
        time_factor = self.display_timer / self.display_duration
        pulse_width = int(LASER_WIDTH * (2.0 - time_factor))  # Width decreases over time
        
        # Create a brighter laser color for better visibility
        bright_factor = 1.0 - time_factor * 0.7
        laser_color = (255, 50 + int(100 * bright_factor), 50 + int(100 * bright_factor))
        
        # Draw line from player to Shay
        pygame.draw.line(
            surface,
            laser_color,
            self.start_pos,
            self.shay_pos,
            pulse_width
        )
        
        # Draw ricochet line from Shay to end point
        if self.end_pos:
            pygame.draw.line(
                surface,
                laser_color,
                self.shay_pos,
                self.end_pos,
                pulse_width
            )
            
        # Draw impact points with pulsing effect
        impact_radius = 5 + int(3 * math.sin(self.display_timer * 20))
        if self.shay_pos:
            pygame.draw.circle(surface, laser_color, (int(self.shay_pos[0]), int(self.shay_pos[1])), impact_radius)
        if self.end_pos:
            pygame.draw.circle(surface, laser_color, (int(self.end_pos[0]), int(self.end_pos[1])), impact_radius)
    
    def update(self, dt):
        """Update laser visual effect timer"""
        if self.visual_active:
            self.display_timer += dt
            if self.display_timer >= self.display_duration:
                self.visual_active = False
                print("Laser visual effect ended") 