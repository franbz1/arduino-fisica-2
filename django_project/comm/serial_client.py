"""
Cliente para comunicación serial con Arduino
"""
import time
import serial
from django.conf import settings
from .exceptions import SerialTimeoutError, SerialParseError

class SerialClient:
    """
    Cliente para manejar la comunicación serial con el Arduino
    """
    def __init__(self, port=None, baud=None, timeout=None):
        """
        Inicializa el cliente serial
        
        Args:
            port (str): Puerto serial (ej: 'COM3', '/dev/ttyUSB0')
            baud (int): Velocidad de transmisión
            timeout (float): Timeout en segundos
        """
        self.port = port or settings.SERIAL_PORT
        self.baud = baud or settings.SERIAL_BAUDRATE
        self.timeout = timeout or settings.SERIAL_TIMEOUT
        self.serial = None
        self.is_connected = False
    
    def connect(self):
        """
        Establece la conexión serial
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=self.timeout
            )
            self.is_connected = True
            
            # Esperar a que Arduino reinicie tras la conexión
            time.sleep(2)
            
            # Vaciar buffer
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Test de conexión
            if self.ping():
                return True
            else:
                self.disconnect()
                return False
                
        except (serial.SerialException, OSError) as e:
            self.is_connected = False
            raise e
    
    def disconnect(self):
        """
        Cierra la conexión serial
        """
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.is_connected = False
    
    def ensure_connected(self):
        """
        Asegura que haya una conexión establecida
        """
        if not self.is_connected or not self.serial or not self.serial.is_open:
            self.connect()
    
    def send_command(self, cmd):
        """
        Envía un comando al Arduino
        
        Args:
            cmd (str): Comando a enviar
        """
        self.ensure_connected()
        cmd_bytes = f"{cmd}\n".encode()
        self.serial.write(cmd_bytes)
        self.serial.flush()
    
    def read_response(self):
        """
        Lee la respuesta del Arduino
        
        Returns:
            str: Respuesta recibida
            
        Raises:
            SerialTimeoutError: Si no se recibe respuesta en el tiempo establecido
        """
        self.ensure_connected()
        response = self.serial.readline()
        
        if not response:
            raise SerialTimeoutError("No se recibió respuesta del dispositivo")
            
        return response.decode().strip()
    
    def send_and_read(self, cmd):
        """
        Envía un comando y espera respuesta
        
        Args:
            cmd (str): Comando a enviar
            
        Returns:
            str: Respuesta recibida
        """
        self.send_command(cmd)
        return self.read_response()
    
    def ping(self):
        """
        Envía un ping para verificar la conexión
        
        Returns:
            bool: True si se recibió respuesta correcta (PONG)
        """
        try:
            response = self.send_and_read("PING")
            return response == "PONG"
        except (SerialTimeoutError, serial.SerialException):
            return False
    
    def set_angle(self, angle):
        """
        Comanda al Arduino a ajustar el ángulo del servo
        
        Args:
            angle (float): Ángulo en grados
            
        Returns:
            bool: True si el comando fue exitoso
            
        Raises:
            SerialTimeoutError: Si no se recibe respuesta
            SerialParseError: Si se recibe una respuesta inesperada
        """
        response = self.send_and_read(f"SET_ANGLE:{angle}")
        
        if response == "ANGLE_OK":
            return True
        elif response == "ANGLE_ERR":
            return False
        else:
            raise SerialParseError(f"Respuesta inesperada: {response}")
    
    def load(self):
        """
        Comanda al Arduino a cargar el mecanismo
        
        Returns:
            bool: True si el comando fue exitoso
        """
        response = self.send_and_read("LOAD")
        
        if response == "LOAD_OK":
            return True
        elif response == "LOAD_ERR":
            return False
        else:
            raise SerialParseError(f"Respuesta inesperada: {response}")
    
    def fire(self):
        """
        Comanda al Arduino a disparar
        
        Returns:
            bool: True si el comando fue exitoso
        """
        response = self.send_and_read("FIRE")
        
        if response == "FIRE_OK":
            return True
        elif response == "FIRE_ERR":
            return False
        else:
            raise SerialParseError(f"Respuesta inesperada: {response}")
            
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect() 