#ifndef MPU6050_HANDLER_H
#define MPU6050_HANDLER_H

#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "settings.h"

// Objeto MPU6050
Adafruit_MPU6050 mpu;

// Filtro para estabilizar las lecturas
const float FILTER_FACTOR = 0.95;
float filteredAngle = 0.0;

// Inicializa el sensor MPU6050
bool setupMPU6050() {
  if (!mpu.begin()) {
    return false;
  }
  
  // Configurar rangos del sensor
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  // Dar tiempo para que se inicialice
  delay(100);
  
  // Calibración inicial
  calibrateMPU();
  
  return true;
}

// Calibra el MPU6050 (promedia múltiples lecturas en reposo)
void calibrateMPU() {
  float totalAngle = 0.0;
  const int numReadings = 10;
  
  for (int i = 0; i < numReadings; i++) {
    totalAngle += getCurrentAngle();
    delay(50);
  }
  
  filteredAngle = totalAngle / numReadings;
}

// Devuelve el ángulo actual del sensor (en grados)
float getCurrentAngle() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  
  // Calcular ángulo usando acelerómetro (inclinación respecto a la gravedad)
  float rawAngle = atan2(a.acceleration.y, a.acceleration.z) * 180.0 / PI;
  
  // Aplicar filtro para suavizar lecturas
  filteredAngle = FILTER_FACTOR * filteredAngle + (1.0 - FILTER_FACTOR) * rawAngle;
  
  return filteredAngle;
}

// Verifica si se ha alcanzado el ángulo objetivo dentro de la tolerancia
bool isAngleReached(float targetAngle) {
  float currentAngle = getCurrentAngle();
  return abs(currentAngle - targetAngle) <= ANGLE_TOLERANCE;
}

#endif // MPU6050_HANDLER_H 