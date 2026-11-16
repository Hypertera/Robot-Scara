import os
import sys
import numpy as np
import time
from Comandos import MOTORES, SENSORES, obtener_puertos_com, serial
from PySide6.QtCore import Qt, QTimer
import pyqtgraph.opengl as gl
from Vistas.tab_controles import TabControles
from Vistas.tab_crear import TabCrear
from Vistas.tab_opciones import TabOpciones
import json

from RobotSCARA import (Jacobiano, cinematicaInversa, 
                        obtener_splines, evaluar_splines_c,
                        normlzr_dist)

from PySide6.QtWidgets import (QApplication, QMainWindow, 
                               QWidget, QVBoxLayout,
                               QPushButton, QTabWidget, 
                               QMessageBox, QFileDialog,)

from PySide6.QtGui import (QFontDatabase, QFont, 
                           QShortcut, QKeySequence, 
                           QIcon)

def resolver_ruta(ruta_relativa):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, ruta_relativa)

class Variables():
    # ARDUINOS
    
    mot = MOTORES()
    sen = SENSORES()
    
    # BEZIÉR
    
    puntos_x = []
    puntos_y = []
    puntos_z = []
    len_puntos = len(puntos_x)
    bezier = None
    indice_edicion = 0
    espcd = [1,2,5,10]
    idx_espacio = 3   
    tam_puntos = 10
    clasificacion = None
    
    # ENCODERS
    
    qp = np.zeros(4, dtype=np.float64) 
    q = np.zeros(3, dtype=np.float64)
    qs = np.zeros(4, dtype=np.float64)
    altura = 150
    
    conv = np.array([(2*np.pi)/0.8, 5.0, 5.0, 0])
    conv2 = np.array([0.8/(2*np.pi), 1/5, 1/5])
    
    kx = 3.0
    ky = 3.0
    kz = 3.0
    vel = [1, 2, 4, 6, 8, 10]
    len_vel = len(vel)
    codo_arriba = False
    
    # PLOT SCARA/TRAYECTORIA
    
    puntos_graficos = gl.GLScatterPlotItem() 
    puntos_graficos.setDepthValue(10)
    
    lineas_guia = gl.GLLinePlotItem()       
    Trayectoria_plot = gl.GLLinePlotItem()
    Trayectoria_plot2 = gl.GLLinePlotItem()
    
    Art1 = gl.GLScatterPlotItem(color=(1, 0.9411765, 0, 1.0), 
                                size=20, pxMode=True)
    Art1.setDepthValue(10) 
    Art2 = gl.GLScatterPlotItem(color=(1, 0.9411765, 0, 1.0), 
                                size=20, pxMode=True)
    Art2.setDepthValue(10) 
    Art23 = gl.GLScatterPlotItem(color=(1, 0.9411765, 0, 1.0), 
                                size=20, pxMode=True)
    Art23.setDepthValue(10) 
    Art3 = gl.GLScatterPlotItem(color=(1, 0.9411765, 0, 1.0), 
                                size=20, pxMode=True)
    Art3.setDepthValue(10) 
    Eslbn = gl.GLLinePlotItem(color=(1, 0.9411765, 0, 1), width=10, 
                              mode='line_strip', antialias=True)
    Eslbn.setDepthValue(10) 
    
varbls = Variables()

