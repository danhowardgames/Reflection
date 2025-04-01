import pygame
import math
from settings import *

def distance(p1, p2):
    """Calculate the distance between two points"""
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

def normalize_vector(vector):
    """Normalize a vector to unit length"""
    magnitude = math.sqrt(vector[0]**2 + vector[1]**2)
    if magnitude == 0:
        return (0, 0)
    return (vector[0] / magnitude, vector[1] / magnitude)

def vector_from_angle(angle_deg):
    """Convert angle in degrees to a unit vector"""
    angle_rad = math.radians(angle_deg)
    return (math.cos(angle_rad), math.sin(angle_rad))

def angle_between_vectors(v1, v2):
    """Calculate angle between two vectors in degrees"""
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
    
    # Avoid division by zero
    if mag1 == 0 or mag2 == 0:
        return 0
        
    cos_angle = dot / (mag1 * mag2)
    # Ensure the value is in valid range for arccos
    cos_angle = max(-1, min(1, cos_angle))
    angle_rad = math.acos(cos_angle)
    return math.degrees(angle_rad)

def rotate_vector(vector, angle_deg):
    """Rotate a vector by angle_deg degrees"""
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    return (
        vector[0] * cos_a - vector[1] * sin_a,
        vector[0] * sin_a + vector[1] * cos_a
    )

def vector_to_angle(vector):
    """Convert a vector to an angle in degrees (0-360)"""
    angle_rad = math.atan2(vector[1], vector[0])
    angle_deg = math.degrees(angle_rad)
    return angle_deg % 360

def is_angle_in_arc(angle, arc_center, arc_size):
    """Check if an angle is within an arc centered at arc_center with size arc_size"""
    half_arc = arc_size / 2
    lower_bound = (arc_center - half_arc) % 360
    upper_bound = (arc_center + half_arc) % 360
    
    # Handle arc crossing the 0/360 boundary
    if lower_bound > upper_bound:
        return angle >= lower_bound or angle <= upper_bound
    else:
        return angle >= lower_bound and angle <= upper_bound

def raycast(start_pos, direction, walls, max_distance=2000):
    """Cast a ray and return the collision point and what was hit"""
    # Normalize direction
    direction = normalize_vector(direction)
    
    # Calculate end point based on direction and max_distance
    end_pos = (
        start_pos[0] + direction[0] * max_distance,
        start_pos[1] + direction[1] * max_distance
    )
    
    # Create a Line for collision detection
    line = pygame.Rect(
        min(start_pos[0], end_pos[0]),
        min(start_pos[1], end_pos[1]),
        abs(end_pos[0] - start_pos[0]) or 1,  # Ensure non-zero width
        abs(end_pos[1] - start_pos[1]) or 1   # Ensure non-zero height
    )
    
    # Check collision with walls
    closest_point = end_pos
    closest_distance = max_distance
    collision_object = None
    
    for wall in walls:
        # Use clipping to find intersection point
        if line.colliderect(wall):
            # Calculate intersection - simplified approximation
            # This is a simplification and may need improvement for exact intersection
            if direction[0] != 0:
                # Check horizontal intersections
                if direction[0] > 0:  # Moving right
                    x_intersect = wall.left
                    t = (x_intersect - start_pos[0]) / direction[0]
                else:  # Moving left
                    x_intersect = wall.right
                    t = (x_intersect - start_pos[0]) / direction[0]
                
                if 0 <= t <= max_distance:
                    y_intersect = start_pos[1] + t * direction[1]
                    if wall.top <= y_intersect <= wall.bottom:
                        intersection = (x_intersect, y_intersect)
                        dist = distance(start_pos, intersection)
                        if dist < closest_distance:
                            closest_distance = dist
                            closest_point = intersection
                            collision_object = wall
            
            if direction[1] != 0:
                # Check vertical intersections
                if direction[1] > 0:  # Moving down
                    y_intersect = wall.top
                    t = (y_intersect - start_pos[1]) / direction[1]
                else:  # Moving up
                    y_intersect = wall.bottom
                    t = (y_intersect - start_pos[1]) / direction[1]
                
                if 0 <= t <= max_distance:
                    x_intersect = start_pos[0] + t * direction[0]
                    if wall.left <= x_intersect <= wall.right:
                        intersection = (x_intersect, y_intersect)
                        dist = distance(start_pos, intersection)
                        if dist < closest_distance:
                            closest_distance = dist
                            closest_point = intersection
                            collision_object = wall
    
    return closest_point, collision_object

def reflect_vector(vector, normal):
    """Reflect a vector against a normal vector"""
    # Ensure normal is normalized
    normal = normalize_vector(normal)
    
    # Calculate reflection using the formula: r = v - 2(v·n)n
    dot_product = vector[0] * normal[0] + vector[1] * normal[1]
    return (
        vector[0] - 2 * dot_product * normal[0],
        vector[1] - 2 * dot_product * normal[1]
    )

def draw_text(surface, text, font, color, x, y, align="topleft"):
    """Draw text with specified alignment"""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    
    if align == "topleft":
        text_rect.topleft = (x, y)
    elif align == "center":
        text_rect.center = (x, y)
    elif align == "topright":
        text_rect.topright = (x, y)
    elif align == "bottomleft":
        text_rect.bottomleft = (x, y)
    elif align == "bottomright":
        text_rect.bottomright = (x, y)
    
    surface.blit(text_surface, text_rect) 