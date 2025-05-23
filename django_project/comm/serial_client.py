"""
Cliente para comunicación serial con Arduino
"""
import time
import serial
from django.conf import settings
from .exceptions import SerialTimeoutError, SerialParseError, SerialConnectionError

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
            # Verificar si ya hay una conexión abierta y cerrarla
            if hasattr(self, 'serial') and self.serial and self.serial.is_open:
                self.serial.close()
                time.sleep(0.5)  # Dar tiempo para que se cierre completamente
            
            # Intentar abrir la conexión
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # Marcar como conectado
            self.is_connected = True
            
            # Esperar a que Arduino reinicie tras la conexión
            time.sleep(2)
            
            # Vaciar buffer
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Intentar un ping sin usar la verificación automática
            # esto evita recursión infinita
            self.send_command("PING")
            response = self.read_response()
            
            if response == "PONG":
                return True
            else:
                print(f"Respuesta inesperada al ping: '{response}'")
                self.disconnect()
                return False
                
        except serial.SerialException as e:
            self.is_connected = False
            print(f"Error de conexión serial: {str(e)}")
            # Asegurarse de que el serial esté cerrado si hubo error
            if hasattr(self, 'serial') and self.serial:
                try:
                    self.serial.close()
                except:
                    pass
            raise e
        except Exception as e:
            self.is_connected = False
            print(f"Error inesperado: {str(e)}")
            if hasattr(self, 'serial') and self.serial:
                try:
                    self.serial.close()
                except:
                    pass
            raise e
        finally:
            # Asegurar limpieza si hay error
            if not self.is_connected and hasattr(self, 'serial') and self.serial:
                try:
                    self.serial.close()
                except:
                    pass
                self.serial = None
    
    def disconnect(self):
        """
        Cierra la conexión serial
        """
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
        except Exception as e:
            print(f"Error al cerrar puerto serial: {str(e)}")
        finally:
            self.is_connected = False
            self.serial = None
    
    def ensure_connected(self):
        """
        Asegura que haya una conexión establecida
        
        Raises:
            SerialConnectionError: Si no se puede establecer conexión
        """
        # Verificar si la conexión está activa y operativa
        if self.is_connected and self.serial and self.serial.is_open:
            try:
                # Prueba simple para verificar que el puerto esté operativo
                self.serial.in_waiting
                return
            except Exception as e:
                print(f"Conexión existente no válida: {str(e)}")
                self.is_connected = False
                try:
                    self.serial.close()
                except:
                    pass
        
        # Intentar conectar si llegamos aquí
        try:
            self.connect()
        except Exception as e:
            raise SerialConnectionError(f"No se pudo establecer conexión: {str(e)}")
    
    def send_command(self, cmd):
        """
        Envía un comando al Arduino
        
        Args:
            cmd (str): Comando a enviar
        """
        self.ensure_connected()
        cmd_bytes = f"{cmd}\n".encode()
        try:
            self.serial.write(cmd_bytes)
            self.serial.flush()
        except Exception as e:
            self.is_connected = False
            print(f"Error al enviar comando: {str(e)}")
            raise e
    
    def read_response(self):
        """
        Lee la respuesta del Arduino
        
        Returns:
            str: Respuesta recibida
            
        Raises:
            SerialTimeoutError: Si no se recibe respuesta en el tiempo establecido
            SerialConnectionError: Si hay un error de conexión
        """
        self.ensure_connected()
        
        try:
            # Leer respuesta del buffer con timeout adecuado
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.serial.in_waiting > 0:
                    response = self.serial.readline()
        
                    if response:
                        # Decodificar respuesta y eliminar espacios y caracteres de control
                        decoded = response.decode().strip()
                        
                        # Log para debug
                        print(f"Respuesta cruda recibida: {repr(response)}")
                        print(f"Respuesta decodificada: '{decoded}'")
                        
                        return decoded
                
                # Pequeña pausa para no saturar la CPU
                time.sleep(0.01)
                
            # Si llegamos aquí, es timeout
            raise SerialTimeoutError("No se recibió respuesta del dispositivo en el tiempo esperado")
            
        except serial.SerialException as e:
            self.is_connected = False
            print(f"Error de conexión al leer respuesta: {str(e)}")
            raise SerialConnectionError(f"Error de conexión: {str(e)}")
    
    def send_and_read(self, cmd):
        """
        Envía un comando y espera respuesta
        
        Args:
            cmd (str): Comando a enviar
            
        Returns:
            str: Respuesta recibida
        """
        max_retries = 2
        last_exception = None
        
        for retry in range(max_retries):
            try:
                self.send_command(cmd)
                return self.read_response()
            except (SerialTimeoutError, SerialConnectionError) as e:
                last_exception = e
                print(f"Error en intento {retry+1}/{max_retries}: {str(e)}")
                # Intentar reconectar antes del próximo intento
                try:
                    self.disconnect()
                    time.sleep(1)  # Pausa antes de reintentar
                except:
                    pass
        
        # Si llegamos aquí, fallaron todos los intentos
        if isinstance(last_exception, SerialTimeoutError):
            raise SerialTimeoutError(f"Después de {max_retries} intentos: {str(last_exception)}")
        else:
            raise SerialConnectionError(f"Después de {max_retries} intentos: {str(last_exception)}")
    
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
            dict: Diccionario con los resultados:
                - success (bool): True si fue exitoso
                - current_angle (float): Ángulo actual según el MPU
                - error (str): Mensaje de error (si hay)
            
        Raises:
            SerialTimeoutError: Si no se recibe respuesta
            SerialParseError: Si se recibe una respuesta inesperada
        """
        response = self.send_and_read(f"SET_ANGLE:{angle}")
        result = {'success': False, 'current_angle': None, 'error': None}
        
        # Respuesta esperada: "ANGLE_OK:XX.X" o "ANGLE_ERR:REASON_XX.X"
        if response.startswith("ANGLE_OK:"):
            # Extraer ángulo actual del MPU
            try:
                current_angle = float(response.split(':')[1])
                result['success'] = True
                result['current_angle'] = current_angle
            except (ValueError, IndexError):
                result['error'] = "Error al parsear ángulo en respuesta"
                
        elif response.startswith("ANGLE_ERR:"):
            # Extraer información de error
            error_parts = response.split(':')[1].split('_')
            if len(error_parts) >= 2:
                error_reason = error_parts[0]
                try:
                    current_angle = float(error_parts[1])
                    result['current_angle'] = current_angle
                    result['error'] = f"Error: {error_reason}"
                except (ValueError, IndexError):
                    result['error'] = f"Error: {response.split(':')[1]}"
            else:
                result['error'] = f"Error: {response.split(':')[1]}"
        else:
            raise SerialParseError(f"Respuesta inesperada: {response}")
            
        return result
    
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