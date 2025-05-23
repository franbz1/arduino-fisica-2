#ifndef MPU6050_HANDLER_H
#define MPU6050_HANDLER_H

#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "settings.h"

// Prototipos de funciones
bool setupMPU6050();
float getCurrentAngle();
bool isAngleReached(float targetAngle);
void calibrateMPU();

// Variables globales
extern Adafruit_MPU6050 mpu;
extern float filteredAngle;

#endif // MPU6050_HANDLER_H