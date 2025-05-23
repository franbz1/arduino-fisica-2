"""
Context processors para el módulo de comunicación
"""
from .connection_manager import connection_manager


def connection_status(request):
    """
    Context processor que añade el estado de conexión a todas las plantillas
    """
    status = connection_manager.get_status()
    return {
        'connection_status': status,
        'is_serial_connected': status['is_connected']
    } 