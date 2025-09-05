"""
Geographic utility functions
"""
import math
from typing import Tuple, Optional


def is_valid_coordinates(latitude: float, longitude: float) -> bool:
    """
    Check if the given coordinates are valid.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    return (
        -90 <= latitude <= 90 and
        -180 <= longitude <= 180 and
        not (latitude == 0 and longitude == 0)
    )


def calculate_distance(
    lat1: float, lon1: float, 
    lat2: float, lon2: float
) -> float:
    """
    Calculate the distance between two points using the Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers
    earth_radius = 6371
    
    return earth_radius * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the bearing between two points.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Bearing in degrees (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing


def is_point_in_polygon(point: Tuple[float, float], polygon: list) -> bool:
    """
    Check if a point is inside a polygon using the ray casting algorithm.
    
    Args:
        point: Tuple of (latitude, longitude)
        polygon: List of (latitude, longitude) tuples forming the polygon
        
    Returns:
        True if point is inside polygon, False otherwise
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside
