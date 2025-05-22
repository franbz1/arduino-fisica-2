from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from comm.serial_client import SerialClient
import serial

# Create your views here.

def ping_view(request):
    """
    Vista para probar la comunicación serial con el Arduino
    enviando un comando PING y esperando respuesta PONG
    """
    context = {
        'connected': False,
        'response': None,
        'raw_response': None,
        'error': None,
        'settings': {
            'SERIAL_PORT': settings.SERIAL_PORT,
            'SERIAL_BAUDRATE': settings.SERIAL_BAUDRATE,
            'SERIAL_TIMEOUT': settings.SERIAL_TIMEOUT,
        }
    }
    
    if request.method == 'POST':
        try:
            # Crear cliente serial y conectar
            client = SerialClient()
            
            # Intentar conexión manual sin usar el método ping()
            client.connect()
            client.send_command("PING")
            
            # Leer respuesta y mostrarla en la interfaz
            raw_response = client.read_response()
            context['raw_response'] = raw_response
            
            # Verificar si la respuesta es correcta
            if raw_response == "PONG":
                context['connected'] = True
                context['response'] = 'PONG'
                messages.success(request, '¡Conexión exitosa con Arduino!')
            else:
                context['error'] = f'Respuesta incorrecta del Arduino: "{raw_response}"'
                messages.warning(request, f'El Arduino respondió con "{raw_response}" en lugar de "PONG"')
                
        except serial.SerialException as e:
            context['error'] = f'Error de conexión: {str(e)}'
            messages.error(request, f'Error al conectar con Arduino: {str(e)}')
        except Exception as e:
            context['error'] = f'Error: {str(e)}'
            messages.error(request, f'Error inesperado: {str(e)}')
            
    return render(request, 'ui/ping.html', context)

def calculate_view(request):
    """
    Vista para calcular parámetros de lanzamiento según distancia
    (Placeholder - se implementará después)
    """
    return render(request, 'ui/calculate.html')
