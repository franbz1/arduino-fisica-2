# Objetivo y Contexto

Este proyecto consiste en desarrollar un *sistema de lanzamiento de proyectiles* controlado por Arduino y orquestado desde una interfaz web construida en Django. El objetivo es permitir al usuario especificar la distancia a la que desea disparar una canica, calcular en el cliente la velocidad y ángulo óptimos usando física de movimiento parabólico, y luego enviar comandos al Arduino para ajustar servos, cargar resorts y disparar.

El Arduino sólo actuará sobre comandos recibidos (sin cálculos internos), utilizando un protocolo serial claro, y todas las constantes del sistema (límites de servos, constantes elásticas, tolerancias, posiciones de muescas) se almacenarán en archivos de configuración `settings`. La interfaz Django guiará al usuario paso a paso, gestionará la comunicación serial mediante Python y ofrecerá feedback y manejo de errores.

---

## Implementación Paso a Paso

A continuación se describe de forma **muy detallada**, en formato Markdown, el flujo completo y los pasos que otra IA o desarrollador debe seguir para implementar el sistema. No incluye el código final, solo indicaciones precisas.

---

## Estructura de Carpetas y Archivos

A continuación se muestra la organización de carpetas y archivos recomendada para todo el proyecto:

project-root/
├── arduino/
│   ├── src/
│   │   ├── main.cpp             # Lógica principal de firmware
│   │   ├── settings.h           # Constantes del sistema para Arduino
│   │   ├── serial_handler.h     # Parsing y envío/recepción serial
│   │   ├── mpu6050_handler.h    # Lectura y filtrado de MPU6050
│   │   ├── servo_controller.h   # Funciones moveToAngle, load, fire
│   │   └── utils.h              # Helpers (timers, mapeos)
│   └── platformio.ini           # Configuración de compilación
│
├── django_project/
│   ├── manage.py
│   ├── django_project/
│   │   ├── settings.py          # Configuración general Django
│   │   └── urls.py              # Rutas globales
│   ├── launcher/                # App de cálculo físico
│   │   ├── __init__.py
│   │   ├── physics.py           # solve_for(distance)
│   │   └── tests.py             # Unit tests del módulo physics
│   ├── comm/                    # App de comunicación serial
│   │   ├── __init__.py
│   │   ├── serial_client.py     # Clase SerialClient
│   │   └── exceptions.py        # Errores específicos (Timeout, ParseError)
│   ├── ui/                      # App de interfaz web
│   │   ├── __init__.py
│   │   ├── views.py             # calculate_view, set_angle_view, etc.
│   │   ├── urls.py              # Rutas de UI (/calculate/, /set-angle/...)
│   │   └── templates/
│   │       ├── base.html
│   │       ├── calculate.html
│   │       ├── results.html
│   │       ├── angle_ready.html
│   │       ├── loaded.html
│   │       └── fired.html
│   └── requirements.txt         # Dependencias Python (Django, pyserial...)
└── README.md                    # Documentación general y flujo del proyecto

arduino/: todo el firmware en C++ organizado en headers y main.

django_project/: proyecto Django con tres apps: launcher, comm y ui.

settings: constantes en arduino/src/settings.h y réplica en django_project/launcher/settings.py (o bien importadas desde el proyecto principal).

---

### 1. Configuración de Archivos de Constantes

1. **Archivo Arduino (`settings.h`)**

   * Nombre: `settings.h`
   * Definir constantes:

     ```cpp
     // Límite mínimo y máximo de ángulo para servo 1 (en grados)
     const float ANGLE_MIN = 0.0;
     const float ANGLE_MAX = 80.0;
     // Tolerancia de lectura MPU para considerar ángulo alcanzado (en grados)
     const float ANGLE_TOLERANCE = 1.0;
     // Posiciones de muescas para resortes (en metros)
     const float NOTCH_POSITIONS[3] = {0.10, 0.20, 0.30};
     // Constante elástica por banda (k) (en N/m)
     const float K_ELASTIC = 120.0;
     // Timeout para comandos serial (en milisegundos)
     const unsigned int SERIAL_TIMEOUT_MS = 2000;
     // Posiciones de servo 2 (gatillo) para "loaded" y "fired" (en grados)
     const float SERVO2_LOADED_POS = 45.0;
     const float SERVO2_FIRED_POS = 0.0;
     // Altura inicial del cañon en m
     const float Initial_hight = 0.3;
     ```

2. **Archivo Django/Python (`settings.py`)**

   * Nombre: `settings.py` (dentro de la app correspondiente)
   * Copiar las mismas constantes, usando sintaxis Python:

     ```python
     # Ángulos de servo 1\ nANGLE_MIN = 0.0
     ANGLE_MAX = 80.0
     ANGLE_TOLERANCE = 1.0

     # Muescas de resortes
     NOTCH_POSITIONS = [0.10, 0.20, 0.30]

     # Constante k de elasticidad
     K_ELASTIC = 120.0

     # Timeout serial (en segundos)
     SERIAL_TIMEOUT = 2

     # Posiciones de servo 2 (gatillo)
     SERVO2_LOADED_POS = 45.0
     SERVO2_FIRED_POS = 0.0

     # Tolerancia para calcular numero de bandas
     BANDS_TOLERANCE = 1.0
     ```

---

### 2. Protocolo Serial\ n

Definir los **comandos** y **respuestas** que usa el Arduino:\ n

