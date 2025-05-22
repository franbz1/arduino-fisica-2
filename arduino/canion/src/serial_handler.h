#ifndef SERIAL_HANDLER_H
#define SERIAL_HANDLER_H

#include "settings.h"
#include <Arduino.h>

// Buffer para comandos recibidos
const int CMD_BUFFER_SIZE = 32;
char cmdBuffer[CMD_BUFFER_SIZE];
int cmdIndex = 0;

// Estados para parseo de comandos
enum CommandType {
  CMD_NONE,
  CMD_PING,
  CMD_SET_ANGLE,
  CMD_LOAD,
  CMD_FIRE
};

// Estructura para almacenar comandos parseados
struct Command {
  CommandType type;
  float value; // Para comandos con parámetros (ej: SET_ANGLE)
};

// Inicializar comunicación serial
void setupSerial() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Esperar a que se conecte el puerto serial (solo necesario para algunos Arduinos)
  }
  Serial.setTimeout(SERIAL_TIMEOUT_MS);
}

// Parsea un comando recibido por serial
Command parseCommand(const char* cmd) {
  Command result = {CMD_NONE, 0.0};
  
  // Comando PING
  if (strcmp(cmd, "PING") == 0) {
    result.type = CMD_PING;
    return result;
  }
  
  // Comando SET_ANGLE:XX.X
  if (strncmp(cmd, "SET_ANGLE:", 10) == 0) {
    result.type = CMD_SET_ANGLE;
    result.value = atof(cmd + 10); // Convertir la parte después del ":" a float
    return result;
  }
  
  // Comando LOAD
  if (strcmp(cmd, "LOAD") == 0) {
    result.type = CMD_LOAD;
    return result;
  }
  
  // Comando FIRE
  if (strcmp(cmd, "FIRE") == 0) {
    result.type = CMD_FIRE;
    return result;
  }
  
  return result; // CMD_NONE si no se reconoce
}

// Lee un comando completo del puerto serial (hasta \n)
Command readSerialCommand() {
  Command emptyCommand = {CMD_NONE, 0.0};
  
  if (Serial.available() > 0) {
    // Leer bytes hasta encontrar un fin de línea o llenar el buffer
    while (Serial.available() > 0 && cmdIndex < CMD_BUFFER_SIZE - 1) {
      char c = Serial.read();
      
      if (c == '\n') {
        // Fin de comando
        cmdBuffer[cmdIndex] = '\0'; // Terminar string
        cmdIndex = 0; // Resetear índice para el próximo comando
        
        // Parsear y retornar el comando
        return parseCommand(cmdBuffer);
      } else {
        // Agregar caracter al buffer
        cmdBuffer[cmdIndex++] = c;
      }
    }
    
    // Si llegamos aquí y el buffer está lleno sin encontrar \n, descartamos
    if (cmdIndex >= CMD_BUFFER_SIZE - 1) {
      cmdIndex = 0;
    }
  }
  
  return emptyCommand;
}

// Envía una respuesta por serial
void sendResponse(const char* response) {
  Serial.println(response);
  Serial.flush(); // Asegurarse de que se envíe
}

#endif // SERIAL_HANDLER_H 