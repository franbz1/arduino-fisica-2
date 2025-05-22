"""
Excepciones personalizadas para el módulo de comunicación serial
"""

class SerialError(Exception):
    """Excepción base para errores de comunicación serial"""
    pass

class SerialConnectionError(SerialError):
    """Error al conectar con el dispositivo serial"""
    pass

class SerialTimeoutError(SerialError):
    """Timeout esperando respuesta del dispositivo"""
    pass

class SerialParseError(SerialError):
    """Error al interpretar la respuesta del dispositivo"""
    pass 