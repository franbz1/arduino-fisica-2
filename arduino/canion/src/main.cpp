#include <Arduino.h>
#include "settings.h"
#include "serial_handler.h"
#include "mpu6050_handler.h"
#include "servo_controller.h"
#include "utils.h"

// LED indicador para estados
const int STATUS_LED = 13;

// Tiempo mínimo entre lecturas de comandos (ms)
const unsigned long CMD_INTERVAL = 50;
unsigned long lastCmdTime = 0;

// Temporizador para detectar timeouts
SimpleTimer cmdTimer;

void setup() {
  // Inicializar LED de estado
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, HIGH);
  
  // Inicializar comunicación serial
  setupSerial();
  
  // Inicializar MPU6050
  if (!setupMPU6050()) {
    // Parpadear LED para indicar error de MPU
    while (true) {
      digitalWrite(STATUS_LED, HIGH);
      delay(200);
      digitalWrite(STATUS_LED, LOW);
      delay(200);
    }
  }
  
  // Inicializar servos
  setupServos();
  
  // Todo inicializado correctamente
  digitalWrite(STATUS_LED, LOW);
}

void loop() {
  // Leer comandos en intervalos regulares
  if (millis() - lastCmdTime >= CMD_INTERVAL) {
    lastCmdTime = millis();
    
    // Leer y procesar comando serial
    Command cmd = readSerialCommand();
    
    // Procesar comando según su tipo
    switch (cmd.type) {
      case CMD_PING:
        sendResponse("PONG");
        break;
        
      case CMD_SET_ANGLE:
        // Verificar límites de ángulo
        if (cmd.value < ANGLE_MIN || cmd.value > ANGLE_MAX) {
          sendResponse("ANGLE_ERR");
        } else {
          // Iniciar timer para timeout
          cmdTimer.start();
          
          // Mover al ángulo
          bool success = moveToAngle(cmd.value);
          
          // Enviar respuesta
          sendResponse(success ? "ANGLE_OK" : "ANGLE_ERR");
        }
        break;
        
      case CMD_LOAD:
        // Cargar mecanismo
        bool loadSuccess = loadMechanism();
        sendResponse(loadSuccess ? "LOAD_OK" : "LOAD_ERR");
        break;
        
      case CMD_FIRE:
        // Disparar mecanismo
        bool fireSuccess = fireMechanism();
        sendResponse(fireSuccess ? "FIRE_OK" : "FIRE_ERR");
        break;
        
      case CMD_NONE:
        // Ningún comando recibido
        break;
    }
  }
} 