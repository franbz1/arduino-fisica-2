#include <Arduino.h>
#include "settings.h"
#include "serial_handler.h"

// LED indicador para estados
const int STATUS_LED = 13;

// Tiempo mínimo entre lecturas de comandos (ms)
const unsigned long CMD_INTERVAL = 50;
unsigned long lastCmdTime = 0;

void setup() {
  // Inicializar LED de estado
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, HIGH);
  
  // Inicializar comunicación serial
  setupSerial();
  
  // Todo inicializado correctamente
  digitalWrite(STATUS_LED, LOW);
  
  // Mensaje de bienvenida
  Serial.println("Sistema listo para recibir comandos");
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
        // Parpadeo breve del LED para indicar recepción
        digitalWrite(STATUS_LED, HIGH);
        delay(50);
        digitalWrite(STATUS_LED, LOW);
        break;
        
      case CMD_SET_ANGLE:
        // Verificar límites de ángulo
        if (cmd.value < ANGLE_MIN || cmd.value > ANGLE_MAX) {
          sendResponse("ANGLE_ERR");
        } else {
          // Por ahora, solo confirmamos que recibimos el comando sin mover el servo
          sendResponse("ANGLE_OK");
          Serial.print("Ángulo recibido: ");
          Serial.println(cmd.value);
        }
        break;
        
      case CMD_LOAD:
        // Solo confirmamos el comando, sin controlar servos
        sendResponse("LOAD_OK");
        break;
        
      case CMD_FIRE:
        // Solo confirmamos el comando, sin controlar servos
        sendResponse("FIRE_OK");
        break;
        
      case CMD_NONE:
        // Ningún comando recibido
        break;
    }
  }
} 