| Comando    | Formato         | Acción Arduino                 | Respuesta                |
| ---------- | --------------- | ------------------------------ | ------------------------ |
| PING       | `PING`          | Test básico                    | `PONG`                   |
| SET\_ANGLE | `SET_ANGLE:<θ>` | Mover servo 1 a ángulo θ       | `ANGLE_OK` o `ANGLE_ERR` |
| LOAD       | `LOAD`          | Bajar servo 2 (cargar gatillo) | `LOAD_OK` o `LOAD_ERR`   |
| FIRE       | `FIRE`          | Subir servo 2 (disparar)       | `FIRE_OK` or `FIRE_ERR`  |

**Nota:** Todos los mensajes terminan con `\n`.

---

### 3. Firmware Arduino (C++)

1. **Inicialización**

   * Incluir `settings.h`, `Servo.h`, librería MPU6050.
   * Inicializar `Serial.begin(baudRate)`.
   * Configurar servos y sensor en `setup()`.

2. **Loop Principal**

   * Llamar a `readSerialCommand()` para obtener línea completa.
   * Parsear comando y argumentos.
   * Para cada comando:

     * **`PING`**: responder `PONG`.
     * **`SET_ANGLE`**:

       1. Validar `ANGLE_MIN <= θ <= ANGLE_MAX`.
       2. Llamar `moveToAngle(θ)`:

          * Mover servo 1 a posición mapeada.
          * Leer MPU hasta `|angle_current - θ| <= ANGLE_TOLERANCE`.
       3. Responder `ANGLE_OK` o `ANGLE_ERR`.
     * **`LOAD`**:

       1. Mover servo 2 a `SERVO2_LOADED_POS`.
       2. Responder `LOAD_OK`.
     * **`FIRE`**:

       1. Mover servo 2 a `SERVO2_FIRED_POS`.
       2. Responder `FIRE_OK`.
   * Gestionar timeouts usando `SERIAL_TIMEOUT_MS`.

---

### 4. Módulo de Cálculo en Django (Python)

1. **Archivo**: `launcher/physics.py`

2. **Función principal**: `def solve_for(distance: float) -> dict:`

   * Parámetros:

     * `distance`: distancia deseada (m).
   * Uso de constantes: `ANGLE_MIN`, `ANGLE_MAX`, `K_ELASTIC`, `NOTCH_POSITIONS`, `g = 9.81`.
   * Búsqueda:

     1. Para ángulo `α` en rango \[`ANGLE_MIN`, `ANGLE_MAX`] con paso adecuado (e.g. 0.5°):

        * Calcular `v = sqrt((g * distance) / sin(2 * α))`.
        * Verificar `v` realista.
     2. Seleccionar el primer `α` y su `v`.
   * Calcular número de bandas (`nBands`) y `notch_index`:

     * Para cada valor en `NOTCH_POSITIONS`, hallar `n = ceil((m * v^2) / (K_ELASTIC * x^2))`.
   * Devolver:

     ```python
     {
       'angle': best_alpha,
       'velocity': best_v,
       'n_bands': nBands,
       'notch': notch_index
     }
     ```

3. **Tests**: cubrir casos límite, distancias pequeñas y grandes.

---

### 5. Cliente Serial en Django (Python)

1. **Archivo**: `comm/serial_client.py`
2. **Clase**: `class SerialClient:`

   * **Constructor**: `__init__(self, port: str, baud: int, timeout: float)`

     * Abrir puerto con `serial.Serial(port, baud, timeout)`.
   * **Métodos**:

     * `def send_command(self, cmd: str) -> None`:

       * `self.serial.write(f"{cmd}\n".encode())`
     * `def read_response(self) -> str`:

       * `return self.serial.readline().decode().strip()`
     * `def set_angle(self, angle: float) -> bool`:

       * `send_command(f"SET_ANGLE:{angle}")`
       * Leer respuesta y retornar `True` si `ANGLE_OK`.
     * `def load(self) -> bool`:

       * Similar con `LOAD` → espera `LOAD_OK`.
     * `def fire(self) -> bool`:

       * Similar con `FIRE` → espera `FIRE_OK`.

---

### 6. Vistas y Flujo en Django

1. **Formulario de Distancia**

   * **URL**: `/calculate/`
   * **View**: `calculate_view(request)`

     * GET: mostrar form.
     * POST: llamar `solve_for(distance)` y renderizar `results.html`.

2. **Resultados y Botones**

   * **Template**: `results.html`

     * Mostrar `angle`, `velocity`, `n_bands`, `notch`.
     * Botón `Ajustar Ángulo` → POST a `/set-angle/`.

3. **Ajuste de Ángulo**

   * **URL**: `/set-angle/`
   * **View**: `set_angle_view(request)`

     * Leer `angle` de POST.
     * Llamar `serial_client.set_angle(angle)`.
     * Si OK: render `angle_ready.html` con botón `Cargar Resortes`.
     * Si error: mensaje de alerta y botón `Reintentar`.

4. **Carga de Resortes**

   * **URL**: `/load/`
   * **View**: `load_view(request)`

     * Esperar confirmación manual del usuario (`<button>`).
     * Al confirmar: `serial_client.load()`.
     * Renderizar `loaded.html` con botón `Disparar`.

5. **Disparo**

   * **URL**: `/fire/`
   * **View**: `fire_view(request)`

     * Llamar `serial_client.fire()`.
     * Render `fired.html` con resumen y botón `Reset`.

6. **Reset**

   * **URL**: `/reset/`
   * **View**: `reset_view(request)`

     * Opcional: opcionalmente enviar comandos para dejar servo en 0.

---

### 7. Pruebas E2E

1. **Simular**: usar Arduino conectado y ejecutar el flujo completo:  calcular → set-angle → load → fire.
2. **Verificar mensajes sérial**: en cada paso confirmar `*_OK`.
3. **Feedback UI**: comprobar alertas de errores y reintentos.
