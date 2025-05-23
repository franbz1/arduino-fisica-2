from django.urls import path
from . import views

app_name = 'comm'

urlpatterns = [
    path('connect/', views.connect_arduino, name='connect'),
    path('disconnect/', views.disconnect_arduino, name='disconnect'),
    path('test/', views.test_connection, name='test'),
    path('status/', views.connection_status_view, name='status'),
] 