#include <AccelStepper.h>

const int senNum = 3; // Número de sensores/motores

enum Comandos{
    CMD_VEL = 4,
    CMD_MOVE = 5,
    CMD_PARO = 6,
    CMD_HABIL = 7,
    CMD_DESHABIL = 8
};

// Datos para recibir y mandar comandos
struct __attribute__((packed)) VelPacket
{
    int16_t vel[senNum];
}; VelPacket velData;

struct __attribute__((packed)) MovePacket
{
    int16_t pasos[senNum-1];
}; MovePacket moveData;

struct __attribute__((packed)) AfirmPacket
{
    uint8_t encabezado = 0xAA;
    uint8_t confirm = 0x55;
}; AfirmPacket afirm;

struct __attribute__((packed)) HablPacket
{
    uint8_t encabezado = 0xAA;
    bool activo;
}; HablPacket hablData;

// Pines CNC Shield
const int stepX = 2; const int dirX = 5;
const int stepY = 3; const int dirY = 6;
const int stepZ = 4; const int dirZ = 7;
//const int stepA = 12; const int dirA = 13;
const int enablePin = 8;
bool en_marcha = false;

AccelStepper motorX(AccelStepper::DRIVER, stepX, dirX);
AccelStepper motorY(AccelStepper::DRIVER, stepY, dirY);
AccelStepper motorZ(AccelStepper::DRIVER, stepZ, dirZ);
//AccelStepper motorA(AccelStepper::DRIVER, stepA, dirA);

void setup() {
  Serial.begin(250000);
  
  
  pinMode(enablePin, OUTPUT);
  digitalWrite(enablePin, HIGH); 

  motorX.setMaxSpeed(4074);
  motorY.setMaxSpeed(4074);
  motorZ.setMaxSpeed(4074);
  //motorA.setMaxSpeed(4074);

  motorX.setAcceleration(250);
  motorY.setAcceleration(250);
  motorZ.setAcceleration(250);
  //motorA.setAcceleration(250);

  Serial.write(0xAA); // Encabezado
  Serial.write(0x03); // Mensaje

  while (true){
    if (Serial.available() >= 2){
      uint8_t h = Serial.read();
      uint8_t c = Serial.read();

      if (h == 0xAA && c == 0x04){
        break;
      }

    }

  }

}

void comandos(){
  if (Serial.available() >= 2){

    if (Serial.read() == 0xAA){

      uint8_t cmd = Serial.read();

      if (cmd == CMD_VEL){

        Serial.readBytes((char*)&velData, sizeof(velData));

        int v1 = velData.vel[0];
        int v2 = velData.vel[1];
        int v3 = velData.vel[2];
        //int v4 = velData.vel[3];

        motorX.setSpeed(v1);
        motorY.setSpeed(v2);
        motorZ.setSpeed(v3);
        //motorA.setSpeed(v4);

      }else if (cmd == CMD_MOVE){

        Serial.readBytes((char*)&moveData, sizeof(moveData));

        int p2 = moveData.pasos[0];
        int p3 = moveData.pasos[1];

        motorY.move(p2);
        motorZ.move(p3);
        //motorA.move(p4);

        en_marcha = true;

      }else if (cmd == CMD_PARO){
        motorX.stop();
        motorY.stop();
        motorZ.stop();
        //motorA.stop();
        motorX.setSpeed(0);
        motorY.setSpeed(0);
        motorZ.setSpeed(0);
        //motorA.setSpeed(0);

      }else if (cmd == CMD_HABIL){
        digitalWrite(enablePin, LOW);

      }else if (cmd == CMD_DESHABIL){
        digitalWrite(enablePin, HIGH);

      }

    }

  }

}

void loop(){
  if (en_marcha == false){
    motorX.runSpeed();
    motorY.runSpeed();
    motorZ.runSpeed();
    //motorA.runSpeed();

  }else if (en_marcha == true){
    motorY.run();
    motorZ.run();

    if (motorY.isRunning() == false && motorZ.isRunning() == false){
      Serial.write((uint8_t*)&afirm, sizeof(afirm));
      en_marcha = false;
    }
    
  }

  comandos();
}