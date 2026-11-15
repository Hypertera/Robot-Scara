#include <Wire.h>

const int PCA_ADDR = 0x70; // Dirección del multiplexor
const int MT6701_ADDR = 0x06; // Dirección del MT6701
const int senNum = 3; // Número de sensores/motores

enum Comandos{
    CMD_POS = 1,
    CMD_GARRA = 2,
};

struct __attribute__((packed)) AngPacket
{
    uint8_t encabezado = 0xAA;
    float ang[senNum];
}; AngPacket angData;

void setup() {
  Wire.begin();
  Wire.setClock(400000);
  Serial.begin(250000); // baudrate
  
  Serial.write(0xAA);
  Serial.write(0x01);

  while (true){
    if (Serial.available() >= 2){
      uint8_t h = Serial.read();
      uint8_t c = Serial.read();

      if (h == 0xAA && c == 0x02){
        break;
      }

    }

  }
  
}

void pcasel(uint8_t bus) {
  if (bus > 7) return;
  Wire.beginTransmission(PCA_ADDR);
  Wire.write(1 << bus);
  Wire.endTransmission();
}

float obtenerAngulo(int canal) {
  pcasel(canal);
  Wire.beginTransmission(MT6701_ADDR);
  Wire.write(0x03); 
  if (Wire.endTransmission() != 0) return 0xFF;

  Wire.requestFrom(MT6701_ADDR, 2);
  if (Wire.available() == 2) {
    uint16_t rawData = (Wire.read() << 6) | (Wire.read() >> 2);
    return (rawData * 360.0) / 16384.0;
  }
  return 0xFF;
}

void comandos(){
  if (Serial.available() >= 2){

    if (Serial.read() == 0xAA){

      uint8_t cmd = Serial.read();

      if (cmd == CMD_POS){

        for (int i=0; i<senNum; i++){
          float angCrudo = obtenerAngulo(i);

          angData.ang[i] = angCrudo;
        }

        Serial.write((char*)&angData, sizeof(angData));
      }

    }

  }

}

void loop() {
  comandos();
}