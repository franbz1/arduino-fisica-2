"""
Módulo para cálculos físicos de trayectoria parabólica
"""
import math
from django.conf import settings
import numpy as np

def solve_for(distance: float) -> dict:
    """
    Calcula el ángulo, velocidad y configuración de bandas para alcanzar una
    distancia específica.
    
    Args:
        distance: Distancia objetivo en metros
    
    Returns:
        dict: Diccionario con los valores calculados:
            - angle: Ángulo en grados
            - velocity: Velocidad inicial en m/s
            - n_bands: Número de bandas elásticas necesarias
            - notch: Índice de la muesca a utilizar
    """
    g = settings.GRAVITY
    angle_min = settings.ANGLE_MIN
    angle_max = settings.ANGLE_MAX
    h0 = settings.INITIAL_HEIGHT  # Altura inicial
    
    best_alpha = None
    best_v = None
    min_v = float('inf')  # Buscamos la velocidad mínima viable
    
    # Búsqueda del ángulo óptimo con paso de 0.5 grados
    for alpha_deg in np.arange(angle_min, angle_max + 0.1, 0.5):
        alpha_rad = math.radians(alpha_deg)
        
        # Resolver ecuación cuadrática para v considerando altura inicial:
        # x = (v²/g) * sin(2α) + v * cos(α) * √(2h₀/g)
        
        # Primero verificamos si el ángulo es viable (para evitar divisiones por cero)
        if abs(math.sin(2 * alpha_rad)) < 1e-6:
            continue
            
        # Calculamos velocidad para este ángulo
        term1 = distance / math.sin(2 * alpha_rad)
        term2 = math.cos(alpha_rad) * math.sqrt(2 * h0 / g)
        
        # La ecuación es: v²/g = term1 - v * term2
        # Reorganizamos como: v² + g*term2*v - g*term1 = 0
        # Resolvemos con fórmula cuadrática
        a = 1
        b = g * term2
        c = -g * term1
        
        # Calculamos el discriminante
        discriminant = b**2 - 4*a*c
        
        if discriminant < 0:
            continue  # No hay solución real
            
        # Tomamos la solución positiva menor
        v1 = (-b + math.sqrt(discriminant)) / (2*a)
        v2 = (-b - math.sqrt(discriminant)) / (2*a)
        
        v = max(0, min(v1, v2) if min(v1, v2) > 0 else max(v1, v2))
        
        # Verificamos que sea una velocidad razonable (menor a 10 m/s)
        if 0 < v < 10 and v < min_v:
            min_v = v
            best_v = v
            best_alpha = alpha_deg
    
    # Si no encontramos solución, retornamos None
    if best_alpha is None:
        return None
    
    # Calcular número de bandas y muesca
    notch_index = 0
    n_bands = float('inf')
    
    # Estimado de masa del proyectil (g)
    mass = 20.0 / 1000  # 20g convertido a kg
    
    # Calculamos energía cinética necesaria
    energy = 0.5 * mass * (best_v ** 2)
    
    # Encontramos la mejor combinación de muesca y bandas
    for i, notch in enumerate(settings.NOTCH_POSITIONS):
        # Energía almacenada por banda en esta posición
        energy_per_band = 0.5 * settings.K_ELASTIC * (notch ** 2)
        
        # Número de bandas necesarias
        bands = math.ceil(energy / energy_per_band)
        
        if bands < n_bands:
            n_bands = bands
            notch_index = i
    
    return {
        'angle': round(best_alpha, 1),
        'velocity': round(best_v, 2),
        'n_bands': n_bands,
        'notch': notch_index
    } 