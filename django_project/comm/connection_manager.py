"""
Manager centralizado para la conexión serial con Arduino
"""
import threading
import time
from .serial_client import SerialClient
from .exceptions import SerialConnectionError, SerialTimeoutError
from django.conf import settings


class ConnectionManager:
    """
    Singleton para gestionar la conexión serial de forma centralizada
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.client = None
            self.is_connected = False
            self.last_error = None
            self.last_test_time = None
            self.last_test_result = None
            self._initialized = True
    
    def connect(self):
        """
        Establece conexión con Arduino
        
        Returns:
            dict: {'success': bool, 'message': str, 'error': str}
        """
        result = {'success': False, 'message': '', 'error': None}
        
        try:
            # Cerrar conexión existente si la hay
            if self.client:
                self.disconnect()
            
            # Crear nuevo cliente
            self.client = SerialClient()
            
            # Intentar conectar
            if self.client.connect():
                self.is_connected = True
                self.last_error = None
                result['success'] = True
                result['message'] = f'Conexión establecida en puerto {settings.SERIAL_PORT}'
            else:
                self.is_connected = False
                result['error'] = 'No se pudo establecer conexión con Arduino'
                
        except SerialConnectionError as e:
            self.is_connected = False
            self.last_error = str(e)
            result['error'] = f'Error de conexión: {str(e)}'
            
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            result['error'] = f'Error inesperado: {str(e)}'
            
        finally:
            # Si hubo error, asegurar que la conexión esté limpia
            if not result['success'] and self.client:
                try:
                    self.client.disconnect()
                except:
                    pass
                self.client = None
                
        return result
    
    def disconnect(self):
        """
        Cierra la conexión con Arduino
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        result = {'success': True, 'message': 'Conexión cerrada'}
        
        try:
            if self.client:
                self.client.disconnect()
        except Exception as e:
            result['message'] = f'Error al cerrar: {str(e)}'
        finally:
            self.client = None
            self.is_connected = False
            self.last_error = None
            
        return result
    
    def test_connection(self):
        """
        Prueba la conexión actual enviando un PING
        
        Returns:
            dict: {'success': bool, 'message': str, 'response_time': float, 'error': str}
        """
        result = {'success': False, 'message': '', 'response_time': None, 'error': None}
        
        if not self.is_connected or not self.client:
            result['error'] = 'No hay conexión establecida'
            self.last_test_result = result
            self.last_test_time = time.time()
            return result
        
        try:
            start_time = time.time()
            
            # Enviar ping y medir tiempo de respuesta
            if self.client.ping():
                response_time = time.time() - start_time
                result['success'] = True
                result['message'] = 'Arduino respondió correctamente'
                result['response_time'] = round(response_time * 1000, 2)  # en ms
            else:
                result['error'] = 'Arduino no respondió al PING'
                
        except SerialTimeoutError as e:
            result['error'] = f'Timeout: {str(e)}'
            
        except SerialConnectionError as e:
            result['error'] = f'Error de conexión: {str(e)}'
            # Marcar como desconectado
            self.is_connected = False
            
        except Exception as e:
            result['error'] = f'Error inesperado: {str(e)}'
            
        finally:
            self.last_test_result = result
            self.last_test_time = time.time()
            
        return result
    
    def get_client(self):
        """
        Obtiene el cliente serial para uso en otras partes del código
        
        Returns:
            SerialClient or None: Cliente serial si está conectado
            
        Raises:
            SerialConnectionError: Si no hay conexión establecida
        """
        if not self.is_connected or not self.client:
            raise SerialConnectionError("No hay conexión establecida. Conecta primero desde el panel de control.")
        
        return self.client
    
    def get_status(self):
        """
        Obtiene el estado actual de la conexión
        
        Returns:
            dict: Estado completo de la conexión
        """
        return {
            'is_connected': self.is_connected,
            'port': settings.SERIAL_PORT,
            'baudrate': settings.SERIAL_BAUDRATE,
            'last_error': self.last_error,
            'last_test_time': self.last_test_time,
            'last_test_result': self.last_test_result,
            'client_exists': self.client is not None
        }


# Instancia global del manager
connection_manager = ConnectionManager() 