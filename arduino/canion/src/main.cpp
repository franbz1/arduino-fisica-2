#include <Arduino.h>
#include "settings.h"
#include "serial_handler.h"
#include "mpu6050_handler.h"
#include "servo_controller.h"

// LED indicador para estados
const int STATUS_LED = 13;

// Tiempo mínimo entre lecturas de comandos (ms)
const unsigned long CMD_INTERVAL = 50;
unsigned long lastCmdTime = 0;

// Variables para respuestas
char responseMsg[50];
bool loadSuccess = false;
bool fireSuccess = false;

void setup() {
  // Inicializar LED de estado
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, HIGH);
  
  // Inicializar comunicación serial
  setupSerial();
  
  // Inicializar MPU6050
  if (!setupMPU6050()) {
    // Parpadear LED para indicar error de MPU
    sendResponse("ERROR_MPU_INIT");
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
        // Parpadeo breve del LED para indicar recepción
        digitalWrite(STATUS_LED, HIGH);
        delay(50);
        digitalWrite(STATUS_LED, LOW);
        break;
        
      case CMD_SET_ANGLE:
        // Verificar límites de ángulo
        if (cmd.value < ANGLE_MIN || cmd.value > ANGLE_MAX) {
          snprintf(responseMsg, sizeof(responseMsg), "ANGLE_ERR:RANGE_EXCEEDED_%.1f", (double)cmd.value);
          sendResponse(responseMsg);
        } else {
          // Encender LED para indicar que se está ajustando
          digitalWrite(STATUS_LED, HIGH);
          
          // Intentar mover al ángulo
          bool success = moveToAngle(cmd.value);
          
          // Obtener ángulo actual del MPU
          float currentAngle = getCurrentAngle();
          
          char angleBuf[10];
          dtostrf(currentAngle, 5, 1, angleBuf);

          // Apagar LED al terminar
          digitalWrite(STATUS_LED, LOW);
          
          // Enviar respuesta con ángulo actual
          if (success) {
            snprintf(responseMsg, sizeof(responseMsg), "ANGLE_OK:%s", angleBuf);
            sendResponse(responseMsg);
          } else {
            snprintf(responseMsg, sizeof(responseMsg), "ANGLE_ERR:TIMEOUT_%s", angleBuf);
            sendResponse(responseMsg);
          }
        }
        break;
        
      case CMD_LOAD:
        // Encender LED para indicar acción
        digitalWrite(STATUS_LED, HIGH);
        
        // Cargar mecanismo
        loadSuccess = loadMechanism();
        
        // Apagar LED al terminar
        digitalWrite(STATUS_LED, LOW);
        
        // Enviar respuesta
        sendResponse(loadSuccess ? "LOAD_OK" : "LOAD_ERR");
        break;
        
      case CMD_FIRE:
        // Encender LED para indicar acción
        digitalWrite(STATUS_LED, HIGH);
        
        // Disparar mecanismo
        fireSuccess = fireMechanism();
        
        // Apagar LED al terminar
        digitalWrite(STATUS_LED, LOW);
        
        // Enviar respuesta
        sendResponse(fireSuccess ? "FIRE_OK" : "FIRE_ERR");
        break;
        
      case CMD_NONE:
        // No hacer nada
        break;
    }
  }
} 