#ifndef SETTINGS_H
#define SETTINGS_H

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
const float INITIAL_HEIGHT = 0.3;

#endif // SETTINGS_H 