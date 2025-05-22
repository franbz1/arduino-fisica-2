from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from comm.serial_client import SerialClient
from launcher.physics import solve_for
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
    """
    context = {
        'min_distance': 0.5,  # Distancia mínima en metros
        'max_distance': 10.0,  # Distancia máxima en metros
        'settings': {
            'ANGLE_MIN': settings.ANGLE_MIN,
            'ANGLE_MAX': settings.ANGLE_MAX,
            'K_ELASTIC': settings.K_ELASTIC,
            'NOTCH_POSITIONS': settings.NOTCH_POSITIONS,
            'INITIAL_HEIGHT': settings.INITIAL_HEIGHT,
        }
    }
    
    if request.method == 'POST':
        try:
            # Obtener distancia del formulario
            distance = float(request.POST.get('distance', 0))
            
            # Validar distancia
            if distance < context['min_distance'] or distance > context['max_distance']:
                messages.warning(request, f'La distancia debe estar entre {context["min_distance"]} y {context["max_distance"]} metros')
                return render(request, 'ui/calculate.html', context)
                
            # Calcular parámetros
            result = solve_for(distance)
            print(result)
            if result is None:
                messages.error(request, 'No se pudo calcular una solución viable para esta distancia')
                return render(request, 'ui/calculate.html', context)
                
            # Guardar los resultados en la sesión para usarlos después
            request.session['launch_params'] = {
                'distance': distance,
                'angle': result['angle'],
                'velocity': result['velocity'],
                'n_bands': result['n_bands'],
                'notch': result['notch_index'],
                'notch_position': settings.NOTCH_POSITIONS[result['notch_index']]
            }
            
            # Redirigir a la página de resultados
            return redirect('ui:results')
            
        except ValueError:
            messages.error(request, 'Por favor ingresa un valor numérico válido para la distancia')
        except Exception as e:
            messages.error(request, f'Error en el cálculo: {str(e)}')
    
    return render(request, 'ui/calculate.html', context)

def results_view(request):
    """
    Vista para mostrar los resultados del cálculo
    """
    # Recuperar parámetros de la sesión
    launch_params = request.session.get('launch_params')
    
    if not launch_params:
        messages.warning(request, 'No hay parámetros de lanzamiento calculados')
        return redirect('ui:calculate')
        
    context = {
        'params': launch_params,
        'notch_names': ['Posición 1', 'Posición 2', 'Posición 3']
    }
    
    return render(request, 'ui/results.html', context)

def set_angle_view(request):
    """
    Vista para enviar comando de ajuste de ángulo al Arduino
    """
    # Recuperar parámetros de la sesión
    launch_params = request.session.get('launch_params')
    
    if not launch_params:
        messages.warning(request, 'No hay parámetros de lanzamiento calculados')
        return redirect('ui:calculate')
        
    context = {
        'params': launch_params,
        'angle_set': False,
        'error': None
    }
    
    if request.method == 'POST':
        try:
            angle = launch_params['angle']
            
            # Conectar con Arduino
            client = SerialClient()
            client.connect()
            
            # Enviar comando de ajuste de ángulo
            if client.set_angle(angle):
                context['angle_set'] = True
                messages.success(request, f'Ángulo ajustado a {angle}° correctamente')
            else:
                context['error'] = 'El Arduino no pudo ajustar el ángulo'
                messages.warning(request, 'Error al ajustar el ángulo')
                
        except serial.SerialException as e:
            context['error'] = f'Error de conexión: {str(e)}'
            messages.error(request, f'Error al conectar con Arduino: {str(e)}')
        except Exception as e:
            context['error'] = f'Error: {str(e)}'
            messages.error(request, f'Error inesperado: {str(e)}')
    
    return render(request, 'ui/set_angle.html', context)
