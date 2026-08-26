import numpy as np
import math as F

def Cinematica(q):
    
    # Parametros DH
    
    a1 = 2.0 #
    a2 = 2.0 # Constantes
    d4 = 0.5 #
    
    q1 = q[0] # d1      #
    q2 = q[1] # theta_1 # Variables Articulares
    q3 = q[2] # theta_2 #
    q4 = q[3] # theta_3 #
    
    A1 = np.array([
    [   1,  0,  0,  0],
    [   0,  1,  0,  0],
    [   0,  0,  1, q1],
    [   0,  0,  0,  1]
    ])
    
    A2 = np.array([
    [F.cos(q2),  -F.sin(q2),     0,     a1*F.cos(q2)],
    [F.sin(q2),  F.cos(q2),      0,     a1*F.sin(q2)],
    [   0,           0,          1,          0],
    [   0,           0,          0,          1]
    ])
    
    A3 = np.array([
    [F.cos(q3),  -F.sin(q3),     0,     a2*F.cos(q3)],
    [F.sin(q3),  F.cos(q3),      0,     a2*F.sin(q3)],
    [   0,           0,          1,          0],
    [   0,           0,          0,          1]
    ])
    
    A4 = np.array([
    [F.cos(q4),  F.sin(q4),     0,     0],
    [F.sin(q4),  -F.cos(q4),    0,     0],
    [   0,           0,        -1,   -d4],
    [   0,           0,         0,     1]
    ])
    
    
    # Multiplicación de Matrices
    A12 =  A1 @ A2
    A13 = A12 @ A3
    A14 = A13 @ A4
    
    # Tomar el Vector de Traslación
    O4 = A14[0:3,3]
    O3 = A13[0:3,3]
    O2 = A12[0:3,3]
    O1 = A1[0:3,3]
   
    return O1[:3], O2[:3], O3[:3], O4[:3], A12[0:3,0:3], A13[0:3,0:3], A14[0:3,0:3]