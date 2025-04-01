import pygame
import math
import random
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
        # Reflection effect variables
        self.reflection_angles = []
        self.reflection_lengths = []
    
    def fire(self, player_pos, shay_pos, shay, walls, enemies):
        """Fire a laser from player to shay, then ricochet according to shay's settings"""
        print(f"Laser firing from {player_pos} to {shay_pos}")
        self.active = True
        self.visual_active = True
        self.display_timer = 0
        self.start_pos = player_pos
        self.shay_pos = shay_pos  # Initially set to target, may be nullified if blocked
        self.ricochet_direction = None  # Reset ricochet direction
        
        # Reset reflection effect
        self.reflection_angles = []
        self.reflection_lengths = []
        
        # Check if laser hits Shay (or is blocked by walls or enemies)
        blocked_by_enemy = self._calculate_path_to_shay(walls, enemies)
        if blocked_by_enemy is True:  # Blocked by wall
            # Laser terminates early due to wall
            print("Laser blocked by wall before reaching Shay")
            self.active = False
            return None
        elif blocked_by_enemy is not False:  # Blocked by enemy (enemy object returned)
            # Laser terminates early due to enemy
            print(f"Laser blocked by enemy before reaching Shay")
            self.active = False
            # Check if enemy was hit from vulnerable side
            if blocked_by_enemy[0] is not None:
                print(f"Enemy hit from vulnerable angle before reaching Shay")
                return blocked_by_enemy[0]  # Return the enemy to be destroyed
            return None
        
        # If we reach here, the laser has successfully reached Shay
        # Calculate ricochet direction using Shay's algorithm
        direction_to_shay = (shay_pos[0] - player_pos[0], shay_pos[1] - player_pos[1])
        self.ricochet_direction = shay.calculate_ricochet_vector(direction_to_shay, player_pos)
        print(f"Ricochet direction: {self.ricochet_direction}")
        
        # Generate reflection effect parameters (after ricochet direction is calculated)
        self._generate_reflection_effect(direction_to_shay)
        
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
    
    def _generate_reflection_effect(self, incoming_vector):
        """Generate random reflection lines within a 180-degree arc centered on the reflection angle"""
        if not self.ricochet_direction:
            return
            
        # Calculate the angle of the ricochet direction
        reflection_angle = vector_to_angle(self.ricochet_direction)
        
        # The reflection arc will be 180 degrees centered around the reflection angle
        arc_start = (reflection_angle - 90) % 360  # Start 90 degrees to the left of reflection
        
        # Generate random reflection lines
        self.reflection_angles = []
        self.reflection_lengths = []
        
        for _ in range(REFLECTION_LINE_COUNT):
            # Random angle within the 180 degree arc centered on reflection angle
            angle = (arc_start + random.random() * 180) % 360
            # Random length (within configured range)
            length = SHAY_SIZE * (REFLECTION_MIN_LENGTH + random.random() * 
                                 (REFLECTION_MAX_LENGTH - REFLECTION_MIN_LENGTH))
            
            self.reflection_angles.append(angle)
            self.reflection_lengths.append(length)
    
    def _calculate_path_to_shay(self, walls, enemies=None):
        """Calculate if laser from player to Shay hits any walls or enemies
        
        Returns:
            - True if blocked by a wall
            - False if path is clear
            - (hit_enemy, hit_pos) tuple if blocked by an enemy
        """
        # Calculate direction from player to Shay
        direction_to_shay = (self.shay_pos[0] - self.start_pos[0], self.shay_pos[1] - self.start_pos[1])
        hit_pos, hit_obj = raycast(self.start_pos, direction_to_shay, walls)
        
        # If we hit something that's not near Shay's position, the laser didn't reach Shay
        dist_to_shay = pygame.math.Vector2(self.shay_pos[0] - self.start_pos[0], 
                                           self.shay_pos[1] - self.start_pos[1]).length()
        dist_to_hit = pygame.math.Vector2(hit_pos[0] - self.start_pos[0], 
                                          hit_pos[1] - self.start_pos[1]).length()
        
        # Allow a small margin of error
        if dist_to_hit < dist_to_shay - 5:
            # Hit wall before reaching Shay
            print(f"Laser hit wall at {hit_pos} before reaching Shay")
            self.end_pos = hit_pos
            self.hit_object = hit_obj
            self.shay_pos = None  # Explicitly set to None since laser didn't reach Shay
            return True
        
        # Now check for enemies in the path to Shay (if any)
        if enemies:
            # Create a rect to represent the path of the laser for initial filtering
            line_rect = pygame.Rect(
                min(self.start_pos[0], self.shay_pos[0]),
                min(self.start_pos[1], self.shay_pos[1]),
                abs(self.shay_pos[0] - self.start_pos[0]) or 1,  # Ensure non-zero width
                abs(self.shay_pos[1] - self.start_pos[1]) or 1   # Ensure non-zero height
            )
            
            # Sort enemies by distance from player to check closest ones first
            sorted_enemies = sorted(enemies, key=lambda e: 
                pygame.math.Vector2(e.pos[0] - self.start_pos[0], e.pos[1] - self.start_pos[1]).length_squared())
            
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
                    
                # Calculate more precise collision by checking if the enemy is between player and Shay
                enemy_center = enemy.rect.center
                
                # Calculate vector from player to enemy
                player_to_enemy = (enemy_center[0] - self.start_pos[0], enemy_center[1] - self.start_pos[1])
                
                # Calculate vector from player to Shay
                player_to_shay = (self.shay_pos[0] - self.start_pos[0], self.shay_pos[1] - self.start_pos[1])
                
                # Calculate projection of player_to_enemy onto laser direction
                laser_len_squared = player_to_shay[0]**2 + player_to_shay[1]**2
                if laser_len_squared < 0.0001:  # Avoid division by zero
                    continue
                    
                projection = (player_to_enemy[0] * player_to_shay[0] + player_to_enemy[1] * player_to_shay[1]) / laser_len_squared
                
                # Enemy is not between player and Shay
                if projection <= 0 or projection >= 1:
                    continue
                    
                # Calculate closest point on laser to enemy
                closest_point = (
                    self.start_pos[0] + projection * player_to_shay[0],
                    self.start_pos[1] + projection * player_to_shay[1]
                )
                
                # Distance from closest point to enemy center
                dist_to_enemy = pygame.math.Vector2(closest_point[0] - enemy_center[0], 
                                                   closest_point[1] - enemy_center[1]).length()
                
                # Check if closest point is close enough to enemy (half the size plus a small buffer)
                collision_threshold = ENEMY_SIZE / 2 + 2  # Half enemy size plus small buffer
                if dist_to_enemy <= collision_threshold:
                    # Calculate distance from player to this hit point
                    dist_from_player = pygame.math.Vector2(closest_point[0] - self.start_pos[0], 
                                                       closest_point[1] - self.start_pos[1]).length()
                    
                    # Only consider this hit if it's closer than any previous hit
                    if dist_from_player < closest_distance:
                        closest_distance = dist_from_player
                        closest_hit_pos = closest_point
                        
                        # Check if hit is from enemy's vulnerable direction
                        # Calculate the direction from the hit point to the enemy
                        hit_to_enemy = normalize_vector((enemy_center[0] - closest_point[0], 
                                                      enemy_center[1] - closest_point[1]))
                        incoming_angle = vector_to_angle(hit_to_enemy)
                        
                        print(f"Initial laser hit enemy - incoming angle: {incoming_angle}, vulnerable angle: {enemy.vulnerable_angle}")
                        
                        if is_angle_in_arc(incoming_angle, enemy.vulnerable_angle, VULNERABLE_ARC_SIZE):
                            # Enemy is hit from vulnerable direction
                            print("Enemy hit from vulnerable angle on initial path!")
                            closest_hit_enemy = enemy
                        else:
                            # Enemy blocks laser but is not destroyed
                            print("Enemy hit but not from vulnerable angle on initial path, laser blocked")
                            closest_hit_enemy = None
            
            # If we found an enemy in the path, return it and the hit position
            if closest_hit_pos is not None:
                self.end_pos = closest_hit_pos
                self.shay_pos = None  # Explicitly set to None since laser didn't reach Shay
                return (closest_hit_enemy, closest_hit_pos)
        
        return False
    
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
        if not self.visual_active or not self.start_pos:
            return
        
        # Calculate pulse effect based on timer
        time_factor = self.display_timer / self.display_duration
        pulse_width = int(LASER_WIDTH * (2.0 - time_factor))  # Width decreases over time
        pulse_width = max(1, pulse_width)  # Ensure minimum width of 1
        
        # Create a brighter laser color for better visibility
        bright_factor = 1.0 - time_factor * 0.7
        laser_color = (255, 50 + int(100 * bright_factor), 50 + int(100 * bright_factor))
        
        # Enhanced impact effect using settings constants with safety checks
        base_impact_radius = IMPACT_BASE_RADIUS + int(IMPACT_PULSE_RANGE * math.sin(self.display_timer * IMPACT_PULSE_SPEED))
        base_impact_radius = max(1, base_impact_radius)  # Ensure minimum radius of 1
        impact_glow_radius = int(base_impact_radius * IMPACT_GLOW_MULTIPLIER)
        impact_glow_radius = max(2, impact_glow_radius)  # Ensure minimum glow radius of 2
        
        # Create the glow surface that will be reused
        glow_color = (laser_color[0], laser_color[1], laser_color[2], IMPACT_GLOW_ALPHA)
        glow_surface_size = max(4, impact_glow_radius * 2)  # Minimum size of 4 pixels
        glow_surface = pygame.Surface((glow_surface_size, glow_surface_size), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surface,
            glow_color,
            (glow_surface_size // 2, glow_surface_size // 2),  # Center of the surface
            impact_glow_radius
        )
        
        # Case 1: Laser blocked before reaching Shay (hits wall or enemy)
        if not self.shay_pos:
            # Draw only from player to endpoint
            if self.end_pos:
                pygame.draw.line(
                    surface,
                    laser_color,
                    self.start_pos,
                    self.end_pos,
                    pulse_width
                )
                
                # Draw enhanced impact at end point where laser was blocked
                surface.blit(
                    glow_surface, 
                    (int(self.end_pos[0] - glow_surface_size // 2), int(self.end_pos[1] - glow_surface_size // 2))
                )
                
                # Then draw the main impact circle
                pygame.draw.circle(
                    surface, 
                    laser_color, 
                    (int(self.end_pos[0]), int(self.end_pos[1])), 
                    base_impact_radius
                )
            return
        
        # Cases 2, 3, 4: Laser reaches Shay
        # Draw line from player to Shay
        pygame.draw.line(
            surface,
            laser_color,
            self.start_pos,
            self.shay_pos,
            pulse_width
        )
        
        # Draw the reflection effect (3 lines in a 180 degree arc)
        if self.reflection_angles and self.ricochet_direction:
            thin_width = max(1, pulse_width // REFLECTION_LINE_WIDTH_DIVISOR)  # Thinner than the main laser
            reflection_color = laser_color
            
            for i in range(len(self.reflection_angles)):
                angle_rad = math.radians(self.reflection_angles[i])
                end_x = self.shay_pos[0] + math.cos(angle_rad) * self.reflection_lengths[i]
                end_y = self.shay_pos[1] + math.sin(angle_rad) * self.reflection_lengths[i]
                
                pygame.draw.line(
                    surface,
                    reflection_color,
                    self.shay_pos,
                    (end_x, end_y),
                    thin_width
                )
        
        # Draw reflection line if applicable (cases 2, 3, 4)
        if self.end_pos and self.ricochet_direction:
            # Draw ricochet line from Shay to end point
            pygame.draw.line(
                surface,
                laser_color,
                self.shay_pos,
                self.end_pos,
                pulse_width
            )
            
            # Draw enhanced impact at end point of reflection
            # First draw outer glow
            surface.blit(
                glow_surface, 
                (int(self.end_pos[0] - glow_surface_size // 2), int(self.end_pos[1] - glow_surface_size // 2))
            )
            
            # Then draw main impact
            pygame.draw.circle(
                surface, 
                laser_color, 
                (int(self.end_pos[0]), int(self.end_pos[1])), 
                base_impact_radius
            )
    
    def update(self, dt):
        """Update laser visual effect timer"""
        if self.visual_active:
            self.display_timer += dt
            if self.display_timer >= self.display_duration:
                self.visual_active = False
                print("Laser visual effect ended") 