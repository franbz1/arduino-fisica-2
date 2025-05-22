from django.urls import path
from . import views

app_name = 'ui'

urlpatterns = [
    # Ruta para probar la comunicación serial (ping)
    path('ping/', views.ping_view, name='ping'),
    # Ruta para el cálculo de parámetros
    path('calculate/', views.calculate_view, name='calculate'),
    # Ruta para mostrar resultados
    path('results/', views.results_view, name='results'),
    # Ruta para ajustar ángulo
    path('set-angle/', views.set_angle_view, name='set_angle'),
] 