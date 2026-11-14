import serial
import serial.tools.list_ports
import struct
import math
import time
import numpy as np

def obtener_puertos_com():
    puertos_disponibles = [p.device for p in serial.tools.list_ports.comports()]
    return puertos_disponibles

class MOTORES:
    def __init__(self):
        
        self.arduino = None
        self.conectado = False
        self.Encabezado = b'\xAA' 
        
        self.CMD_VEL = b'\x04'
        self.CMD_MOVE = b'\x05'  
        self.CMD_PARO = b'\x06'
        self.CMD_HABIL = b'\x07'
        self.CMD_DESHABIL = b'\x08'
        self.CMD_MARCHA =  b'\x09'
        
        self.PasosFormat = '<4h' 
        self.MoverFormat = '<2h'
        self.HabilitarFormat = '<?' 
        self.AfirmFormat = '<2B'
        self.AfirmSize = struct.calcsize(self.AfirmFormat)
        
        PASOS_POR_REV = 200
        MICROSTEPPING = 8
        self.RELACION_PASOS_RAD = (PASOS_POR_REV * MICROSTEPPING) / (2 * math.pi)
        self.angRad = [0]*4
        self.pasos = [0]*4
        
    def conectarArd(self, ser):
        self.arduino = ser
        self.conectado = True
    
    def enviarVel(self, v):
        v_pasos = np.round(v * self.RELACION_PASOS_RAD).astype(np.int16)

        packet = self.Encabezado + self.CMD_VEL
        packet += struct.pack(self.PasosFormat, *v_pasos)
        
        self.arduino.write(packet)
    
    def mover(self, ang):
        p_pasos = np.round(ang * self.RELACION_PASOS_RAD).astype(np.int16)

        packet = self.Encabezado + self.CMD_MOVE
        packet += struct.pack(self.MoverFormat, *p_pasos)
        
        self.arduino.write(packet)
    
    def respuesta(self):
        try:
            if self.arduino.in_waiting >= self.AfirmSize:
                data = self.arduino.read(self.AfirmSize)
                
                if data[0] == 0xAA:
                    if data[1] == 0x55:    
                        return True
                    
            self.arduino.reset_input_buffer()
            return False
        except Exception as e:
            print(f"Error en telemetría: {str(e)}")
    
    def habilitar(self):
        packet = self.Encabezado + self.CMD_HABIL
        self.arduino.write(packet)
        
    def deshabilitar(self):
        packet = self.Encabezado + self.CMD_DESHABIL
        self.arduino.write(packet)
    
    def detenerMot(self):
        self.arduino.write(b'\xAA\x06')
    
    def cerrarSerial(self):
        self.conectado = False
        self.arduino.close()
        
class SENSORES:
    def __init__(self):
        
        self.arduino = None
        self.conectado = False
        self.Encabezado = b'\xAA' 
        
        self.CMD_POS = b'\x01'
        
        self.SenFormat = '<B3f'
        self.SenSize = struct.calcsize(self.SenFormat)
        
        self.lecturaAnt = np.zeros(3)
        self.vueltas = np.zeros(3)
        self.desfase = np.zeros(3)
        self.invertido = np.array([False, False, True])
        self.ang_total = np.zeros(3)
        self.angulosCrudos = np.zeros(3)
        self.ultima_pos = np.zeros(3)
        
    def conectarArd(self, ser):
        self.arduino = ser
        self.conectado = True
    
    def corregirAngulo(self):
        lecturaAct = self.angulosCrudos
        
        delta = lecturaAct - self.lecturaAnt
        self.vueltas += (delta < -180).astype(int) - (delta > 180).astype(int)
       
        self.lecturaAnt = lecturaAct
        ang_abierto = (self.vueltas*360) + lecturaAct
        
        ang_corregido = ang_abierto - self.desfase
        self.ang_total = np.where(self.invertido, -ang_corregido, ang_corregido)
                
        self.ultima_pos = self.ang_total
        return self.ang_total

    def obtenerPosicion(self, bloqueo=False):
        try:
            packet = self.Encabezado + self.CMD_POS
            self.arduino.write(packet)
            
            if bloqueo:
                inicio_espera = time.time()
                while self.arduino.in_waiting < self.SenSize:
                    if (time.time() - inicio_espera) > 0.2: 
                        break
                    time.sleep(0.001)
            
            if self.arduino.in_waiting >= self.SenSize:
                data = self.arduino.read(self.SenSize)
                
                if data[0] == 0xAA:
                    
                    valores = struct.unpack(self.SenFormat, data)
                    
                    self.angulosCrudos = np.array([valores[1], valores[2], valores[3]])
                else:
                    self.arduino.reset_input_buffer()
                    
        except Exception as e:
            print(f"Error en telemetría: {str(e)}")

    def cerrarSerial(self):
        self.conectado = False
        self.arduino.close()