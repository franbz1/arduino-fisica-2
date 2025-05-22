# Sistema de Lanzamiento de Proyectiles

Este proyecto consiste en un sistema de lanzamiento de proyectiles controlado por Arduino y orquestado desde una interfaz web construida en Django.

## Componentes del Sistema

El proyecto está dividido en dos partes principales:

1. **Firmware Arduino**: Controla los servos y sensores para el lanzamiento físico del proyectil.
2. **Aplicación Django**: Proporciona una interfaz web para controlar el sistema y realizar cálculos físicos.

## Requisitos

### Hardware
- Arduino UNO o compatible
- Sensor MPU6050
- 2 servomotores
- Bandas elásticas
- Estructura mecánica para el lanzador

### Software
- Python 3.8+
- Django 5.0+
- PlatformIO (para compilar y cargar el firmware Arduino)
- Bibliotecas Arduino:
  - Adafruit MPU6050
  - Adafruit Unified Sensor
  - Servo

## Instalación

### Firmware Arduino

1. Instalar PlatformIO en VSCode o como CLI
2. Abrir la carpeta `arduino/` con PlatformIO
3. Compilar y cargar el firmware al Arduino

```bash
cd arduino
pio run -t upload
```

### Aplicación Django

1. Crear y activar un entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Instalar dependencias
```bash
cd django_project
pip install -r requirements.txt
```

3. Ejecutar el servidor de desarrollo
```bash
python manage.py runserver
```

4. Acceder a la aplicación web en `http://localhost:8000/`

## Uso

1. Conectar el Arduino al puerto USB
2. Iniciar la aplicación Django
3. Especificar la distancia deseada en la interfaz web
4. Seguir las instrucciones para ajustar el ángulo, cargar y disparar

## Estructura del Proyecto

### Arduino
- `settings.h`: Constantes del sistema
- `main.cpp`: Programa principal
- `serial_handler.h`: Manejo de comunicación serial
- `mpu6050_handler.h`: Control del sensor MPU6050
- `servo_controller.h`: Control de servomotores
- `utils.h`: Utilidades generales

### Django
- `launcher/`: App para cálculos físicos
- `comm/`: App para comunicación serial
- `ui/`: App para la interfaz de usuario

## Protocolo de Comunicación

| Comando    | Formato         | Acción Arduino                 | Respuesta                |
| ---------- | --------------- | ------------------------------ | ------------------------ |
| PING       | `PING`          | Test básico                    | `PONG`                   |
| SET_ANGLE  | `SET_ANGLE:<θ>` | Mover servo 1 a ángulo θ       | `ANGLE_OK` o `ANGLE_ERR` |
| LOAD       | `LOAD`          | Bajar servo 2 (cargar gatillo) | `LOAD_OK` o `LOAD_ERR`   |
| FIRE       | `FIRE`          | Subir servo 2 (disparar)       | `FIRE_OK` or `FIRE_ERR`  | 