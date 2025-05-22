#ifndef UTILS_H
#define UTILS_H

#include <Arduino.h>

// Clase Timer simple para medir intervalos
class SimpleTimer {
private:
  unsigned long startTime;
  unsigned long duration;
  bool isRunning;
  
public:
  SimpleTimer() : startTime(0), duration(0), isRunning(false) {}
  
  // Iniciar el timer
  void start() {
    startTime = millis();
    isRunning = true;
  }
  
  // Detener el timer y devolver el tiempo transcurrido
  unsigned long stop() {
    if (isRunning) {
      duration = millis() - startTime;
      isRunning = false;
    }
    return duration;
  }
  
  // Obtener tiempo transcurrido sin detener
  unsigned long elapsed() {
    return isRunning ? millis() - startTime : duration;
  }
  
  // Verificar si ha pasado un tiempo determinado
  bool hasElapsed(unsigned long milliseconds) {
    return elapsed() >= milliseconds;
  }
  
  // Resetear el timer
  void reset() {
    startTime = millis();
    duration = 0;
    isRunning = false;
  }
};

// Calcula el promedio de un array de floats
float calculateAverage(float *values, int count) {
  float sum = 0;
  for (int i = 0; i < count; i++) {
    sum += values[i];
  }
  return sum / count;
}

// Mapeo lineal de un valor entre dos rangos (similar a la función map() de Arduino pero con float)
float mapFloat(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// Limita un valor entre un mínimo y máximo
float constrain(float value, float min_value, float max_value) {
  if (value < min_value) return min_value;
  if (value > max_value) return max_value;
  return value;
}

#endif // UTILS_H 