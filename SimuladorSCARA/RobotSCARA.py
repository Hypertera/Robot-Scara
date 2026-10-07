import numpy as np

def Jacobiano(q):
    # Parametros DH
    
    a1 = 20 #
    a2 = 20 # Constantes
    d4 = 10.22 #
    
    q1 = q[0] # d1      #
    q2 = q[1] # theta_1 # Variables Articulares
    q3 = q[2] # theta_2 #
    q4 = q[3] # theta_3 #
    
    A1 = np.array([
    [   1,  0,  0,  0],
    [   0,  1,  0,  0],
    [   0,  0,  1, q1+16.1],
    [   0,  0,  0,  1]
    ])
    
    A2 = np.array([
    [np.cos(q2),  -np.sin(q2),     0,     a1*np.cos(q2)],
    [np.sin(q2),  np.cos(q2),      0,     a1*np.sin(q2)],
    [   0,           0,          1,          0],
    [   0,           0,          0,          1]
    ])
    
    A3 = np.array([
    [np.cos(q3),  -np.sin(q3),     0,     a2*np.cos(q3)],
    [np.sin(q3),  np.cos(q3),      0,     a2*np.sin(q3)],
    [   0,           0,          1,          -5.88],
    [   0,           0,          0,          1]
    ])
    
    A4 = np.array([
    [np.cos(q4),  np.sin(q4),     0,     0],
    [np.sin(q4),  -np.cos(q4),    0,     0],
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
    
    # Tomar la tercera columna de las matrices Zi-1
    Z3 = A14[0:3,2]
    Z2 = A13[0:3,2]
    Z1 = A12[0:3,2]
    Z0 = A1[0:3,2]
    
    J1 = np.reshape(Z0, (3,1))
    J2 = np.reshape(np.cross(Z1,(O4-O1)), (3,1))
    J3 = np.reshape(np.cross(Z2,(O4-O2)), (3,1))
    J4 = np.reshape(np.cross(Z3,(O4-O3)), (3,1))
    
    Jacob = np.block([
        [J1, J2, J3, J4],
        [np.reshape(Z0*0, (3,1)),  np.reshape(Z1, (3,1)), np.reshape(Z2, (3,1)),  np.reshape(Z1, (3,1))],
    ])
    
    Rot = np.array([
    [np.cos(-q2),  -np.sin(-q2),     0],
    [np.sin(-q2),  np.cos(-q2),      0],
    [   0,           0,          1]
    ])
    
    return O1[:3], O2[:3], O3[:3], O4[:3], Rot[0:3,0:3], Jacob

def cinematicaInversa(x, y, elbow_up=False):

    L1 = 20
    L2 = 20
    r2 = x**2 + y**2

    c2 = (r2 - L1**2 - L2**2) / (2 * L1 * L2)

    if abs(c2) > 1:
        q1 = None
        q2 = None
        return q1, q2

    s2 = np.sqrt(1 - c2**2)

    if elbow_up:
        s2 = -s2

    q2 = np.arctan2(s2, c2)

    q1 = np.arctan2(y, x) - np.arctan2(
        L2 * s2,
        L1 + L2 * c2
    )

    return q1, q2

def obtener_splines(t, q):
    t = np.asarray(t)
    q = np.asarray(q)
    n = len(t)
    
    h = np.diff(t)
    
    # Construcción de la matriz tridiagonal M
    diag_sup_inf = h[1:n-2]
    diag_princ = 2 * (h[:-1] + h[1:])
    
    M = np.diag(diag_princ) + np.diag(diag_sup_inf, 1) + np.diag(diag_sup_inf, -1)
    
    # Vector de términos independientes
    f = np.diff(q) / h
    b_vec = 6 * np.diff(f)
    
    # Resolver para g (segundas derivadas / 2)
    g_mid = np.linalg.solve(M, b_vec)
    
    # Aplicar condiciones de frontera natural (0 en los extremos)
    g = np.concatenate(([0], g_mid, [0]))
    
    # Calcular coeficientes de cada tramo
    a = np.diff(g) / (6 * h)
    b = g[:-1] / 2
    c = f - h * (2 * g[:-1] + g[1:]) / 6
    d = q[:-1]
    
    # Retorna una matriz donde cada fila son los coeficientes [a, b, c, d] del tramo
    return np.column_stack((a, b, c, d))

def evaluar_splines_c(S, t, time):
    n = len(t)

    # Identificar el índice del tramo
    if time > t[-1]:
        k = n - 2  # Python usa índices desde 0, el último tramo es n-2
    else:
        # Busca el primer índice donde el tiempo encaja en el intervalo [t_k, t_{k+1}]
        # t[1:] es t_{k+1} y t[:-1] es t_k
        indices = np.where((t[:-1] <= time) & (time <= t[1:]))[0]
        k = indices[0] if indices.size > 0 else 0

    # Diferencia de tiempo respecto al inicio del tramo
    dt = time - t[k]
    
    # Coeficientes del tramo k: [a, b, c, d]
    coeffs = S[k, :]

    # Evaluar posición (qk)
    # S[k,0]*dt^3 + S[k,1]*dt^2 + S[k,2]*dt + S[k,3]
    qk = coeffs[0]*dt**3 + coeffs[1]*dt**2 + coeffs[2]*dt + coeffs[3]
    
    # Evaluar velocidad (qpk) - Derivada
    # 3*S[k,0]*dt^2 + 2*S[k,1]*dt + S[k,2]
    qpk = 3*coeffs[0]*dt**2 + 2*coeffs[1]*dt + coeffs[2]

    return qk, qpk

def normlzr_dist(puntos_arr, I):
    diffs = np.diff(puntos_arr, axis=1)
    dist_segmentos = np.sqrt(np.sum(diffs**2, axis=0))
    dist_acumulada = np.concatenate(([0], np.cumsum(dist_segmentos)))
    
    dist_equidistante = np.linspace(0, dist_acumulada[-1], I)
    
    x_eq = np.interp(dist_equidistante, dist_acumulada, puntos_arr[0, :])
    y_eq = np.interp(dist_equidistante, dist_acumulada, puntos_arr[1, :])
    z_eq = np.interp(dist_equidistante, dist_acumulada, puntos_arr[2, :])
    
    return x_eq, y_eq, z_eq