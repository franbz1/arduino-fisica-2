#ifndef SERVO_CONTROLLER_H
#define SERVO_CONTROLLER_H

#include <Servo.h>
#include "settings.h"
#include "mpu6050_handler.h"

// Pines para los servos
const int SERVO1_PIN = 9;  // Servo del ángulo
const int SERVO2_PIN = 10; // Servo del gatillo

// Estado actual del sistema
struct ServoState {
  float currentAngle;
  bool isLoaded;
  bool hasFired;
};

// Variables externas
extern Servo servo1;
extern Servo servo2;
extern ServoState state;

// Funciones para control de servos
void setupServos();
int mapAngleToServo(float angle);
void resetServoToZero();
bool moveToAngle(float angle);
bool loadMechanism();
bool fireMechanism();

#endif // SERVO_CONTROLLER_H 