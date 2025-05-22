from typing import Optional, Dict
import math
import numpy as np
from django.conf import settings


def solve_for(distance: float) -> Optional[Dict[str, float]]:
    """
    Calcula el ángulo, velocidad y configuración de bandas para alcanzar una
    distancia específica.
    
    Args:
        distance: Distancia objetivo en metros
    
    Returns:
        Optional[dict]: Diccionario con los valores calculados o None si no hay solución:
            - angle: Ángulo en grados
            - velocity: Velocidad inicial en m/s
            - n_bands: Número de bandas elásticas necesarias
            - notch_index: Índice de la muesca a utilizar
            - notch_position: Deformación en metros de la muesca seleccionada
    """
    # Parámetros físicos
    g = settings.GRAVITY
    angle_min = settings.ANGLE_MIN
    angle_max = settings.ANGLE_MAX
    angle_step = getattr(settings, 'ANGLE_STEP', 0.5)
    max_velocity = getattr(settings, 'MAX_VELOCITY', 10.0)
    h0 = settings.INITIAL_HEIGHT  # Altura inicial
    
    best_alpha = None
    best_v = None
    min_v = float('inf')  # Velocidad mínima encontrada
    
    # Búsqueda del ángulo óptimo
    for alpha_deg in np.arange(angle_min, angle_max + angle_step/2, angle_step):
        alpha_rad = math.radians(alpha_deg)
        sin2a = math.sin(2 * alpha_rad)
        if abs(sin2a) < 1e-6:
            continue

        # Terminos de la ecuación para despejar v
        term1 = distance / sin2a
        term2 = math.cos(alpha_rad) * math.sqrt(2 * h0 / g)
        # v^2 + g*term2*v - g*term1 = 0
        a = 1
        b = g * term2
        c = -g * term1
        discriminant = b**2 - 4*a*c
        if discriminant < 0:
            continue

        v1 = (-b + math.sqrt(discriminant)) / (2 * a)
        v2 = (-b - math.sqrt(discriminant)) / (2 * a)
        # Seleccionamos la solución positiva
        candidates = [v for v in (v1, v2) if v > 0]
        if not candidates:
            continue
        v = min(candidates)

        # Filtrar velocidades razonables
        if v < max_velocity and v < min_v:
            min_v = v
            best_v = v
            best_alpha = alpha_deg

    if best_alpha is None:
        return None

    # Cálculo de bandas
    mass = settings.PROJECTILE_MASS / 1000  # convertir g a kg
    energy_needed = 0.5 * mass * (best_v ** 2)

    n_bands = float('inf')
    notch_index = -1
    notch_position = None

    for i, notch in enumerate(settings.NOTCH_POSITIONS):
        # Ignorar muescas sin deformación
        if notch <= 0:
            continue
        # Energía por banda
        energy_per_band = 0.5 * settings.K_ELASTIC * (notch ** 2)
        bands = math.ceil(energy_needed / energy_per_band)
        if bands < n_bands:
            n_bands = bands
            notch_index = i
            notch_position = notch

    return {
        'angle': float(round(best_alpha, 1)),
        'velocity': float(round(best_v, 2)),
        'n_bands': int(n_bands),
        'notch_index': int(notch_index),
        'notch_position': float(round(notch_position, 3))
    }