class InterfazScara(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Scara By @Hypertera")
        self.resize(1300, 1000)
        self.setStyleSheet("background-color: #212424; color: #ffffff;")
       
        if sys.platform == "darwin":
            self.nombre_icono = "icon.icns"
            self.atajo_guardar = "Meta+G"
            self.atajo_abrir = "Meta+O"
            self.atajo_limpiar = "Meta+X"
            self.atajo_deshacer = "Meta+Z"
            self.atajo_pantalla = "Meta+Ctrl+F"
        else:
            self.nombre_icono = "icon.ico"
            self.atajo_guardar = "Ctrl+G"
            self.atajo_abrir = "Ctrl+O"
            self.atajo_limpiar = "Ctrl+X"
            self.atajo_deshacer = "Ctrl+Z"
            self.atajo_pantalla = "F11"
        
        self.setWindowIcon(QIcon(resolver_ruta(self.nombre_icono)))
        self.atajo_pantalla = QShortcut(QKeySequence(self.atajo_pantalla), self)
        self.atajo_pantalla.activated.connect(self.alternar_pantalla_completa)
        
        # FUENTES
        
        self.fuente_tabs = QFont("JetBrains Mono", 10)  
        self.fuente_tabs.setBold(True) 
        
        etiqueta = QFont('JetBrains Mono', 11)
        etiqueta.setBold(True)
        
        etiqueta2 = QFont('JetBrains Mono', 9)
        etiqueta.setBold(True)
        
        etiqueta3 = QFont('JetBrains Mono', 20)
        etiqueta3.setBold(True)
        
        etiqueta4 = QFont("Bruno Ace", 14)
        etiqueta4.setBold(True)
        
        self.etiqueta5 = QFont("Bruno Ace", 13)
        self.etiqueta5.setBold(True)
        
        sw_lbl = QFont('JetBrains Mono', 12)
        sw_lbl.setBold(True)
        
        etiqueta_nodo = QFont('Bruno Ace', 11)
        etiqueta_nodo.setBold(True)
        
        # PNG's
        
        self.ruta_switch_on = resolver_ruta("switch.png").replace("\\", "/")
        self.ruta_switch_off = resolver_ruta("switch2.png").replace("\\", "/")
        self.ruta_casa = resolver_ruta("casa0.png").replace("\\", "/")
        self.ruta_abajo = resolver_ruta("abajo.png").replace("\\", "/")
        self.ruta_izq = resolver_ruta("izq.png").replace("\\", "/")
        self.ruta_arriba = resolver_ruta("arriba.png").replace("\\", "/")
        self.ruta_der = resolver_ruta("der.png").replace("\\", "/")
        
        # TIMERS
        
        self.ejecutando_trayectoria = False 
        self.timerSimul = QTimer()
        self.timerSimul.timeout.connect(self.simulacion)
        self.timerRobot = QTimer()
        self.timerRobot.timeout.connect(self.bucle_princpl)
        
        # ÍNDICES
        
        self.idx_vel = 0
        self.idx_inicio = 0
        self.idx_adic = 0
        
        # VARIABLES DE PRUEBA/SEGUIMIENTO
        
        self.t_inicial = 0.0
        self.t_prueba = 60
        self.pos_buf = np.empty(4, dtype=np.float64)
        self.vel_buf = np.empty(4, dtype=np.float64)
        self.detener = False
        self.seg_listo = False
        
        # VARIABLES DE MOVIMIENTO
        
        self.en_marcha = False
        self.escala_vel = 0.5
        self.escala_vel_z = 0.75
        self.rutina = 0
        paso_tornillo = 0.8
        omega_max = 16.0
        self.vel_max_z = omega_max*paso_tornillo/(2*np.pi)
        self.motores = False
        
        # VARIABLES DE CONEXIÓN/CALIBRACIÓN
        
        self.inicio = False
        self.calibrado = False
        self.conexion_exitosa = False
        
        # HISTORIAL
        
        self.historial = [] 
        
        # VISORES
        
        self.grid = gl.GLGridItem()
        self.grid.setSize(x=100, y=100)
        self.grid.setSpacing(x=varbls.espcd[varbls.idx_espacio], y=varbls.espcd[varbls.idx_espacio])

        self.grid2 = gl.GLGridItem()
        self.grid2.setSize(x=100, y=100)
        self.grid2.setSpacing(x=10, y=10)
        
        self.lbl_etiqueta = gl.GLTextItem(
            text="", 
            font=etiqueta_nodo,
            color=(241, 196, 15, 255)
            )
        
        self.lbl_etiqueta.setDepthValue(10) 
        
        self.view = gl.GLViewWidget()
        self.view.addItem(self.lbl_etiqueta)
        self.crear_visor(self.view, self.grid, 1)
        
        self.view2 = gl.GLViewWidget()
        self.crear_visor(self.view2, self.grid2, 2)
        
        # PESTAÑAS
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.tabs = QTabWidget()
        self.tabs.setFont(etiqueta)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #2e5883; padding: 10px 20px; margin: 2px; border-radius: 8px; }
            QTabBar::tab:selected { background: #14375e; color: white; }
        """)
        
        self.main_layout.addWidget(self.tabs)

        self.tab_grafica = TabCrear(self, etiqueta, etiqueta2, 
                                    etiqueta4, sw_lbl)
        
        self.tab_controles = TabControles(self, etiqueta, etiqueta2, 
                                          etiqueta4, self.etiqueta5, 
                                          sw_lbl)
        
        self.tab_opciones = TabOpciones(self, etiqueta, etiqueta2, 
                                        etiqueta3, etiqueta4, self.etiqueta5, 
                                        varbls)

        self.tabs.addTab(self.tab_grafica, "Crear")
        self.tabs.addTab(self.tab_controles, "Controles")
        self.tabs.addTab(self.tab_opciones, "Opciones")
        
        barra_herramientas = self.addToolBar("Herramientas")
        barra_herramientas.setMovable(False) 
        barra_herramientas.setStyleSheet("""
            QToolBar { background-color: #222222; border-bottom: 1px solid #444; padding: 5px; spacing: 10px; }
            QToolButton { background-color: #3d3d3d; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; }
            QToolButton:hover { background-color: #3498db; }
        """)
        
        self.btn_z = self.tab_controles.botones_jog["A1"][0]
        
        barra_herramientas.addSeparator()
        
        btn_top_cargar = barra_herramientas.addAction("📂 Cargar trayectoria")
        btn_top_cargar.setFont(etiqueta)
        btn_top_cargar.triggered.connect(self.cargar)
        btn_top_cargar.setShortcut(self.atajo_abrir) 
        
        barra_herramientas.addSeparator()
        
        btn_top_guardar = barra_herramientas.addAction("💾 Guardar como")
        btn_top_guardar.setFont(etiqueta)
        btn_top_guardar.triggered.connect(self.guardar)
        btn_top_guardar.setShortcut(self.atajo_guardar) 
        
        barra_herramientas.addSeparator() 
        
        btn_top_deshacer = barra_herramientas.addAction("↶")
        btn_top_deshacer.triggered.connect(self.deshacer)
        btn_top_deshacer.setShortcut(self.atajo_deshacer) 
        btn_top_deshacer.setFont(etiqueta)
        
        barra_herramientas.addSeparator()
        
        btn_top_salir = barra_herramientas.addAction("Salir")
        btn_top_salir.setFont(etiqueta)
        btn_top_salir.triggered.connect(self.cerrar_App)
        btn_top_salir.setShortcut("Esc") 
        
    def alternar_pantalla_completa(self):
        if self.isFullScreen():
            self.showNormal() 
        else:
            self.showFullScreen() 

    def crear_boton(self, texto, color, color_h):
        btn = QPushButton(texto, font=self.fuente_tabs)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; 
                font-weight: bold;
                border-radius: 8px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {color_h};
            }}
            QPushButton:disabled {{
                background-color: #3d3d3d; 
                color: #7f8c8d;            
                border: 1px solid #555555;
            }}
        """)
        return btn

    def actualizar_robot(self, T1, T2, T3, T4):
        T23 = np.array([T2[0], T2[1], T3[2]])
        
        varbls.Art1.setData(pos=np.array([T1]))
        varbls.Art2.setData(pos=np.array([T2]))
        varbls.Art23.setData(pos=np.array([T23]))
        varbls.Art3.setData(pos=np.array([T3]))

        line_vertices = np.vstack([T1, T2, T23, T3, T4])
        varbls.Eslbn.setData(pos=line_vertices)
        
    def crear_visor(self, view, grid, a):
        
        etiqueta = QFont('Bruno Ace', 20)
        etiqueta.setBold(True)
        
        etiqueta1 = QFont('Bruno Ace', 13)
        etiqueta1.setBold(True)
        
        etiqueta2 = QFont('Bruno Ace', 7)
        etiqueta2.setBold(True)
        
        pts_x = np.array([[-50, 0, 0], [50, 0, 0]])
        pts_y = np.array([[0, -50, 0], [0, 50, 0]])
        
        ejeX = gl.GLLinePlotItem(pos=pts_x, 
                                      color=(1, 0, 0, 0.4), 
                                      width=2, 
                                      antialias=True)
        
        lbl_x_pos = gl.GLTextItem(pos=(53, -2, 0), 
                                       text="x", 
                                       font=etiqueta,
                                       color=(255, 0, 0, 150))
        
        ejeY = gl.GLLinePlotItem(pos=pts_y, 
                                      color=(0, 1, 0, 0.4), 
                                      width=2, antialias=True)
        
        lbl_y_pos = gl.GLTextItem(pos=(-2, 53, 0), 
                                       text="y", 
                                       font=etiqueta1,
                                       color=(0, 255, 0, 150))
        
        valores_x = np.arange(-40, 41, 10)
        
        for val in valores_x:
            if val < 0:
                desfase = 2.5
            else:
                desfase = 1.3
            lbl_num_x = gl.GLTextItem(
                pos=(val-desfase, -56, 0), 
                text=str(val), 
                font=etiqueta2,
                color=(200, 200, 200, 255)
            )
            
            lbl_num_y = gl.GLTextItem(
                pos=(-60, val+desfase,  0), 
                text=str(val), 
                font=etiqueta2,
                color=(200, 200, 200, 255) 
            )
            
            view.addItem(lbl_num_x)
            view.addItem(lbl_num_y)
        
        view.addItem(ejeX)
        view.addItem(ejeY)
        view.addItem(lbl_x_pos)
        view.addItem(lbl_y_pos)
        
        view.setCameraPosition(distance=150, elevation=35, azimuth=-60)
        view.setBackgroundColor('#232627')
       
        view.addItem(grid)
        
        Area = gl.GLLinePlotItem(color=(1, 1, 1, 1), width=5, 
                                  mode='line_strip', antialias=True)
        # Brazo
        
        brazo = 40
        t = np.linspace(0, np.deg2rad(164), 250)
        x1 = brazo*np.cos(t)
        y1 = brazo*np.sin(t)
        z = np.zeros(250)
        xn1 = np.flip(x1)
        yn1 = np.flip(-y1)
        
        x1 = np.hstack([xn1, x1])
        y1 = np.hstack([yn1, y1])
        z1 = np.hstack([z, z])
        
        #Base
        
        base = 11
        t = np.linspace(0, np.deg2rad(90), 250)
        x2 = base*np.cos(t)
        y2 = base*np.sin(t)
        xn2 = np.flip(x2)
        yn2 = np.flip(-y2)
        
        x2 = np.flip(np.hstack([xn2, x2]))
        y2 = np.flip(np.hstack([yn2, y2]))
        z2 = np.flip(np.hstack([z, z]))
        
        xf = np.hstack([x1,x2])
        yf = np.hstack([y1,y2])
        zf = np.hstack([z1,z2])
        
        xf = np.append(xf, x1[0])
        yf = np.append(yf, y1[0])
        zf = np.append(zf, 0)
        
        posiciones = np.vstack([xf,yf,zf]).T
        
        Area.setData(pos=posiciones, color=(1, 1, 1, 0.4), width=2, antialias=True)
        
        view.addItem(Area)
        
        if a == 1:
            view.addItem(varbls.puntos_graficos)
            view.addItem(varbls.lineas_guia)
            view.addItem(varbls.Trayectoria_plot)
        
        elif a == 2:
            view.setCameraPosition(distance=200, elevation=45, azimuth=-60)
            view.setBackgroundColor('#232627')
           
            view.addItem(grid)
            
            Tornillo = gl.GLLinePlotItem(pos=np.array([[0, 0, 10.51],
                                                       [0, 0, 57]]), 
                                         color=(0.784314, 0.784314, 0.784314, 1.0),
                                         width=10, 
                                         mode='line_strip', antialias=True)
            
            Arco = gl.GLLinePlotItem(color=(1, 0.9411765, 0, 1), width=10, 
                                      mode='line_strip', antialias=True)
            
            Cuadro = gl.GLLinePlotItem(color=(1, 0.9411765, 0, 1), width=10, 
                                      mode='line_strip', antialias=True)
            
            Platform = gl.GLLinePlotItem(color=(1, 0.9411765, 0, 1), width=10, 
                                      mode='line_strip', antialias=True)
            
            Platform2 = gl.GLLinePlotItem(color=(1, 0.9411765, 0, 1), width=10, 
                                      mode='line_strip', antialias=True)
            
            altura = 10.510
            alturaPlt = 61.1
            linea = 20.5
            arco = 6.5
            plt = 2.8
            
            xc = np.array([0, -linea, -linea, 0, -linea, -linea, 0,
                           -linea, -linea, 0, -linea, -linea])
            
            yc = np.array([arco, arco, -arco, -arco, -arco, -arco, -arco,
                           -arco, arco, arco, arco, arco])
            
            zc = np.array([0, 0, 0, 0, 0, altura, altura, altura, altura,
                           altura, altura, 0])
            
            t = np.linspace(0, np.pi/2, 250)
            
            xp = plt*np.cos(t)
            yp = plt*np.sin(t)
            xnp = np.flip(xp)
            ynp = np.flip(-yp)
            
            x1 = arco*np.cos(t)
            y1 = arco*np.sin(t)
            xn1 = np.flip(x1)
            yn1 = np.flip(-y1)
            z0 = np.ones(250)
            
            x2p = np.hstack([xnp, xp])
            y2p = np.hstack([ynp, yp])
            z2p = np.hstack([z0*alturaPlt-4.1, z0*alturaPlt-4.1])
            
            x3p = np.flip(np.hstack([xnp, xp]))
            y3p = np.flip(np.hstack([ynp, yp]))
            z3p = np.flip(np.hstack([z0*alturaPlt, z0*alturaPlt]))
            
            xfp = np.append(x2p, x3p)
            yfp = np.append(y2p, y3p)
            zfp = np.append(z2p, z3p)
            
            xfp2 = -xfp
            yfp2 = -yfp
            zfp2 = zfp
            
            x2 = np.hstack([xn1, x1])
            y2 = np.hstack([yn1, y1])
            z2 = np.hstack([z0*0, z0*0])
            
            x3 = np.flip(np.hstack([xn1, x1]))
            y3 = np.flip(np.hstack([yn1, y1]))
            z3 = np.flip(np.hstack([z0*altura, z0*altura]))
            
            xf = np.append(x2, x3)
            yf = np.append(y2, y3)
            zf = np.append(z2, z3)
            
            xf = np.append(xf, 0)
            yf = np.append(yf, -arco)
            zf = np.append(zf, 0)
            
            posiciones = np.vstack([xf,yf,zf]).T
            
            Arco.setData(pos=posiciones)
            
            posiciones = np.vstack([xfp,yfp,zfp]).T
            
            Platform.setData(pos=posiciones)
            
            posiciones = np.vstack([xfp2,yfp2,zfp2]).T
            
            Platform2.setData(pos=posiciones)
            
            posiciones = np.vstack([xc,yc,zc]).T
            
            Cuadro.setData(pos=posiciones)
            
            view.addItem(Tornillo)
            view.addItem(Arco)
            view.addItem(Cuadro)
            view.addItem(Platform)
            view.addItem(Platform2)
            view.addItem(varbls.Art1)
            view.addItem(varbls.Art2)
            view.addItem(varbls.Art23)
            view.addItem(varbls.Art3)
            view.addItem(varbls.Eslbn)
            view.addItem(varbls.Trayectoria_plot2)
        
            T1, T2, T3, T4, _ = Jacobiano(varbls.q)
            self.actualizar_robot(T1, T2, T3, T4)
            
    def actualizar_visor_puntos(self):

        posiciones = np.vstack([varbls.puntos_x, varbls.puntos_y, varbls.puntos_z]).T
            
        if len(varbls.puntos_x) > 0 and self.tab_grafica.sw_puntos.isChecked():
             posiciones = np.vstack([varbls.puntos_x, varbls.puntos_y, varbls.puntos_z]).T
             num_pts = len(varbls.puntos_x)
             
             colores = np.zeros((num_pts, 4))
             colores[:] = [0.10196, 0.737255, 0.611765, 1]
             
             if self.tab_grafica.sw_insertar_inicio.isChecked():
                 self.idx_ultimo = 0
             else:
                 self.idx_ultimo = len(varbls.puntos_x) - 1
                 
             x = varbls.puntos_x[self.idx_ultimo]
             y = varbls.puntos_y[self.idx_ultimo]
             z = varbls.puntos_z[self.idx_ultimo]
             
             if self.tab_grafica.widget_edicion.isVisible() and 0 <= varbls.indice_edicion < num_pts:
                 colores[varbls.indice_edicion] = [1, 0, 0, 1]
                 
                 x = varbls.puntos_x[varbls.indice_edicion]
                 y = varbls.puntos_y[varbls.indice_edicion]
                 z = varbls.puntos_z[varbls.indice_edicion]
                
                 self.lbl_etiqueta.setData(
                    text=f" P{varbls.indice_edicion} | x:{x:.1f} | y:{y:.1f} | z:{z:.1f}",
                    pos=(x+0.5, y+0.5, z+0.5)
                    )
             else:
                 self.lbl_etiqueta.setData(
                    text=f" P{self.idx_ultimo} | x:{x:.1f} | y:{y:.1f} | z:{z:.1f}",
                    pos=(x+0.5, y+0.5, z + 0.5)
                    )
                    
             varbls.puntos_graficos.setData(pos=posiciones, color=colores, size=varbls.tam_puntos, pxMode=True)
 
        else:
            self.lbl_etiqueta.setData(text="")
            varbls.puntos_graficos.setData(pos=np.empty((0, 3)))
            varbls.lineas_guia.setData(pos=np.empty((0, 3)))
        
        if len(varbls.puntos_x) > 1  and self.tab_grafica.sw_lineas.isChecked():
            varbls.lineas_guia.setData(pos=posiciones, color=(0.52157, 0.31765, 0.13725, 0.8), width=5, antialias=True)
        else:
            varbls.lineas_guia.setData(pos=np.empty((0, 3)))
    
    def actualizar_visor_trayect(self):
        num_puntos = len(varbls.puntos_x)
        
        if num_puntos == 4 and self.idx_inicio == 1 :
            self.idx_inicio = 0
        elif num_puntos == 3 and self.idx_adic == 0:
            self.idx_adic = 2
            
        if num_puntos >= 4:
            aux = []
            trayectoria_completa = []
            for start_idx in range(self.idx_inicio, num_puntos - 3, 3):
                P0 = [varbls.puntos_x[start_idx],     varbls.puntos_y[start_idx],     varbls.puntos_z[start_idx]]
                P1 = [varbls.puntos_x[start_idx + 1], varbls.puntos_y[start_idx + 1], varbls.puntos_z[start_idx + 1]]
                P2 = [varbls.puntos_x[start_idx + 2], varbls.puntos_y[start_idx + 2], varbls.puntos_z[start_idx + 2]]
                P3 = [varbls.puntos_x[start_idx + 3], varbls.puntos_y[start_idx + 3], varbls.puntos_z[start_idx + 3]]
                
                z0 = varbls.puntos_z[start_idx]
                z1 = varbls.puntos_z[start_idx + 1]
                z2 = varbls.puntos_z[start_idx + 2]
                z3 = varbls.puntos_z[start_idx + 3]
                
                rango = np.abs(np.array([[z0], [z1], [z2], [z3]]) - min(z0,z1,z2,z3)) > 1.0
                aux.append(rango)
                
                trayectoria_tramo = self.calcular_trayectoria(P0, P1, P2, P3)
                trayectoria_completa.append(trayectoria_tramo)
                
            varbls.clasificacion = np.hstack(aux)   
            
            varbls.bezier = np.vstack(trayectoria_completa)
            varbls.Trayectoria_plot.setData(pos=varbls.bezier, color=(0.2039, 0.596, 0.8588, 1), width=5, antialias=True)
            varbls.Trayectoria_plot2.setData(pos=varbls.bezier, color=(0.2039, 0.596, 0.8588, 1), width=5, antialias=True)
        
            num_segmnts = varbls.clasificacion.shape[1]
            PUNTS_TRAM = 51
            
            tipos_tramos = [1 if np.any(varbls.clasificacion[:, j]) else 0 for j in range(num_segmnts)]
            
            self.curvs_agrpds = []
            
            if num_segmnts > 0:
                tipo_actual = tipos_tramos[0]
                idx_inicio_grupo = 0
                
                for j in range(1, num_segmnts):
                    if tipos_tramos[j] != tipo_actual:
                        fila_inicio = idx_inicio_grupo * PUNTS_TRAM
                        fila_fin = j * PUNTS_TRAM
                        
                        bloque_punts = varbls.bezier[fila_inicio:fila_fin, :]
                        
                        self.curvs_agrpds.append({
                            "tipo": "RAMPA_Z" if tipo_actual == 1 else "PLANO_XY",
                            "puntos_xyz": bloque_punts
                        })
                        
                        tipo_actual = tipos_tramos[j]
                        idx_inicio_grupo = j
                
                fila_inicio = idx_inicio_grupo * PUNTS_TRAM
                fila_fin = num_segmnts * PUNTS_TRAM
                bloque_punts = varbls.bezier[fila_inicio:fila_fin, :]
                
                self.curvs_agrpds.append({
                    "tipo": "RAMPA_Z" if tipo_actual == 1 else "PLANO_XY",
                    "puntos_xyz": bloque_punts
                })

        else:
            varbls.clasificacion = None
            varbls.bezier = None
            varbls.Trayectoria_plot.setData(pos=np.empty((0, 3)))
            varbls.Trayectoria_plot2.setData(pos=np.empty((0, 3)))

    def calcular_trayectoria(self, P0, P1, P2, P3):
        bdt = 0.02
        S = 1
        
        M = np.array([[-1,  3, -3, 1], 
                      [ 3, -6,  3, 0], 
                      [-3,  3,  0, 0], 
                      [ 1,  0,  0, 0]])
        
        P = np.column_stack((P0, P1, P2, P3))
        
        tiempos = np.arange(0, S+bdt, bdt)
        xy = np.zeros((3, len(tiempos)))
        
        i = 0
        for t in tiempos:
            tn = t / S
            T = np.array([tn**3, tn**2, tn, 1])
            pts = P @ M @ T
            xy[:, i] = pts
            i += 1
        return xy.T

    # =============================================================================
    #   FUNCIONES tab_crear
    # =============================================================================

    def agregar_punto(self):
        try:
            x = float(self.tab_grafica.entradas['x'].text())
            y = float(self.tab_grafica.entradas['y'].text())
            z = float(self.tab_grafica.entradas['z'].text())
            
            self.guardar_historial() 
            
            if self.tab_grafica.sw_insertar_inicio.isChecked():
                varbls.puntos_x.insert(0, x)
                varbls.puntos_y.insert(0, y)
                varbls.puntos_z.insert(0, z)
                self.idx_inicio += 1
                self.actualizar_visor_puntos()
                
                if self.idx_inicio == 3:
                    self.idx_inicio = 0
                    self.actualizar_visor_trayect()
                    
            else:
                varbls.puntos_x.append(x)
                varbls.puntos_y.append(y)
                varbls.puntos_z.append(z)
                self.idx_adic += 1
                self.actualizar_visor_puntos()
                
                if self.idx_adic == 3:
                    self.idx_adic = 0
                    self.actualizar_visor_trayect()
                
            for entry in self.tab_grafica.entradas.values():
                entry.clear()
                
            self.tab_grafica.entradas['x'].setFocus() 
            varbls.len_puntos = len(varbls.puntos_x)
        except ValueError:
            QMessageBox.warning(self, "Error", "Valores numéricos no válidos.")

    def gestionar_cambio_modo_insercion(self, estado):
        
        if self.tab_grafica.sw_insertar_inicio.isChecked():
            self.tab_grafica.btn_añadir.setText("Añadir Punto ↩")
            self.tab_grafica.btn_borrar.setText("Borrar Punto ↩")
            self.idx_ultimo = 0
            self.actualizar_visor_puntos()
        else:
            self.tab_grafica.btn_añadir.setText("Añadir Punto") 
            self.tab_grafica.btn_borrar.setText("Borrar Punto")
            
        if len(varbls.puntos_x) > 0 and not self.tab_grafica.sw_insertar_inicio.isChecked():
            self.idx_ultimo = len(varbls.puntos_x) - 1
            self.tab_grafica.btn_añadir.setText("Añadir Punto") 
            self.tab_grafica.btn_borrar.setText("Borrar Punto")
            self.actualizar_visor_puntos()
        
    def borrar_punto(self):
        if varbls.puntos_x:
            self.guardar_historial()
            if self.tab_grafica.sw_insertar_inicio.isChecked():
                if self.idx_inicio == 0:
                    varbls.puntos_x.pop(0)
                    varbls.puntos_y.pop(0)
                    varbls.puntos_z.pop(0)
                    self.idx_inicio = 2
                    self.actualizar_visor_trayect()
                elif self.idx_inicio == 2:
                    varbls.puntos_x.pop(0)
                    varbls.puntos_y.pop(0)
                    varbls.puntos_z.pop(0)
                    self.idx_inicio = 1
                elif self.idx_inicio == 1:
                    varbls.puntos_x.pop(0)
                    varbls.puntos_y.pop(0)
                    varbls.puntos_z.pop(0)
                    self.idx_inicio = 0
            else:
                if self.idx_adic == 0:
                    varbls.puntos_x.pop()
                    varbls.puntos_y.pop()
                    varbls.puntos_z.pop()
                    self.idx_adic = 2
                    self.actualizar_visor_trayect()
                elif self.idx_adic == 2:
                    varbls.puntos_x.pop()
                    varbls.puntos_y.pop()
                    varbls.puntos_z.pop(0)
                    self.idx_adic = 1
                elif self.idx_adic == 1:
                    varbls.puntos_x.pop()
                    varbls.puntos_y.pop()
                    varbls.puntos_z.pop()
                    self.idx_adic = 0
            varbls.len_puntos = len(varbls.puntos_x)
            self.actualizar_visor_puntos()
        else:
            QMessageBox.information(self, "Aviso", "No hay puntos que borrar.")

    def limpiar_todo(self):
        if varbls.puntos_x:
            self.guardar_historial()
            varbls.puntos_x.clear()
            varbls.puntos_y.clear()
            varbls.puntos_z.clear()
            self.actualizar_visor_puntos()
            self.actualizar_visor_trayect()
            self.idx_inicio = 0
            self.idx_adic = 0
            varbls.len_puntos = len(varbls.puntos_x)
        else:
            QMessageBox.information(self, "Aviso", "No hay puntos que borrar.")
        
    def activar_modo_edicion(self):
        if not varbls.puntos_x:
            QMessageBox.warning(self, "Aviso", "No hay puntos en la trayectoria para modificar.")
            return
        
        self.tab_grafica.widget_insercion.hide()
        self.tab_grafica.widget_edicion.show()
        
        varbls.indice_edicion = 0
        self.cargar_datos_punto_actual()
        self.actualizar_visor_puntos()

    def desactivar_modo_edicion(self):
        self.tab_grafica.widget_edicion.hide()
        self.tab_grafica.widget_insercion.show()
        
        for entry in self.tab_grafica.entradas.values():
            entry.clear()
        self.actualizar_visor_puntos()

    def navegar_punto(self, direccion):
        nuevo_indice = varbls.indice_edicion + direccion
        if nuevo_indice < 0:
            nuevo_indice = varbls.len_puntos - 1
            
        elif nuevo_indice >= varbls.len_puntos:
            nuevo_indice = 0
            
        varbls.indice_edicion = nuevo_indice
        self.cargar_datos_punto_actual()
        self.actualizar_visor_puntos()

    def cargar_datos_punto_actual(self):
        idx = varbls.indice_edicion
        self.tab_grafica.lbl_indice.setText(f"<b>P{idx}</b>")
        
        self.tab_grafica.entradas['x'].setText(str(varbls.puntos_x[idx]))
        self.tab_grafica.entradas['y'].setText(str(varbls.puntos_y[idx]))
        self.tab_grafica.entradas['z'].setText(str(varbls.puntos_z[idx]))

    def guardar_punto_editado(self):
        try:
            idx = varbls.indice_edicion
            self.guardar_historial()
            varbls.puntos_x[idx] = float(self.tab_grafica.entradas['x'].text())
            varbls.puntos_y[idx] = float(self.tab_grafica.entradas['y'].text())
            varbls.puntos_z[idx] = float(self.tab_grafica.entradas['z'].text())
            
            self.actualizar_visor_puntos()
            
            if self.tab_grafica.sw_insertar_inicio.isChecked() and self.idx_inicio == 0:
                self.actualizar_visor_trayect()
            elif not self.tab_grafica.sw_insertar_inicio.isChecked() and self.idx_adic == 0:
                self.actualizar_visor_trayect()
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Asegúrate de ingresar valores numéricos válidos.")

    def guardar_historial(self):
        estado_actual = (
            varbls.puntos_x.copy(),
            varbls.puntos_y.copy(),
            varbls.puntos_z.copy(),
            varbls.len_puntos,
            self.idx_inicio,
            self.idx_adic
        )
        self.historial.append(estado_actual)
        
        if len(self.historial) > 20:
            self.historial.pop(0)

    def deshacer(self):
        if not self.historial:
            return

        ultimo_estado = self.historial.pop()
        
        varbls.puntos_x = ultimo_estado[0]
        varbls.puntos_y = ultimo_estado[1]
        varbls.puntos_z = ultimo_estado[2]
        varbls.len_puntos = ultimo_estado[3]
        self.idx_inicio = ultimo_estado[4]
        self.idx_adic = ultimo_estado[5]
        
        if varbls.indice_edicion >= len(varbls.puntos_x):
            varbls.indice_edicion = max(0, len(varbls.puntos_x) - 1)
            if hasattr(self, 'cargar_datos_punto_actual') and varbls.puntos_x:
                self.cargar_datos_punto_actual()

        self.actualizar_visor_puntos()
        self.actualizar_visor_trayect()

    def guardar(self):
        self.guardar_historial()
        if not varbls.puntos_x:
            QMessageBox.warning(self, "Aviso", "No hay puntos en la trayectoria para guardar.")
            return

        puntos_control = np.vstack([varbls.puntos_x, varbls.puntos_y, varbls.puntos_z]).T
        idx_inicio = np.array(self.idx_inicio)

        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Trayectoria NumPy",
            "trayectoria_robot.npz", 
            "Archivos de NumPy (*.npz)"
        )

        if ruta_archivo:
            try:
                curva_bezier = varbls.bezier if varbls.bezier is not None else np.empty((0, 3))
                
                np.savez(
                    ruta_archivo, 
                    puntos_control=puntos_control, 
                    curva_bezier=curva_bezier,
                    idx_inicio=idx_inicio
                )
                
                QMessageBox.information(self, "Éxito", f"Trayectoria guardada en formato NumPy:\n{ruta_archivo}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{str(e)}")

    def cargar(self):
        self.guardar_historial()
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar Trayectoria NumPy",
            "",
            "Archivos de NumPy (*.npz);;Todos los Archivos (*)"
        )

        if ruta_archivo:
            try:
                with np.load(ruta_archivo) as datos:
                    if 'puntos_control' in datos:
                        matriz_puntos = datos['puntos_control']
                        
                        varbls.puntos_x = matriz_puntos[:, 0].tolist()
                        varbls.puntos_y = matriz_puntos[:, 1].tolist()
                        varbls.puntos_z = matriz_puntos[:, 2].tolist()
                        varbls.len_puntos = len(varbls.puntos_x)
                        
                        if 'curva_bezier' in datos and datos['curva_bezier'].size > 0:
                            varbls.bezier = datos['curva_bezier']
                        else:
                            varbls.bezier = None
                            
                        if 'idx_inicio' in datos:
                            self.idx_inicio = int(datos['idx_inicio'])
                        else:
                            self.idx_inicio = 0
                        
                        self.actualizar_visor_puntos()
                        self.actualizar_visor_trayect()
                    else:
                        QMessageBox.warning(self, "Archivo no compatible", "El archivo .npz no contiene una trayectoria válida para el robot.")
                        
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un fallo al leer el archivo binario:\n{str(e)}")
    
    # =============================================================================
    #   FUNCINES tab_controles | subpantalla_manual
    # =============================================================================
    
    def interfaz_desconectado(self):
        """Función auxiliar para regresar el botón a su estado inicial si falla la búsqueda"""
        self.tab_controles.btn_conectar.setEnabled(True)
        self.tab_controles.btn_conectar.setText("Conectar")
        self.tab_controles.btn_conectar.setStyleSheet("""
            QPushButton {
                background-color: #2e5883;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #274b70;
            }
            QPushButton:disabled {
                background-color: #3d3d3d; 
                color: #7f8c8d;            
                border: 1px solid #555555;
            }
        """)
        
        self.tab_controles.btn_conectar.clicked.disconnect()
        self.tab_controles.btn_conectar.clicked.connect(self.conectar_robot_real)
        
        self.tab_controles.lbl_estado_robot.setText("<b>ROBOT DESCONECTADO</b>")
        self.tab_controles.lbl_estado_robot.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold;")
    
    def siguiente_prt(self):
        
        if self.idx_puerto_actual >= len(self.puertos):
            self.timer_busqueda.stop()
            QMessageBox.warning(self, "No encontrado", "No se encontró ningun disposipositivo.")
            self.interfaz_desconectado()
            self.conexion_exitosa = False
            return
            
        puerto_a_probar = self.puertos[self.idx_puerto_actual]
        
        try:
            ser = serial.Serial(puerto_a_probar, baudrate=250000, timeout=2.0)
            
            dato = ser.read(2)
            
            if dato == b'\xAA\x01':
                ser.write(b'\xAA\x02')
                print("Arduino encontrado en", puerto_a_probar)
                varbls.sen.conectarArd(ser)
            elif dato == b'\xAA\x03':
                ser.write(b'\xAA\x04')
                print("Arduino encontrado en", puerto_a_probar)
                varbls.mot.conectarArd(ser)
            else:
                ser.close()
        except Exception:
            pass
        
        if varbls.sen.conectado and varbls.mot.conectado:
            self.timer_busqueda.stop()
            self.conexion_exitosa = True
            self.tab_controles.btn_conectar.setEnabled(True)
            self.tab_controles.btn_conectar.setText("Desconectar")
            self.tab_controles.btn_conectar.setStyleSheet("""
                QPushButton {
                    background-color: #73180e;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: #931c10; 
                }
                QPushButton:disabled {
                    background-color: #3d3d3d; 
                    color: #7f8c8d;            
                    border: 1px solid #555555;
                }
            """)
             
            self.tab_controles.btn_conectar.clicked.disconnect() 
            self.tab_controles.btn_conectar.clicked.connect(self.desconectar_robot_real) 
            
            self.tab_controles.lbl_estado_robot.setText("<b>ROBOT CONECTADO</b>")
            self.tab_controles.lbl_estado_robot.setStyleSheet("color: #2ecc71; font-size: 12px; font-weight: bold;") 
            self.tab_controles.pantalla_jogging.setEnabled(True)
            self.tab_controles.btn_SCARA.setEnabled(True)
            self.tab_opciones.btn_cargar_cal.setEnabled(True)
            self.tab_opciones.btn_guardar_cal.setEnabled(True)
            self.tab_opciones.btn_habilitar.setEnabled(True)
         
            QApplication.beep()
            self.timerRobot.start(16)

        self.idx_puerto_actual += 1

    def conectar_robot_real(self):
        self.tab_controles.lbl_estado_robot.setText("<b>ESTADO: BUSCANDO ROBOT...</b>")
        self.tab_controles.lbl_estado_robot.setStyleSheet("color: #f1c40f; font-size: 12px; font-weight: bold;") # Amarillo
        self.tab_controles.btn_conectar.setEnabled(False)
        
        self.puertos = obtener_puertos_com()
        
        if not self.puertos:
            QMessageBox.critical(self, "Error", "No se detectó ningún dispositivo.")
            self.interfaz_desconectado()
            return
        
        self.idx_puerto_actual = 0
        
        self.timer_busqueda = QTimer()
        self.timer_busqueda.timeout.connect(self.siguiente_prt)
        self.timer_busqueda.start(50)

    def desconectar_robot_real(self):
        self.timerRobot.stop()
        self.calibrado = False
        self.guardar_vueltas()
        varbls.mot.detenerMot()
        varbls.mot.cerrarSerial()
        varbls.sen.cerrarSerial()
        self.conexion_exitosa = False
        self.interfaz_desconectado()
        self.tab_controles.pantalla_jogging.setEnabled(False)
        self.tab_controles.btn_SCARA.setEnabled(False)
        self.tab_opciones.btn_cargar_cal.setEnabled(False)
        self.tab_opciones.btn_guardar_cal.setEnabled(False)
        self.tab_opciones.btn_habilitar.setEnabled(False)
        
        QApplication.beep()
    
    def cambiar_vel(self, direccion):
        nuevo_idx = self.idx_vel + direccion
        
        if nuevo_idx < 0:
            nuevo_idx = varbls.len_vel - 1
            
        elif nuevo_idx >= varbls.len_vel:
            nuevo_idx = 0
        
        self.idx_vel = nuevo_idx
        
        self.tab_controles.lbl_valor_vel.setText(f"<b>{varbls.vel[nuevo_idx]} cm/s</b>")

    def iniclzr_desplzmnt(self, Pf, Pi):
        
        distancia = np.linalg.norm(Pf - Pi)
    
        tf = 1.6 * distancia / self.vel_max_z
        
        A = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [-3/tf**2, -2/tf, 3/tf**2, -1/tf],
            [2/tf**3, 1/tf**2, -2/tf**3, 1/tf**2]
        ])
        
        B = np.array([
            [Pi[0], Pi[1], Pi[2]],
            [0, 0, 0],
            [Pf[0], Pf[1], Pf[2]],
            [0, 0, 0]
        ])
        
        K = np.array([varbls.kx, varbls.ky, varbls.kz])
        self.D = np.diag(K)
        self.Cof = A @ B
        self.t_final = tf
        
        self.en_marcha = True
        self.t_inicial = time.time()
        
    def desplzmnt_xy(self, band=0):
        if self.rutina == 1 or self.rutina == 4:
            if band == 1:
                x = self.Pf[0]
                y = self.Pf[1]
                
                qd2, qd3 = cinematicaInversa(x, y, varbls.codo_arriba)

                qd = np.array([qd2, qd3])
                q = np.array([varbls.q[1], varbls.q[2]])
                
                qt = qd - q

                varbls.mot.mover(qt*5)
            
            resp = varbls.mot.respuesta()
            if self.rutina == 1 and resp:
                self.rutina = 2
                _, _, _, T4, _ = Jacobiano(varbls.q)
                
                Pi = np.array([T4[0], T4[1], T4[2]])
                self.iniclzr_desplzmnt(self.Pf, Pi)
                
            elif self.rutina == 4 and resp:
                self.rutina = 0
                self.tab_controles.pantalla_jogging.setEnabled(True)
                if self.seg_listo:
                    self.ejecutar_SCARA()
                else:
                    self.habilitar()
            elif resp is None:
                self.rutina = 0
                varbls.mot.detenerMot()
                QMessageBox.warning(self, "Aviso", "La comunicación con Arduino falló, reinicie la aplicación.")
    
    def desplzmnt_z(self,T1,T2,T3,T4,J):
        if self.en_marcha:
            tk = time.time() - self.t_inicial
    
            if tk <= self.t_final:
                
                tk_sq = tk ** 2
        
                self.pos_buf[0], self.pos_buf[1] = 1.0, tk
                self.pos_buf[2], self.pos_buf[3] =  tk_sq, tk * tk_sq
                
                self.vel_buf[0], self.vel_buf[1] = 0.0, 1.0
                self.vel_buf[2], self.vel_buf[3] = 2.0 * tk, 3.0 * tk_sq
                
                xyd = self.pos_buf @ self.Cof
                xypd = self.vel_buf @ self.Cof
                
                e = xyd - T4
                
                b = xypd + self.D @ e
                
                varbls.qp[:], _, _, _ = np.linalg.lstsq(J, b, rcond=None)
                
                varbls.qp *= varbls.conv
                
                varbls.mot.enviarVel(varbls.qp)
            else:
                varbls.mot.detenerMot()
                self.en_marcha = False
                
                if self.rutina == 2:
                    self.rutina = 0
                    self.tab_controles.pantalla_jogging.setEnabled(True)
                    if self.seg_listo:
                        self.ejecutar_SCARA()
                    else:
                        self.habilitar()
                if self.rutina == 3:
                    self.rutina = 4
                    self.desplzmnt_xy(1)
    
    def comprbr_limts(self, x, y, z):
        qd2, qd3 = cinematicaInversa(x, y, varbls.codo_arriba)
        h = np.sqrt(x**2 + y**2)
        
        if (qd2 is None 
            or h < 11 
            or (x<0 and abs(y)<11)
            or z < 0):
            
            QMessageBox.warning(self, "Aviso", "Punto fuera del alcance del Robot.")
            return False
        else:
            return True
    
    def pose_casa(self):
        self.deshabilitar()
        x = 25
        y = 0
        z = 10
        _, _, _, T4, _ = Jacobiano(varbls.q)
        self.Pf = np.array([x,y,z])
        if T4[2] > z or T4[2] == z:
            self.rutina = 1
            self.tab_controles.pantalla_jogging.setEnabled(False)
            self.desplzmnt_xy(1)
        elif T4[2] < z:
            self.rutina = 3
            self.tab_controles.pantalla_jogging.setEnabled(False)
            Pi = np.array([T4[0],T4[1],T4[2]])
            Pf = np.array([T4[0],T4[1],z])
            self.iniclzr_desplzmnt(Pf, Pi)
        
    def posicionar_robot(self, band=0):
        try:
            _, _, _, T4, _ = Jacobiano(varbls.q)
            
            if band == 0:
                x = float(self.tab_controles.entradas_sim['x'].text())
                y = float(self.tab_controles.entradas_sim['y'].text())
                z = float(self.tab_controles.entradas_sim['z'].text())
            else:
                x = varbls.bezier[0,0]
                y = varbls.bezier[0,1]
                z = varbls.bezier[0,2]
                self.seg_listo = True
                self.deshabilitar()
       
            valido = self.comprbr_limts(x, y, z)
            
            if valido:
                self.Pf = np.array([x,y,z])
                self.deshabilitar()
                if T4[2] > z or T4[2] == z:
                    self.rutina = 1
                    self.tab_controles.pantalla_jogging.setEnabled(False)
                    self.desplzmnt_xy(1)
                elif T4[2] < z:
                    self.rutina = 3
                    self.tab_controles.pantalla_jogging.setEnabled(False)
                    Pi = np.array([T4[0],T4[1],T4[2]])
                    Pf = np.array([T4[0],T4[1],z])
                    self.iniclzr_desplzmnt(Pf, Pi)
            else:
                return
        except:
            QMessageBox.warning(self, "Aviso", "Ingresa un punto válido.")

    def cambiar_postura_codo(self, estado):
        
        sw_jog = self.tab_controles.sw_codo
        sw_trayect = self.tab_controles.sw_codo2
        
        switch_pulsado = self.sender()
        if switch_pulsado is None:
            return
            
        nuevo_estado_booleano = switch_pulsado.isChecked()
        varbls.codo_arriba = nuevo_estado_booleano
        
        sw_jog.blockSignals(True)
        sw_trayect.blockSignals(True)
        
        sw_jog.setChecked(nuevo_estado_booleano)
        sw_trayect.setChecked(nuevo_estado_booleano)
        
        texto_dinamico = "Pose 2" if nuevo_estado_booleano else "Pose 1"
        sw_jog.setText(texto_dinamico)
        sw_trayect.setText(texto_dinamico)
        
        sw_jog.blockSignals(False)
        sw_trayect.blockSignals(False)
    
    def actlzr_vel_xy(self, valor):
        self.escala_vel = valor / 100.0
        
        self.tab_controles.lbl_val_vel.setText(f"<b>{valor}%</b>")
        
    def actlzr_vel_z(self, valor):
        self.escala_vel_z = valor / 100.0
        
        self.tab_controles.lbl_val_vel_z.setText(f"<b>{valor}%</b>")

    def mover_art(self, art, dirccn):
        VEL_MAX_A1 = 5.0  
        VEL_MAX_A2 = 5.0  
        vel_z = 12
        
        if art == "A1":
            vel_enviar = (vel_z*self.escala_vel_z) * dirccn
            varbls.mot.enviarVel(np.array([vel_enviar, 0, 0, 0]))
            
        elif art == "A2":
            vel_enviar = (VEL_MAX_A1*self.escala_vel) * dirccn
            varbls.mot.enviarVel(np.array([0, vel_enviar, 0, 0]))
            
        elif art == "A3":
            vel_enviar = (VEL_MAX_A2*self.escala_vel) * dirccn
            varbls.mot.enviarVel(np.array([0, 0, vel_enviar, 0]))

    def detnr_art(self):
        varbls.mot.detenerMot()
         
    # =============================================================================
    #   FUNCIONES tab_controles | subpantalla_trayectoria    
    # =============================================================================
    
    def habilitar(self):
        if self.conexion_exitosa:
            self.tab_controles.btn_SCARA.setEnabled(True)
        else:
            self.tab_controles.btn_SCARA.setEnabled(False)
            
        self.tab_controles.btn_parar.setEnabled(False)
        self.tab_controles.btn_ejec.setEnabled(True) 
        self.tab_controles.btn_conectar.setEnabled(True) 
        self.tab_controles.btn_next.setEnabled(True)
        self.tab_controles.btn_prev.setEnabled(True)
        self.tab_controles.sw_codo2.setEnabled(True)
        
        self.tab_opciones.btn_cargar_cal.setEnabled(True)
        self.tab_opciones.btn_guardar_cal.setEnabled(True)
        self.tab_opciones.btn_habilitar.setEnabled(True)
        
    def deshabilitar(self):
        self.tab_controles.btn_ejec.setEnabled(False) 
        self.tab_controles.btn_conectar.setEnabled(False) 
        self.tab_controles.btn_SCARA.setEnabled(False)
        self.tab_controles.btn_next.setEnabled(False)
        self.tab_controles.btn_prev.setEnabled(False)
        self.tab_controles.sw_codo2.setEnabled(False)
        self.tab_controles.barra_progreso.setValue(0)
        
        self.tab_opciones.btn_cargar_cal.setEnabled(False)
        self.tab_opciones.btn_guardar_cal.setEnabled(False)
        self.tab_opciones.btn_habilitar.setEnabled(False)
    
    def pausa(self):
        if self.idx_bloque_actual == 0:
            self.tab_controles.btn_parar.setEnabled(True)
        self.t_inicial = time.time()
        if not self.seg_listo:
             self.timerSimul.start(16)
        else:
            varbls.sen.arduino.reset_input_buffer()
            varbls.mot.arduino.reset_input_buffer()
            self.timerRobot.start(16)
    
    def segmntr_trayect(self):
        self.segmnts_agrpds = []
        
        vel_xy = varbls.vel[self.idx_vel] 
        for idx, bloque in enumerate(self.curvs_agrpds):
            tipo = bloque["tipo"]
            puntos_xyz = bloque["puntos_xyz"]  
            I = puntos_xyz.shape[0]
            
            qx, qy, qz = normlzr_dist(puntos_xyz.T, I)
            
            t_prueba = np.linspace(0, self.t_prueba, I)
            Spx_p = obtener_splines(t_prueba, qx)
            Spy_p = obtener_splines(t_prueba, qy)
            Spz_p = obtener_splines(t_prueba, qz)
            
            muestras = 1000
            tiempos_eval = np.linspace(t_prueba[0], t_prueba[-1], muestras)
            
            x_p = np.zeros(muestras)
            y_p = np.zeros(muestras)
            z_p = np.zeros(muestras)
            
            for i, tk in enumerate(tiempos_eval):
                x_p[i], _ = evaluar_splines_c(Spx_p, t_prueba, tk)
                y_p[i], _ = evaluar_splines_c(Spy_p, t_prueba, tk)
                z_p[i], _ = evaluar_splines_c(Spz_p, t_prueba, tk)
                
            dx = np.diff(x_p)
            dy = np.diff(y_p)
            dz = np.diff(z_p)
            distancias = np.sqrt(dx**2 + dy**2 + dz**2)
            
            L = np.sum(distancias)
            
            if tipo == "RAMPA_Z":
                vel_ejec = self.vel_max_z
                comp = 1.6
            else:
                vel_ejec = vel_xy
                comp = 1.7
                
            t_final = comp * L / vel_ejec
            
            vectr_t_finl = np.linspace(0, t_final, I)
            
            pasos_angulares = np.linspace(0, np.pi, I)
            suavizado = 0.5 * (1.0 - np.cos(pasos_angulares))
            
            indices = np.linspace(0, 1, I)
            qx_suave = np.interp(suavizado, indices, qx)
            qy_suave = np.interp(suavizado, indices, qy)
            qz_suave = np.interp(suavizado, indices, qz)
            
            Spx_final = obtener_splines(vectr_t_finl, qx_suave)
            Spy_final = obtener_splines(vectr_t_finl, qy_suave)
            Spz_final = obtener_splines(vectr_t_finl, qz_suave)

            bloque_Sp = {
                "tipo": tipo,
                "t_final": t_final,
                "vector_tiempo": vectr_t_finl,
                "Spx": Spx_final,
                "Spy": Spy_final,
                "Spz": Spz_final
            }
            
            self.segmnts_agrpds.append(bloque_Sp)
    
    def ini_seguimiento_SCARA(self):
        if varbls.bezier is None or len(varbls.bezier) == 0:
            QMessageBox.warning(self, "Aviso", "No hay una trayectoria calculada para ejecutar.")
            return
        
        caja_confirmacion = QMessageBox(self)
        caja_confirmacion.setBaseSize(750, 650)
        caja_confirmacion.setIcon(QMessageBox.Question)
        caja_confirmacion.setWindowTitle("Confirmación de Seguridad")
        caja_confirmacion.setText("<h2 style='color: #dddddd; margin-bottom: 10px; background-color: #1e1e1e;'>¿Desea iniciar la ejecución de la trayectoria?</h2>")
        caja_confirmacion.setInformativeText(
            "<p style='font-size: 19px; line-height: 1.5; color: #dddddd; background-color: #1e1e1e;'>"
            "Asegúrese de que el espacio de trabajo del robot SCARA esté libre de obstáculos.<br><br>"
            "<b>Presione ENTER para continuar o ESC para cancelar.</b>"
            "</p>"
        )
       
        boton_aceptar = caja_confirmacion.addButton("Continuar", QMessageBox.AcceptRole)
        boton_cancelar = caja_confirmacion.addButton("Cancelar", QMessageBox.RejectRole)
        
        caja_confirmacion.setDefaultButton(boton_aceptar)
        
        caja_confirmacion.setStyleSheet("""
            QMessageBox { background-color: #1e1e1e; }
            QLabel { color: #ffffff; font-size: 12px; }
            QPushButton { 
                background-color: #1e1e1e; color: white; 
                padding: 6px 15px; border-radius: 4px; min-width: 80px; 
            }
            QPushButton:focus { border: 1px solid #0063b2; } 
        """)
        
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy
        espaciador_ancho = QSpacerItem(450, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout_interno = caja_confirmacion.layout()
        layout_interno.addItem(espaciador_ancho, layout_interno.rowCount(), 0, 1, layout_interno.columnCount())
        
        QApplication.beep()
        caja_confirmacion.exec()
        
        if caja_confirmacion.clickedButton() == boton_cancelar:
            return 
        
        varbls.sen.arduino.reset_input_buffer()
        varbls.mot.arduino.reset_input_buffer()
        
        if not self.motores:
            self.activar_desactivar()
            
        self.posicionar_robot(band=1)

    def ejecutar_SCARA(self):
        self.timerRobot.stop()
        self.timerRobot.timeout.disconnect(self.bucle_princpl)
        self.timerRobot.timeout.connect(self.seguimnt_SCARA)
        
        self.tab_controles.barra_progreso.setValue(0)
        
        K = np.array([varbls.kx, varbls.ky, varbls.kz])
        self.D = np.diag(K)
        
        self.idx_bloque_actual = 0
        self.t_barra = 0
        self.tk = 0
        self.segmntr_trayect() 
        
        for i in range(len(self.segmnts_agrpds)):
            bloque = self.segmnts_agrpds[i]
            self.t_barra += bloque["t_final"]
            
        self.ejecutar_segmento()

    def ini_seguimiento(self):
        
        if varbls.bezier is None or len(varbls.bezier) == 0:
            QMessageBox.warning(self, "Aviso", "No hay una trayectoria calculada para ejecutar.")
            return
        
        x = varbls.bezier[0,0]
        y = varbls.bezier[0,1]
        z = varbls.bezier[0,2]
        
        if not self.comprbr_limts(x, y, z):
            return
        
        self.segmntr_trayect()
        
        q2, q3 = cinematicaInversa(x, y, varbls.codo_arriba)
       
        if self.conexion_exitosa and self.calibrado:
            self.timerRobot.stop()
            
        self.tab_controles.barra_progreso.setValue(0)
        self.deshabilitar()
        
        K = np.array([varbls.kx, varbls.ky, varbls.kz])
        self.D = np.diag(K)
        
        varbls.qs[:] = np.array([varbls.bezier[0,2], q2, q3, 0])
        T1, T2, T3, T4, _ = Jacobiano(varbls.qs)
        self.actualizar_robot(T1, T2, T3, T4)
        
        self.idx_bloque_actual = 0
        self.t_barra = 0
        self.tk = 0
        
        for i in range(len(self.segmnts_agrpds)):
            bloque = self.segmnts_agrpds[i]
            self.t_barra += bloque["t_final"]
        
        self.ejecutar_segmento()
        
    def ejecutar_segmento(self):
        if self.idx_bloque_actual >= len(self.segmnts_agrpds):
            self.parar(1)
            if not self.seg_listo:
                if self.conexion_exitosa and self.calibrado:
                    self.timerRobot.start(16)
            else:
                varbls.sen.arduino.reset_input_buffer()
                varbls.mot.arduino.reset_input_buffer()
                QTimer.singleShot(1500, self.terminar)
        else:
            bloque = self.segmnts_agrpds[self.idx_bloque_actual]
            self.t_final = bloque["t_final"]
            self.Spx = bloque["Spx"]
            self.Spy = bloque["Spy"]
            self.Spz = bloque["Spz"]
            self.t = bloque["vector_tiempo"]
            QTimer.singleShot(1350, self.pausa)

    def simulacion(self):
        tk = time.time() - self.t_inicial
        
        T1, T2, T3, T4, J = Jacobiano(varbls.qs)
        
        qkx, qpkx = evaluar_splines_c(self.Spx, self.t, tk)
        qky, qpky = evaluar_splines_c(self.Spy, self.t, tk)
        qkz, qpkz = evaluar_splines_c(self.Spz, self.t, tk)
        
        xyd = np.asarray((qkx,qky, qkz))
        xypd = np.asarray((qpkx,qpky, qpkz))
        
        e = xyd - T4
        
        b = xypd + self.D @ e
        
        varbls.qp[:], _, _, _ = np.linalg.lstsq(J, b, rcond=None)
        
        varbls.qs += varbls.qp*0.016666
                
        self.actualizar_robot(T1,T2,T3,T4) 
        
        porcentaje = int(((tk + self.tk) / self.t_barra) * 100)
        self.tab_controles.barra_progreso.setValue(porcentaje)
        
        if tk >= self.t_final:
            self.timerSimul.stop() 
            self.tk += self.t_final
            self.idx_bloque_actual += 1
            self.ejecutar_segmento()
        
    def parar(self, band=0):
        if not self.seg_listo:
            self.timerSimul.stop() 
            self.habilitar()
            self.terminar(1)
        else:
            varbls.mot.detenerMot()
            self.timerRobot.stop()
            self.tab_controles.btn_parar.setEnabled(False)
            varbls.sen.arduino.reset_input_buffer()
            varbls.mot.arduino.reset_input_buffer()
            
        QApplication.beep()
        if band == 1:
            self.tab_controles.barra_progreso.setValue(100) 
        else:
            if self.conexion_exitosa and self.calibrado:
                QTimer.singleShot(900, self.terminar)
            QMessageBox.information(self, "Aviso", "Seguimiento detenido")
    
    def terminar(self, band=0):
        if band == 0:
            self.seg_listo = False
            self.inicio = True
            self.timerRobot.timeout.disconnect(self.seguimnt_SCARA)
            self.timerRobot.timeout.connect(self.bucle_princpl)
            
        if self.conexion_exitosa and self.calibrado:
            self.timerRobot.start(16)
    
    def seguimnt_SCARA(self):
        tk = time.time() - self.t_inicial
        
        varbls.sen.obtenerPosicion()
        varbls.q[:] = np.radians(varbls.sen.corregirAngulo())
        
        varbls.q *= varbls.conv2
        
        T1, T2, T3, T4, J = Jacobiano(varbls.q)
        
        qkx, qpkx = evaluar_splines_c(self.Spx, self.t, tk)
        qky, qpky = evaluar_splines_c(self.Spy, self.t, tk)
        qkz, qpkz = evaluar_splines_c(self.Spz, self.t, tk)
        
        xyd = np.asarray((qkx,qky, qkz))
        xypd = np.asarray((qpkx,qpky, qpkz))
        
        # Control
        e = xyd - T4
        
        b = xypd + self.D @ e
        
        varbls.qp[:], _, _, _ = np.linalg.lstsq(J, b, rcond=None)
        
        varbls.qp *= varbls.conv
        
        varbls.mot.enviarVel(varbls.qp)
        
        self.actualizar_robot(T1,T2,T3,T4) 
        porcentaje = int(((tk + self.tk) / self.t_barra) * 100)
        self.tab_controles.barra_progreso.setValue(porcentaje)
        
        if tk >= self.t_final:
            varbls.mot.detenerMot()
            self.timerRobot.stop() 
            self.tk += self.t_final
            self.idx_bloque_actual += 1
            self.ejecutar_segmento()   
            
    # =============================================================================
    #   FUNCIONES tab_opciones
    # =============================================================================
            
    def cambiar_espaciado_grid(self, direccion):
        nuevo_idx = varbls.idx_espacio + direccion
        
        if nuevo_idx < 0:
            nuevo_idx = len(varbls.espcd) - 1
            
        elif nuevo_idx >= len(varbls.espcd):
            nuevo_idx = 0
        
        varbls.idx_espacio = nuevo_idx
        valor_actual = varbls.espcd[nuevo_idx]
        
        self.tab_opciones.lbl_valor_grid.setText(f"<b>{valor_actual} cm</b>")
        
        self.grid.setSpacing(x=valor_actual, y=valor_actual)
            
    def actualizar_tam_puntos(self):
        try:
            nuevo_tam = int(self.tab_opciones.entry_tam_puntos.text())
            if nuevo_tam > 0:
                varbls.tam_puntos = nuevo_tam
                self.actualizar_visor_puntos()
                self.actualizar_visor_trayect()
            else:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Valor no válido", "Por favor ingresa un número entero positivo.")
            self.tab_opciones.entry_tam_puntos.setText(str(varbls.tam_puntos))

    def calibrar(self):
        varbls.sen.vueltas = np.zeros(3)
        
        varbls.sen.desfase = np.copy(varbls.sen.angulosCrudos)
        varbls.sen.lecturaAnt = np.copy(varbls.sen.angulosCrudos)
        
        _ = varbls.sen.corregirAngulo()
        
        self.guardar_json_config('calibracionSCARA.json')
        QMessageBox.information(self, "¡Éxito!", "Calibración base en Pose Cero guardada.")

    def cargar_calib(self):
        try:
            ruta_archivo, _ = QFileDialog.getOpenFileName(
                self, "Cargar Estado del Robot", "", "Archivos JSON (*.json)"
            )
            if not ruta_archivo:
                return
                
            with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                data = json.load(archivo)
            
            offsets = []
            vueltas_guardadas = []
            lecturas_previas = []
            
            for s in data["sensores"]:
                offsets.append(s["desfase"])
                vueltas_guardadas.append(s["vueltas"])
                lecturas_previas.append(s["lecturaAnt"])
            
            varbls.sen.desfase = np.array(offsets)
            varbls.sen.vueltas = np.array(vueltas_guardadas)
            varbls.sen.lecturaAnt = np.array(lecturas_previas)
            self.calibrado = True
            self.activar_desactivar()
            self.inicio = True
            QApplication.beep()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar la calibración:\n{str(e)}")
    
    def guardar_json_config(self, nombre_archivo):
        config_dict = {"sensores": []}
        for i in range(3):
            config_dict["sensores"].append({
                "ID": i,
                "desfase": float(varbls.sen.desfase[i]),
                "vueltas": int(varbls.sen.vueltas[i]),
                "lecturaAnt": float(varbls.sen.lecturaAnt[i]),
                "invertido": bool(varbls.sen.invertido[i]),
            })
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=4)
    
    def activar_desactivar(self):
        if self.motores:
            varbls.mot.deshabilitar()
            self.tab_opciones.btn_habilitar.setText("Habilitar")
            self.motores = False
        else:
            varbls.mot.habilitar()
            self.tab_opciones.btn_habilitar.setText("Deshabilitar")
            self.motores = True
    
    def obtener_texto_ganancia(self, tipo):
        
        if tipo == 'Kx':
            return str(varbls.kx)
        elif tipo == 'Ky':
            return str(varbls.ky)
        elif tipo == 'Kz':
            return str(varbls.kz)
        return "1.0"

    def cambiar_ganancia(self, ganancia, direccion):

        key = ganancia.lower() 
        
        if ganancia == 'Kx':
           varbls.kx = round(varbls.kx + direccion, 1)
           
           if varbls.kx < 0.2:
               varbls.kx = 20.0
           elif varbls.kx > 20.0:
               varbls.kx = 0.2
           
           nuevo_valor = varbls.kx 
           
        elif ganancia == 'Ky':
            varbls.ky = round(varbls.ky + direccion, 1)
            
            if varbls.ky < 0.2:
                varbls.ky = 20.0
            elif varbls.ky > 20.0:
                varbls.ky = 0.2
            
            nuevo_valor = varbls.ky
            
        self.tab_controles.labels_ganancias[key].setText(f"<b>{nuevo_valor}</b>")
    
    def bucle_princpl(self):
         varbls.sen.obtenerPosicion()
         varbls.q[:] = np.radians(varbls.sen.corregirAngulo())
         
         varbls.q *= varbls.conv2
         T1,T2,T3,T4,J = Jacobiano(varbls.q)
         
         if T4[2] <= 1:
             if self.btn_z.isEnabled():
                 self.btn_z.setEnabled(False)
                 self.detnr_art()
         else:
             if not self.btn_z.isEnabled():
                 self.btn_z.setEnabled(True)
             
         self.desplzmnt_xy()
         self.desplzmnt_z(T1,T2,T3,T4,J)
         
         if self.calibrado:
            self.actualizar_robot(T1, T2, T3, T4)  
            
         if self.inicio:
             self.inicio = False
             self.pose_casa()
    
    def guardar_vueltas(self):
        self.guardar_json_config('calibracionSCARA.json')
            
    def cerrar_App(self):
        if self.conexion_exitosa:
            if self.calibrado:
                self.guardar_vueltas()
                self.timerRobot.stop()
                self.calibrado = False
            varbls.mot.detenerMot()
            varbls.mot.deshabilitar()
            varbls.mot.cerrarSerial() 
            varbls.sen.cerrarSerial()
        self.close()
    
    def closeEvent(self, event):
        if self.conexion_exitosa:
            if self.calibrado:
                self.guardar_vueltas()
                varbls.mot.detenerMot()
                varbls.mot.deshabilitar()
                varbls.mot.cerrarSerial() 
                varbls.sen.cerrarSerial()
        event.accept()
    
if __name__ == "__main__":
    import ctypes
    if sys.platform == "win32":
        myappid = "hypertera.simuladorscara.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication.instance()
    if app is None: app = QApplication(sys.argv)
    
    JBM = resolver_ruta(
    os.path.join("Fuentes", "JetBrainsMono-Regular.ttf")
    )
    
    JBM_B = resolver_ruta(
    os.path.join("Fuentes", "JetBrainsMono-Bold.ttf")
    )
    
    BA = resolver_ruta(
    os.path.join("Fuentes", "BrunoAce-Regular.ttf")
    )
    
    id_JBM = QFontDatabase.addApplicationFont(JBM)
    id_JBM_B = QFontDatabase.addApplicationFont(JBM_B)
    id_BA = QFontDatabase.addApplicationFont(BA)
    
    if sys.platform == "darwin":
        nombre_icono = "icon.icns"
    else:
        nombre_icono = "icon.ico"
        
    app.setWindowIcon(QIcon(resolver_ruta(nombre_icono)))
    ventana = InterfazScara()
    ventana.showMaximized()
    sys.exit(app.exec())