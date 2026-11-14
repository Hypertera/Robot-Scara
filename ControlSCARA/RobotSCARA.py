import numpy as np


def Jacobiano(q):
    a1, a2, d3, d4, d0 = 20.0, 20.0, 5.88, 11.62, 17.5
    
    q1 = q[0] 
    q2 = q[1] 
    q3 = q[2]
    # q4 = q[3] 
    
    q23 = q2 + q3
    
    O3 = np.array([
        a1 * np.cos(q2) + a2 * np.cos(q23), 
        a1 * np.sin(q2) + a2 * np.sin(q23), 
        q1 + d0 - d3
    ])
    
    O4 = np.array([
        a1 * np.cos(q2) + a2 * np.cos(q23),
        a1 * np.sin(q2) + a2 * np.sin(q23),
        q1 + d0 - d3 - d4
    ])
    
    O2 = np.array([a1 * np.cos(q2), a1 * np.sin(q2), q1 + d0])
    O1 = np.array([0.0, 0.0, q1 + d0])
    
    J = np.zeros((3, 4))
    
    J[0, 0] = 0.0
    J[1, 0] = 0.0
    J[2, 0] = 1.0 
    
    J[0, 1] = -O4[1]
    J[1, 1] = O4[0]
    J[2, 1] = 0.0
    
    dx42 = O4[0] - O2[0]
    dy42 = O4[1] - O2[1]
    J[0, 2] = -dy42
    J[1, 2] = dx42
    J[2, 2] = 0.0
    
    J[0, 3] = 0.0
    J[1, 3] = 0.0
    J[2, 3] = 0.0
    
    return O1, O2, O3, O4, J

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

def obtener_splines(t, q, v_inicio=0.0, v_final=0.0):
    t = np.asarray(t, dtype=float)
    q = np.asarray(q, dtype=float)

    n = len(t)

    h = np.diff(t)

    A = np.zeros((n, n))
    rhs = np.zeros(n)

    A[0, 0] = 2 * h[0]
    A[0, 1] = h[0]
    rhs[0] = 6 * ((q[1] - q[0]) / h[0] - v_inicio)

    for i in range(1, n - 1):
        A[i, i - 1] = h[i - 1]
        A[i, i] = 2 * (h[i - 1] + h[i])
        A[i, i + 1] = h[i]

        rhs[i] = 6 * (
            (q[i + 1] - q[i]) / h[i]
            - (q[i] - q[i - 1]) / h[i - 1]
        )

    A[-1, -2] = h[-1]
    A[-1, -1] = 2 * h[-1]
    rhs[-1] = 6 * (
        v_final - (q[-1] - q[-2]) / h[-1]
    )

    M = np.linalg.solve(A, rhs)

    a = np.diff(M) / (6 * h)
    b = M[:-1] / 2
    c = np.diff(q) / h - h * (2 * M[:-1] + M[1:]) / 6
    d = q[:-1]

    return np.column_stack((a, b, c, d))

def evaluar_splines_c(S, t, time):
    n = t.shape[0]

    if time > t[-1]:
        k = n - 2  
    else:
        indices = np.where((t[:-1] <= time) & (time <= t[1:]))[0]
        k = indices[0] if indices.size > 0 else 0

    dt = time - t[k]
    
    coeffs = S[k, :]

    qk = coeffs[0]*dt**3 + coeffs[1]*dt**2 + coeffs[2]*dt + coeffs[3]
    
    qpk = 3*coeffs[0]*dt**2 + 2*coeffs[1]*dt + coeffs[2]

    return qk, qpk

def normlzr_dist(puntos_arr, I):
    diffs = np.diff(puntos_arr, axis=1)
    dist_segmentos = np.sqrt(np.sum(diffs**2, axis=0))

    indices_validos = np.concatenate((
        [True],
        dist_segmentos > 1e-12
    ))

    puntos_arr = puntos_arr[:, indices_validos]

    diffs = np.diff(puntos_arr, axis=1)
    dist_segmentos = np.sqrt(np.sum(diffs**2, axis=0))
    dist_acumulada = np.concatenate((
        [0],
        np.cumsum(dist_segmentos)
    ))

    dist_equidistante = np.linspace(
        0,
        dist_acumulada[-1],
        I
    )

    x_eq = np.interp(
        dist_equidistante, dist_acumulada, puntos_arr[0, :]
    )
    y_eq = np.interp(
        dist_equidistante, dist_acumulada, puntos_arr[1, :]
    )
    z_eq = np.interp(
        dist_equidistante, dist_acumulada, puntos_arr[2, :]
    )

    return x_eq, y_eq, z_eq