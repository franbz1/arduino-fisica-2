from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .connection_manager import connection_manager
import json

# Create your views here.

@require_http_methods(["POST"])
def connect_arduino(request):
    """
    Vista para establecer conexión con Arduino
    """
    result = connection_manager.connect()
    
    if result['success']:
        messages.success(request, result['message'])
    else:
        messages.error(request, result['error'])
    
    # Retornar JSON para peticiones AJAX
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse(result)
    
    # Para peticiones normales, redirigir de vuelta
    return JsonResponse(result)

@require_http_methods(["POST"])
def disconnect_arduino(request):
    """
    Vista para cerrar conexión con Arduino
    """
    result = connection_manager.disconnect()
    messages.info(request, result['message'])
    
    # Retornar JSON para peticiones AJAX
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse(result)
    
    return JsonResponse(result)

@require_http_methods(["POST"])
def test_connection(request):
    """
    Vista para probar la conexión con Arduino (PING)
    """
    result = connection_manager.test_connection()
    
    if result['success']:
        message = f"{result['message']} (Tiempo: {result['response_time']}ms)"
        messages.success(request, message)
    else:
        messages.warning(request, result['error'])
    
    # Retornar JSON para peticiones AJAX
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse(result)
    
    return JsonResponse(result)

def connection_status_view(request):
    """
    Vista para obtener el estado actual de la conexión
    """
    status = connection_manager.get_status()
    return JsonResponse(status)
