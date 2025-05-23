from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from comm.connection_manager import connection_manager
from comm.exceptions import SerialTimeoutError, SerialConnectionError, SerialParseError
from launcher.physics import solve_for
import serial
import time

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
        },
        'ports_available': []
    }
    
    # Obtener puertos disponibles
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        context['ports_available'] = [p.device for p in ports]
    except:
        # Si no podemos obtener los puertos, continuamos sin ellos
        pass
    
    if request.method == 'POST':
        # Usar el connection manager para hacer el test
        result = connection_manager.test_connection()
        
        if result['success']:
            context['connected'] = True
            context['response'] = 'PONG'
            messages.success(request, f'{result["message"]} (Tiempo: {result["response_time"]}ms)')
        else:
            context['error'] = result['error']
            messages.error(request, result['error'])
            
    return render(request, 'ui/ping.html', context)

def calculate_view(request):
    """
    Vista para calcular parámetros de lanzamiento según distancia
    """
    context = {
        'min_distance': 0.1,  # Distancia mínima en metros
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
                'notch_position': settings.NOTCH_POSITIONS[result['notch_index']],
                'INITIAL_HEIGHT': settings.INITIAL_HEIGHT,
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
        'notch_names': ['Posición 1', 'Posición 2', 'Posición 3'],
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
        'error': None,
        'current_angle': None
    }
    
    if request.method == 'POST':
        try:
            angle = launch_params['angle']
            
            # Usar el connection manager para obtener el cliente
            client = connection_manager.get_client()
            
            # Enviar comando de ajuste de ángulo
            result = client.set_angle(angle)
            
            if result['success']:
                context['angle_set'] = True
                context['current_angle'] = result['current_angle']
                messages.success(request, f'Ángulo ajustado a {result["current_angle"]}° correctamente')
                
                # Actualizar el ángulo en los parámetros de lanzamiento con el valor real medido
                launch_params['actual_angle'] = result['current_angle']
                request.session['launch_params'] = launch_params
                context['params'] = launch_params
            else:
                context['error'] = result['error'] or 'Error desconocido al ajustar el ángulo'
                context['current_angle'] = result['current_angle']
                messages.warning(request, context['error'])
                
        except SerialConnectionError as e:
            context['error'] = str(e)
            messages.error(request, str(e))
        except Exception as e:
            context['error'] = f'Error: {str(e)}'
            messages.error(request, f'Error inesperado: {str(e)}')
    
    return render(request, 'ui/set_angle.html', context)

def load_view(request):
    """
    Vista para cargar el mecanismo y disparar (todo en una página)
    """
    # Recuperar parámetros de la sesión
    launch_params = request.session.get('launch_params')
    
    if not launch_params:
        messages.warning(request, 'No hay parámetros de lanzamiento calculados')
        return redirect('ui:calculate')
    
    # Verificar que el ángulo esté configurado
    if not launch_params.get('actual_angle'):
        messages.warning(request, 'Primero debes ajustar el ángulo del cañón')
        return redirect('ui:set_angle')
        
    context = {
        'params': launch_params,
        'loaded': launch_params.get('loaded', False),
        'error': None
    }
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        try:
            # Usar el connection manager para obtener el cliente
            client = connection_manager.get_client()
            
            if action == 'load':
                # Enviar comando de carga
                if client.load():
                    context['loaded'] = True
                    messages.success(request, '¡Mecanismo cargado correctamente!')
                    
                    # Marcar como cargado en la sesión
                    launch_params['loaded'] = True
                    request.session['launch_params'] = launch_params
                    context['params'] = launch_params
                else:
                    context['error'] = 'Error al cargar el mecanismo'
                    messages.error(request, 'El Arduino reportó un error al cargar el mecanismo')
            
            elif action == 'fire':
                # Verificar que esté cargado
                if not launch_params.get('loaded'):
                    messages.warning(request, 'El mecanismo debe estar cargado antes de disparar')
                    return render(request, 'ui/load.html', context)
                
                # Enviar comando de disparo
                if client.fire():
                    messages.success(request, '¡Disparo ejecutado correctamente!')
                    
                    # Marcar como disparado y limpiar estado de carga
                    launch_params['fired'] = True
                    launch_params['loaded'] = False  # Ya no está cargado después del disparo
                    request.session['launch_params'] = launch_params
                    context['params'] = launch_params
                else:
                    context['error'] = 'Error al ejecutar el disparo'
                    messages.error(request, 'El Arduino reportó un error al disparar')
                    
        except SerialConnectionError as e:
            context['error'] = str(e)
            messages.error(request, str(e))
        except Exception as e:
            context['error'] = f'Error: {str(e)}'
            messages.error(request, f'Error inesperado: {str(e)}')
    
    return render(request, 'ui/load.html', context)

def reset_view(request):
    """
    Vista para reiniciar el proceso de lanzamiento
    """
    # Limpiar la sesión
    if 'launch_params' in request.session:
        del request.session['launch_params']
    
    messages.info(request, 'Proceso reiniciado. Puedes calcular un nuevo lanzamiento.')
    return redirect('ui:calculate')
