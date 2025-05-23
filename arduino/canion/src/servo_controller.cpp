#include "servo_controller.h"

// Objetos Servo
Servo servo1; // Control de ángulo
Servo servo2; // Control de gatillo/disparo

// Estado actual del sistema
ServoState state = {0.0, false, false};

// Inicializa los servos
void setupServos() {
  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);
  
  // Posición inicial
  servo1.write(0);
  servo2.write(SERVO2_FIRED_POS);
  
  delay(500); // Tiempo para que los servos alcancen la posición inicial
  
  state.currentAngle = 0.0;
  state.isLoaded = false;
  state.hasFired = false;
}

// Mapeo de ángulos físicos a valores de servo (0-180)
int mapAngleToServo(float angle) {
  // Dependiendo de cómo esté montado el servo, 
  // podría necesitar inversión (180 - resultado)
  return map(angle, ANGLE_MIN, ANGLE_MAX, 0, 180);
}

// Regresa el servo a la posición 0 y espera a que se estabilice
void resetServoToZero() {
  servo1.write(0);
  delay(1000); // Tiempo para que el servo llegue a 0 y se estabilice
  state.currentAngle = 0.0;
}

// Mueve el servo al ángulo especificado
bool moveToAngle(float angle) {
  // Verificar que el ángulo esté dentro de los límites
  if (angle < ANGLE_MIN || angle > ANGLE_MAX) {
    return false;
  }
  
  // PASO 1: Regresar a posición 0 primero
  resetServoToZero();
  
  // PASO 2: Recalibrar el MPU6050 desde la posición 0
  calibrateMPU();
  
  // PASO 3: Ahora mover al ángulo objetivo
  // Convertir ángulo físico a posición del servo
  int servoPos = mapAngleToServo(angle);
  
  // Mover el servo gradualmente para mejor precisión
  servo1.write(servoPos);
  
  // Esperar hasta que se alcance el ángulo o timeout
  unsigned long startTime = millis();
  while (!isAngleReached(angle)) {
    if (millis() - startTime > SERIAL_TIMEOUT_MS) {
      return false; // Timeout
    }
    delay(10);
  }
  
  // Actualizar el estado
  state.currentAngle = angle;
  return true;
}

// Carga el mecanismo (mueve servo2 a posición de carga)
bool loadMechanism() {
  servo2.write(SERVO2_LOADED_POS);
  
  // Dar tiempo al servo para llegar a su posición
  delay(500);
  
  // Actualizar estado
  state.isLoaded = true;
  state.hasFired = false;
  
  return true;
}

// Dispara el mecanismo (mueve servo2 a posición de disparo)
bool fireMechanism() {
  // Verificar que esté cargado antes de disparar
  if (!state.isLoaded) {
    return false;
  }
  
  // PASO 1: Ejecutar el disparo moviendo el servo del gatillo
  servo2.write(SERVO2_FIRED_POS);
  
  // Dar tiempo al servo del gatillo para completar la acción
  delay(1000);
  
  // PASO 2: Regresar el servo del ángulo a posición 0 después del disparo
  resetServoToZero();
  
  // PASO 3: Recalibrar el MPU después de regresar a 0
  calibrateMPU();
  
  // Actualizar estado
  state.isLoaded = false;
  state.hasFired = true;
  state.currentAngle = 0.0; // El ángulo ahora es 0
  
  return true;
} 