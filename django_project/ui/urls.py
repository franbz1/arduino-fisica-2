from django.urls import path
from . import views

app_name = 'ui'

urlpatterns = [
    # Ruta para probar la comunicación serial (ping)
    path('ping/', views.ping_view, name='ping'),
    # Ruta para el cálculo (se implementará después)
    path('calculate/', views.calculate_view, name='calculate'),
] 