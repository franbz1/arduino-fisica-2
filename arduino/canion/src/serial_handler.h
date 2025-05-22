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
  delay(100); // Pequeña espera para estabilizar la conexión
}

// Parsea un comando recibido por serial
Command parseCommand(const char* cmd) {
  Command result = {CMD_NONE, 0.0};
  
  // Eliminar espacios al inicio y final
  int start = 0;
  int end = strlen(cmd) - 1;
  
  while (cmd[start] == ' ' && start < end) {
    start++;
  }
  
  while (cmd[end] == ' ' && end > start) {
    end--;
  }
  
  // Si solo hay espacios, devolver CMD_NONE
  if (start > end) {
    return result;
  }
  
  // Comando PING
  if (strncmp(&cmd[start], "PING", 4) == 0) {
    result.type = CMD_PING;
    return result;
  }
  
  // Comando SET_ANGLE:XX.X
  if (strncmp(&cmd[start], "SET_ANGLE:", 10) == 0) {
    result.type = CMD_SET_ANGLE;
    char* valueStart = (char*)&cmd[start + 10];
    // Verificar que hay un valor numérico después del :
    if (*valueStart) {
      result.value = atof(valueStart); // Convertir la parte después del ":" a float
    } else {
      // Si no hay valor, mantenemos CMD_NONE
      result.type = CMD_NONE;
    }
    return result;
  }
  
  // Comando LOAD
  if (strncmp(&cmd[start], "LOAD", 4) == 0) {
    result.type = CMD_LOAD;
    return result;
  }
  
  // Comando FIRE
  if (strncmp(&cmd[start], "FIRE", 4) == 0) {
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
      
      if (c == '\n' || c == '\r') {
        // Si el buffer está vacío (solo recibimos \n o \r), ignoramos
        if (cmdIndex == 0) {
          continue;
        }
        
        // Fin de comando
        cmdBuffer[cmdIndex] = '\0'; // Terminar string
        Command parsedCmd = parseCommand(cmdBuffer);
        cmdIndex = 0; // Resetear índice para el próximo comando
        
        // Parsear y retornar el comando
        return parsedCmd;
      } else {
        // Agregar caracter al buffer
        cmdBuffer[cmdIndex++] = c;
      }
    }
    
    // Si llegamos aquí y el buffer está lleno sin encontrar \n, descartamos
    if (cmdIndex >= CMD_BUFFER_SIZE - 1) {
      cmdIndex = 0;
      // Notificar error de buffer
      Serial.println("ERR_BUFFER_OVERFLOW");
    }
  }
  
  return emptyCommand;
}

// Envía una respuesta por serial
void sendResponse(const char* response) {
  // Asegurar que enviamos exactamente el texto sin caracteres adicionales
  Serial.print(response);
  Serial.print("\r\n"); // Terminación de línea estándar
  Serial.flush(); // Asegurarse de que se envíe completamente
}

#endif // SERIAL_HANDLER_H 