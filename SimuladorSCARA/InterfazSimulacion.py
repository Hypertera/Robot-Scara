import os
import sys
import numpy as np
import time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QIcon
import pyqtgraph.opengl as gl
from RobotSCARA import (Jacobiano, cinematicaInversa, 
                        obtener_splines, evaluar_splines_c,
                        normlzr_dist)

from PySide6.QtWidgets import (QApplication, QMainWindow, 
                               QWidget, QVBoxLayout,
                               QHBoxLayout,QPushButton, 
                               QLineEdit, QLabel, 
                               QFrame, QTabWidget, 
                               QMessageBox, QFileDialog, 
                               QCheckBox, QProgressBar,
                               )

def resolver_ruta(ruta_relativa):
    """ Obtiene la ruta absoluta para recursos empaquetados por PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath("."), ruta_relativa)

class Variables():
    puntos_x = []
    puntos_y = []
    puntos_z = []
    q = np.array([0,0,0,0])
    bezier = None
    indice_edicion = 0
    espcd = [1,2,5,10]
    idx_espacio = 3   
    
    vel = [1.5,2.25,4.5]
    idx_vel = 0   
    codo_arriba = False
    
    tam_puntos = 10 
    
    puntos_graficos = gl.GLScatterPlotItem() 
    lineas_guia = gl.GLLinePlotItem()       
    Trayectoria_plot = gl.GLLinePlotItem()
    Trayectoria_plot2 = gl.GLLinePlotItem()
    
    historial = [] 
    
    ContraPeso = gl.GLScatterPlotItem(color=(1, 0.9411765, 0, 1.0), 
                                size=20, pxMode=True)
    
    Art1 = gl.GLScatterPlotItem(color=(1, 0.9411765, 0, 1.0), 
                                size=20, pxMode=True)
    
    Art2 = gl.GLScatterPlotItem(color=(1, 0.9411765, 0, 1.0), 
                                size=20, pxMode=True)
    
    Art23 = gl.GLScatterPlotItem(color=(1, 0.9411765, 0, 1.0), 
                                size=20, pxMode=True)
    
    Art3 = gl.GLScatterPlotItem(color=(1, 0.9411765, 0, 1.0), 
                                size=20, pxMode=True)
    
    tornillo = gl.GLLinePlotItem(pos=np.array([0, 0, 58]), 
                                 color=(0.784314, 0.784314, 0.784314, 0.5),
                                 width=10, 
                                 mode='line_strip', antialias=True)
    
    Eslbn = gl.GLLinePlotItem(color=(1, 0.9411765, 0, 1), width=10, 
                              mode='line_strip', antialias=True)
    
    Area = gl.GLLinePlotItem(color=(1, 1, 1, 1), width=5, 
                              mode='line_strip', antialias=True)
    
varbls = Variables()

class InterfazScara(QMainWindow):
    def __init__(self):
        super().__init__()
        
        if sys.platform == "darwin":
            self.atajo_guardar = "Meta+G"
            self.atajo_abrir = "Meta+O"
            self.atajo_limpiar = "Meta+X"
            self.atajo_deshacer = "Meta+Z"
            self.atajo_pantalla = "Meta+Ctrl+F"
        else:
            self.atajo_guardar = "Ctrl+G"
            self.atajo_abrir = "Ctrl+O"
            self.atajo_limpiar = "Ctrl+X"
            self.atajo_deshacer = "Ctrl+Z"
            self.atajo_pantalla = "F11"
        
        self.setWindowIcon(QIcon(resolver_ruta("icon.ico")))

        self.atajo_pantalla = QShortcut(QKeySequence(self.atajo_pantalla), self)
        self.atajo_pantalla.activated.connect(self.alternar_pantalla_completa)

        self.timer = QTimer()
        self.timer.timeout.connect(self.simulacion)
        self.t_inicial = 0.0
        self.t_prueba = 60
        
        self.setWindowTitle("Scara By @Hypertera")
        self.resize(1100, 800)
        self.setStyleSheet("background-color: #212424; color: #ffffff;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.tabs = QTabWidget()
        fuente_tabs = QFont("JetBrains Mono", 10)  
        fuente_tabs.setBold(True)        
        self.tabs.setFont(fuente_tabs)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #2e5883; padding: 10px 20px; margin: 2px; border-radius: 5px; }
            QTabBar::tab:selected { background: #14375e; color: white; }
        """)
        self.main_layout.addWidget(self.tabs)

        self.tab_grafica = QWidget()
        self.tab_controles = QWidget()
        self.tab_opciones = QWidget()

        self.tabs.addTab(self.tab_grafica, "Trayectoria")
        self.tabs.addTab(self.tab_controles, "Simulación")
        self.tabs.addTab(self.tab_opciones, "Opciones")
        
        barra_herramientas = self.addToolBar("Herramientas")
        barra_herramientas.setMovable(False) 
        barra_herramientas.setStyleSheet("""
            QToolBar { background-color: #222222; border-bottom: 1px solid #444; padding: 5px; spacing: 10px; }
            QToolButton { background-color: #3d3d3d; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; }
            QToolButton:hover { background-color: #3498db; }
        """)
        
        barra_herramientas.addSeparator()
        
        btn_top_cargar = barra_herramientas.addAction("📂 Abrir Trayectoria")
        btn_top_cargar.triggered.connect(self.cargar)
        btn_top_cargar.setShortcut(self.atajo_abrir) 
        
        barra_herramientas.addSeparator()
        
        btn_top_guardar = barra_herramientas.addAction("💾 Guardar Como...")
        btn_top_guardar.triggered.connect(self.guardar)
        btn_top_guardar.setShortcut(self.atajo_guardar) 
        
        barra_herramientas.addSeparator() 
        
        btn_top_deshacer = barra_herramientas.addAction("↶")
        btn_top_deshacer.triggered.connect(self.deshacer)
        btn_top_deshacer.setShortcut(self.atajo_deshacer) 
        
        barra_herramientas.addSeparator()
        
        btn_top_salir = barra_herramientas.addAction("Salir")
        btn_top_salir.triggered.connect(self.close)
        btn_top_salir.setShortcut("Esc") 
        
        self.grid = gl.GLGridItem()
        self.grid.setSize(x=100, y=100)
        self.grid.setSpacing(x=varbls.espcd[varbls.idx_espacio], y=varbls.espcd[varbls.idx_espacio])

        self.grid2 = gl.GLGridItem()
        self.grid2.setSize(x=100, y=100)
        self.grid2.setSpacing(x=10, y=10)
        
        # --- PESTAÑA: GRÁFICA ---
        self.layout_grafica = QHBoxLayout(self.tab_grafica)
        
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("background-color: #232627; border-radius: 10px;")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        
        etiqueta = QFont('JetBrains Mono', 11)
        etiqueta.setBold(True)
        lbl = QLabel("CREAR TRAYECTORIA")
        lbl.setFont(etiqueta)
        self.sidebar_layout.addWidget(lbl)
        
        self.sidebar_layout.addSpacing(20)
        
        etiqueta = QFont('JetBrains Mono', 9)
        etiqueta.setBold(True)
        self.entradas = {}
        lista_entries = []
        
        for eje in ['X', 'Y', 'Z']:
            
            lbl = QLabel(f"{eje}:")
            lbl.setFont(etiqueta)
            
            self.sidebar_layout.addWidget(lbl)
            entry = QLineEdit()
            
            entry.setPlaceholderText("cm") 
            
            entry.setStyleSheet("""
                QLineEdit {
                    background-color: #3d3d3d; 
                    border: 1px solid #555; 
                    padding: 5px;
                    color: #ffffff;
                }
                QLineEdit::placeholder {
                    color: #888888; /* Gris tenue para diferenciarlo del texto real */
                    font-style: italic; /* Opcional: cursiva para la sugerencia */
                }
            """)
            
            self.sidebar_layout.addWidget(entry)
            self.entradas[eje.lower()] = entry
            
            lista_entries.append(entry)

        lista_entries[0].returnPressed.connect(lambda: lista_entries[1].setFocus())
        
        lista_entries[1].returnPressed.connect(lambda: lista_entries[2].setFocus())
        
        def al_terminar_z():
            if self.widget_edicion.isVisible():
                self.guardar_punto_editado()
                lista_entries[0].setFocus()
            else:
                self.agregar_punto()  
                lista_entries[0].setFocus() 
                
        lista_entries[2].returnPressed.connect(al_terminar_z)
        
        self.widget_insercion = QWidget()
        layout_ins = QVBoxLayout(self.widget_insercion)
        layout_ins.setContentsMargins(0, 0, 0, 0)
        
        self.btn_añadir = self.crear_boton("Añadir Punto", "#2e5883")
        self.btn_añadir.clicked.connect(self.agregar_punto)
        
        self.btn_ir_modificar = self.crear_boton("Modificar Trayect", "#2e5883")
        self.btn_ir_modificar.clicked.connect(self.activar_modo_edicion)
        
        self.btn_borrar = self.crear_boton("Borrar Último", "#73180e")
        self.btn_borrar.clicked.connect(self.borrar_punto)
        self.btn_borrar.setShortcut("Backspace")

        self.btn_limpiar = self.crear_boton("Limpiar Todo", "#73180e")
        self.btn_limpiar.clicked.connect(self.limpiar_todo)
        self.btn_limpiar.setShortcut(self.atajo_limpiar)
        
        self.sidebar_layout.addSpacing(20)
        
        layout_ins.addWidget(self.btn_añadir)
        layout_ins.addWidget(self.btn_ir_modificar)
        layout_ins.addWidget(self.btn_borrar)
        layout_ins.addWidget(self.btn_limpiar)

        self.sidebar_layout.addWidget(self.widget_insercion)

        self.widget_edicion = QWidget()
        layout_edi = QVBoxLayout(self.widget_edicion)
        layout_edi.setContentsMargins(0, 0, 0, 0)

        layout_nav = QHBoxLayout()
        self.btn_prev = self.crear_boton("<", "#7f8c8d")
        self.btn_prev.clicked.connect(lambda: self.navegar_punto(-1))
        self.lbl_indice = QLabel("<b>P0</b>")
        self.lbl_indice.setAlignment(Qt.AlignCenter)
        self.lbl_indice.setStyleSheet("font-size: 14px; color: #f1c40f;")
        self.btn_next = self.crear_boton(">", "#7f8c8d")
        self.btn_next.clicked.connect(lambda: self.navegar_punto(1))
        
        layout_nav.addWidget(self.btn_prev)
        layout_nav.addWidget(self.lbl_indice)
        layout_nav.addWidget(self.btn_next)
        layout_edi.addLayout(layout_nav)

        self.btn_aplicar_cambio = self.crear_boton("Modificar Punto", "#2e5883")
        self.btn_aplicar_cambio.clicked.connect(self.guardar_punto_editado)
        
        self.btn_cancelar_edi = self.crear_boton("Regresar", "#73180e")
        self.btn_cancelar_edi.clicked.connect(self.desactivar_modo_edicion)

        layout_edi.addSpacing(10)
        layout_edi.addWidget(self.btn_aplicar_cambio)
        layout_edi.addWidget(self.btn_cancelar_edi)
        
        self.sidebar_layout.addWidget(self.widget_edicion)
        self.widget_edicion.hide()

        self.sidebar_layout.addStretch()
        
        self.view = gl.GLViewWidget()
        self.crear_visor(self.view, self.grid, 1)
        
        # ---- PESTAÑA: SIMULACIÓN ----
        self.layout_simulacion = QHBoxLayout(self.tab_controles)
        
        self.sidebar2 = QFrame()
        self.sidebar2.setFixedWidth(250)
        self.sidebar2.setStyleSheet("background-color: #232627; border-radius: 10px;")
        self.sidebar_layout2 = QVBoxLayout(self.sidebar2)
        
        etiqueta = QFont('JetBrains Mono', 12)
        etiqueta.setBold(True)
        lbl = QLabel("ROBOT SCARA")
        lbl.setFont(etiqueta)
        self.sidebar_layout2.addWidget(lbl)
        
        self.lbl_pos = QLabel("<b>POSICIONAR ROBOT</b>")
        self.lbl_pos.setAlignment(Qt.AlignCenter)
        self.sidebar_layout2.addWidget(self.lbl_pos)
        
        self.entradas_sim = {}
        for eje in ['X', 'Y', 'Z']:
            lbl_sim = QLabel(f"{eje}:")
            self.sidebar_layout2.addWidget(lbl_sim)
            
            entry_sim = QLineEdit()
            entry_sim.setPlaceholderText("cm")
            entry_sim.setStyleSheet("background-color: #3d3d3d; border: 1px solid #555; padding: 5px; color: white;")
            self.sidebar_layout2.addWidget(entry_sim)
            self.entradas_sim[eje.lower()] = entry_sim
        
        lista_entries_sim = [
            self.entradas_sim['x'], 
            self.entradas_sim['y'], 
            self.entradas_sim['z']
        ]
        
        lista_entries_sim[0].returnPressed.connect(lambda: lista_entries_sim[1].setFocus())
        
        lista_entries_sim[1].returnPressed.connect(lambda: lista_entries_sim[2].setFocus())
        
        lista_entries_sim[2].returnPressed.connect(self.posicionar_robot)
    
        ruta_switch_on = resolver_ruta("switch.png").replace("\\", "/")
        ruta_switch_off = resolver_ruta("switch2.png").replace("\\", "/")
        
        self.sw_codo = QCheckBox("Pose 1")
        self.sw_codo.setChecked(False)
        self.sw_codo.setCursor(Qt.PointingHandCursor)
        self.sw_codo.setStyleSheet(f"""
            QCheckBox {{ spacing: 12px; font-size: 11px; font-weight: bold; color: #ffffff; }}
            QCheckBox::indicator {{ width: 36px; height: 20px; border-radius: 10px; }}
            QCheckBox::indicator:unchecked {{ background-color: #232627; image: url('{ruta_switch_off}'); alignment: left; }}
            QCheckBox::indicator:checked {{ background-color: #232627; image: url('{ruta_switch_on}'); alignment: right; }}
        """)
        self.sidebar_layout2.addWidget(self.sw_codo)
        
        self.sidebar_layout2.addSpacing(20)
        
        self.lbl_simul = QLabel("<b>SIMULACIÓN</b>")
        self.lbl_simul.setAlignment(Qt.AlignCenter)
        self.sidebar_layout2.addWidget(self.lbl_simul)
        
        self.btn_ejec = self.crear_boton("Ejecutar Trayect", "#2e5883")
        self.btn_ejec.clicked.connect(self.inicializar_simulacion)
        
        self.btn_parar = self.crear_boton("Parar", "#73180e")
        self.btn_parar.clicked.connect(self.parar_simulacion)
        
        layout_nav_grid = QHBoxLayout()

        self.btn_vel_menos = self.crear_boton("<", "#7f8c8d")
        self.btn_vel_menos.clicked.connect(lambda: self.cambiar_vel(-1))
        
        self.lbl_valor_vel = QLabel(f"<b>{varbls.idx_vel+1}</b>")
        self.lbl_valor_vel.setAlignment(Qt.AlignCenter)
        self.lbl_valor_vel.setStyleSheet("font-size: 14px; color: #f1c40f;")
        
        self.btn_vel_mas = self.crear_boton(">", "#7f8c8d")
        self.btn_vel_mas.clicked.connect(lambda: self.cambiar_vel(1))
        
        self.sidebar_layout2.addWidget(self.btn_ejec)
        self.lbl_vel = QLabel("<b>VELOCIDAD</b>")
        self.lbl_vel.setAlignment(Qt.AlignCenter)
        self.sidebar_layout2.addWidget(self.lbl_vel)
        
        etiqueta_seccion = QFont('JetBrains Mono', 10)
        etiqueta_seccion.setBold(True)
        
        layout_nav_grid.addWidget(self.btn_vel_menos)
        layout_nav_grid.addWidget(self.lbl_valor_vel)
        layout_nav_grid.addWidget(self.btn_vel_mas)
        self.sidebar_layout2.addLayout(layout_nav_grid)

        self.sidebar_layout2.addSpacing(20)
        self.sidebar_layout2.addWidget(self.btn_parar)
        
        self.sidebar_layout2.addSpacing(20)
        
        self.sw_codo.stateChanged.connect(self.cambiar_postura_codo)
        self.sidebar_layout2.addStretch()
        
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setRange(0, 100) 
        self.barra_progreso.setValue(0)      
        self.barra_progreso.setTextVisible(True) 
        self.barra_progreso.setAlignment(Qt.AlignCenter)
        
        self.barra_progreso.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #1e1e1e;
                text-align: center;
                color: white;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3498db; /* Color azul igual que tus pestañas */
                border-radius: 4px;
            }
        """)
        
        self.sidebar_layout2.addSpacing(15)
        self.sidebar_layout2.addWidget(self.barra_progreso)
        
        self.view2 = gl.GLViewWidget()
        self.crear_visor(self.view2, self.grid2, 2)

        # --- PESTAÑA: OPCIONES ---
        self.layout_opciones = QVBoxLayout(self.tab_opciones)
        self.layout_opciones.setAlignment(Qt.AlignTop)
        self.layout_opciones.setSpacing(15)
        
        self.layout_opciones.addWidget(QLabel("<b>ESPACIADO DE LA CUADRÍCULA (GRID)</b>"))
        
        layout_nav_grid = QHBoxLayout()

        self.btn_grid_menos = self.crear_boton("<", "#7f8c8d")
        self.btn_grid_menos.clicked.connect(lambda: self.cambiar_espaciado_grid(-1))
        
        self.lbl_valor_grid = QLabel(f"<b>{varbls.espcd[varbls.idx_espacio]} cm</b>")
        self.lbl_valor_grid.setAlignment(Qt.AlignCenter)
        self.lbl_valor_grid.setStyleSheet("font-size: 14px; color: #f1c40f;")
        
        self.btn_grid_mas = self.crear_boton(">", "#7f8c8d")
        self.btn_grid_mas.clicked.connect(lambda: self.cambiar_espaciado_grid(1))
        
        layout_nav_grid.addWidget(self.btn_grid_menos)
        layout_nav_grid.addWidget(self.lbl_valor_grid)
        layout_nav_grid.addWidget(self.btn_grid_mas)
        self.layout_opciones.addLayout(layout_nav_grid)
        
        self.layout_opciones.addSpacing(10)
        
        self.layout_opciones.addWidget(QLabel("<b>TAMÁÑO DE LOS PUNTOS DE CONTROL</b>"))
        
        self.entry_tam_puntos = QLineEdit()
        self.entry_tam_puntos.setMaximumWidth(250)
        self.entry_tam_puntos.setText(str(varbls.tam_puntos))
        self.entry_tam_puntos.setPlaceholderText("Ej: 10")
        
        self.entry_tam_puntos.setStyleSheet("background-color: #3d3d3d; border-radius: 10px; border: 1px solid #555; padding: 5px; color: white;")
        
        self.entry_tam_puntos.editingFinished.connect(self.actualizar_tam_puntos)
        self.layout_opciones.addWidget(self.entry_tam_puntos)

        
    def crear_boton(self, texto, color):
        btn = QPushButton(texto, font=QFont('JetBrains Mono Bold', 11))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"background-color: {color}; border-radius: 5px; padding: 5px;")
        return btn

    def actualizar_robot(self, T1, T2, T3, T4, Rot):
        T23 = np.array([T2[0], T2[1], T3[2]])
        
        ContrPes = np.array([-14, 0, T1[2]])
        ContrPes = np.array([-14, 0, T1[2]]) @ (Rot)
        
        varbls.ContraPeso.setData(pos=np.array([ContrPes]))
        varbls.Art1.setData(pos=np.array([T1]))
        varbls.Art2.setData(pos=np.array([T2]))
        varbls.Art23.setData(pos=np.array([T23]))
        varbls.Art3.setData(pos=np.array([T3]))

        line_vertices = np.vstack([ContrPes, T1, T2, T23, T3, T4])
        varbls.Eslbn.setData(pos=line_vertices)
        
    def crear_visor(self, view, grid, a):
        view.setCameraPosition(distance=150, elevation=35, azimuth=-60)
        view.setBackgroundColor('#232627')
       
        view.addItem(grid)

        pts_x = np.array([[-50, 0, 0], [50, 0, 0]])
        pts_y = np.array([[0, -50, 0], [0, 50, 0]])
        
        ejeX = gl.GLLinePlotItem(pos=pts_x, 
                                      color=(1, 0, 0, 0.4), 
                                      width=2, 
                                      antialias=True)
        
        lbl_x_pos = gl.GLTextItem(pos=(53, -2, 0), 
                                       text="x", 
                                       font=QFont('Bruno Ace', 17),
                                       color=(255, 0, 0, 150))
        
        ejeY = gl.GLLinePlotItem(pos=pts_y, 
                                      color=(0, 1, 0, 0.4), 
                                      width=2, antialias=True)
        
        lbl_y_pos = gl.GLTextItem(pos=(-2, 53, 0), 
                                       text="y", 
                                       font=QFont('Bruno Ace', 13),
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
                font=QFont('Bruno Ace', 7),
                color=(200, 200, 200, 255)
            )
            
            lbl_num_y = gl.GLTextItem(
                pos=(-60, val+desfase,  0), 
                text=str(val), 
                font=QFont('Bruno Ace', 7),
                color=(200, 200, 200, 255) 
            )
            
            view.addItem(lbl_num_x)
            view.addItem(lbl_num_y)
        
        view.addItem(ejeX)
        view.addItem(ejeY)
        view.addItem(lbl_x_pos)
        view.addItem(lbl_y_pos)
        
        if a == 1:
            view.addItem(varbls.puntos_graficos)
            view.addItem(varbls.lineas_guia)
            view.addItem(varbls.Trayectoria_plot)
            
            # Brazo
            
            brazo = 40
            t = np.linspace(0, 2*np.pi, 250)
            x2 = brazo*np.cos(t)
            y2 = brazo*np.sin(t)
            z2 = np.zeros(250)
            xn2 = np.flip(x2)
            yn2 = np.flip(-y2)
            zn2 = z2
            
            x2 = np.flip(np.hstack([xn2, x2]))
            y2 = np.flip(np.hstack([yn2, y2]))
            z2 = np.flip(np.hstack([zn2, z2]))
            
            posiciones = np.vstack([x2,y2,z2]).T
            
            varbls.Area.setData(pos=posiciones, color=(1, 1, 1, 0.4), width=2, antialias=True)
            
            view.addItem(varbls.Area)
            
            self.layout_grafica.addWidget(self.sidebar)
            self.sidebar_layout.addSpacing(15)
            self.sidebar_layout.addWidget(QLabel("<b>VISUALIZACIÓN</b>"))
            
            ruta_switch_on = resolver_ruta("switch.png").replace("\\", "/")
            ruta_switch_off = resolver_ruta("switch2.png").replace("\\", "/")
            
            estilo_switch = f"""
                            QCheckBox {{ 
                                spacing: 12px; 
                                font-size: 11px; 
                                font-weight: bold; 
                                color: #ffffff;
                            }}
                            QCheckBox::indicator {{ 
                                width: 36px; 
                                height: 20px; 
                                border-radius: 10px;
                            }}
                            /* Estado Desactivado: Carga switch2.png */
                            QCheckBox::indicator:unchecked {{ 
                                background-color: #232627; 
                                image: url('{ruta_switch_off}'); 
                                alignment: left;
                            }}
                            /* Estado Activado: Carga switch1.png */
                            QCheckBox::indicator:checked {{ 
                                background-color: #232627; 
                                image: url('{ruta_switch_on}'); 
                                alignment: right;
                            }}
                        """
                        
            self.sw_puntos = QCheckBox("Mostrar Puntos")
            self.sw_puntos.setChecked(True) 
            self.sw_puntos.setStyleSheet(estilo_switch)
            self.sw_puntos.stateChanged.connect(self.actualizar_visor)
            
            self.sw_lineas = QCheckBox("Mostrar Líneas Guía")
            self.sw_lineas.setChecked(True) 
            self.sw_lineas.setStyleSheet(estilo_switch)
            self.sw_lineas.stateChanged.connect(self.actualizar_visor)
            
            self.sidebar_layout.addWidget(self.sw_puntos)
            self.sidebar_layout.addWidget(self.sw_lineas)
            
            self.layout_grafica.addWidget(view)
            
        elif a == 2:
            view.addItem(varbls.tornillo)
            view.addItem(varbls.ContraPeso)
            view.addItem(varbls.Art1)
            view.addItem(varbls.Art2)
            view.addItem(varbls.Art23)
            view.addItem(varbls.Art3)
            view.addItem(varbls.Eslbn)
            view.addItem(varbls.Trayectoria_plot2)
        
            T1, T2, T3, T4, Rot, _ = Jacobiano(varbls.q)
            self.actualizar_robot(T1, T2, T3, T4, Rot)
            
            self.layout_simulacion.addWidget(self.sidebar2)
            self.layout_simulacion.addWidget(view)
    
    def actualizar_visor(self):
        trayectoria_completa = []
        posiciones = np.vstack([varbls.puntos_x, varbls.puntos_y, varbls.puntos_z]).T
            
        if len(varbls.puntos_x) > 0 and self.sw_puntos.isChecked():
             posiciones = np.vstack([varbls.puntos_x, varbls.puntos_y, varbls.puntos_z]).T
             num_pts = len(varbls.puntos_x)
             
             colores = np.zeros((num_pts, 4))
             colores[:] = [0.10196, 0.737255, 0.611765, 1]
             
             if self.widget_edicion.isVisible() and 0 <= varbls.indice_edicion < num_pts:
                 colores[varbls.indice_edicion] = [1, 0, 0, 1]
             
             varbls.puntos_graficos.setData(pos=posiciones, color=colores, size=varbls.tam_puntos, pxMode=True)
 
        else:
            varbls.puntos_graficos.setData(pos=np.empty((0, 3)))
            varbls.lineas_guia.setData(pos=np.empty((0, 3)))
            
        if len(varbls.puntos_x) > 1  and self.sw_lineas.isChecked():
            varbls.lineas_guia.setData(pos=posiciones, color=(0.52157, 0.31765, 0.13725, 0.8), width=5, antialias=True)
        else:
            varbls.lineas_guia.setData(pos=np.empty((0, 3)))
            
        num_puntos = len(varbls.puntos_x)

        if num_puntos >= 4:
            trayectoria_completa = []
            
            for start_idx in range(0, num_puntos - 3, 3):
                P0 = [varbls.puntos_x[start_idx],     varbls.puntos_y[start_idx],     varbls.puntos_z[start_idx]]
                P1 = [varbls.puntos_x[start_idx + 1], varbls.puntos_y[start_idx + 1], varbls.puntos_z[start_idx + 1]]
                P2 = [varbls.puntos_x[start_idx + 2], varbls.puntos_y[start_idx + 2], varbls.puntos_z[start_idx + 2]]
                P3 = [varbls.puntos_x[start_idx + 3], varbls.puntos_y[start_idx + 3], varbls.puntos_z[start_idx + 3]]
                
                trayectoria_tramo = self.calcular_trayectoria(P0, P1, P2, P3)
                trayectoria_completa.append(trayectoria_tramo)
            
            varbls.bezier = np.vstack(trayectoria_completa)
            varbls.Trayectoria_plot.setData(pos=varbls.bezier, color=(0.2039, 0.596, 0.8588, 1), width=5, antialias=True)
            varbls.Trayectoria_plot2.setData(pos=varbls.bezier, color=(0.2039, 0.596, 0.8588, 1), width=5, antialias=True)
        else:
            varbls.bezier = None
            varbls.Trayectoria_plot.setData(pos=np.empty((0, 3)))
            varbls.Trayectoria_plot2.setData(pos=varbls.bezier, color=(0.2039, 0.596, 0.8588, 1), width=5, antialias=True)
            
    def calcular_trayectoria(self, P0, P1, P2, P3):
        
        bdt = 0.02
        S = 1
        
        M = np.array([[-1,  3, -3, 1], 
                      [ 3, -6,  3, 0], 
                      [-3,  3,  0, 0], 
                      [ 1,  0,  0, 0]])
        
        P = np.column_stack((P0, P1, P2, P3))
        
        tiempos = np.arange(0, S + (bdt / 10), bdt)
        xy = np.zeros((3, len(tiempos)))
        
        i = 0
        for t in tiempos:
            tn = t / S
            T = np.array([tn**3, tn**2, tn, 1])
            pts = P @ M @ T
            xy[:, i] = pts
            i += 1
        return xy.T

    def agregar_punto(self):
        try:
            x = float(self.entradas['x'].text())
            y = float(self.entradas['y'].text())
            z = float(self.entradas['z'].text())
            
            self.guardar_historial()
            
            varbls.puntos_x.append(x)
            varbls.puntos_y.append(y)
            varbls.puntos_z.append(z)
            
            self.actualizar_visor()
            
            for entry in self.entradas.values():
                entry.clear()
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingresa coordenadas válidas.")

    def guardar(self):
        self.guardar_historial()
        if not varbls.puntos_x:
            QMessageBox.warning(self, "Aviso", "No hay puntos en la trayectoria para guardar.")
            return

        puntos_control = np.vstack([varbls.puntos_x, varbls.puntos_y, varbls.puntos_z]).T

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
                    curva_bezier=curva_bezier
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
                        
                        if 'curva_bezier' in datos and datos['curva_bezier'].size > 0:
                            varbls.bezier = datos['curva_bezier']
                        else:
                            varbls.bezier = None
                        
                        self.actualizar_visor()
                        QMessageBox.information(self, "Éxito", "Trayectoria cargada de forma exitosa.")
                    else:
                        QMessageBox.warning(self, "Archivo no compatible", "El archivo .npz no contiene una trayectoria válida para el robot.")
                        
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un fallo al leer el archivo binario:\n{str(e)}")
    
    def borrar_punto(self):
        if varbls.puntos_x:
            self.guardar_historial()
            varbls.puntos_x.pop()
            varbls.puntos_y.pop()
            varbls.puntos_z.pop()
            self.actualizar_visor()
        else:
            QMessageBox.information(self, "Aviso", "No hay puntos que borrar.")

    def limpiar_todo(self):
        if varbls.puntos_x:
            self.guardar_historial()
            varbls.puntos_x.clear()
            varbls.puntos_y.clear()
            varbls.puntos_z.clear()
            self.actualizar_visor()
        else:
            QMessageBox.information(self, "Aviso", "No hay puntos que borrar.")
        
    def activar_modo_edicion(self):
        if not varbls.puntos_x:
            QMessageBox.warning(self, "Aviso", "No hay puntos en la trayectoria para modificar.")
            return
        
        self.widget_insercion.hide()
        self.widget_edicion.show()
        
        varbls.indice_edicion = 0
        self.cargar_datos_punto_actual()
        self.actualizar_visor()

    def desactivar_modo_edicion(self):
        self.widget_edicion.hide()
        self.widget_insercion.show()
        
        for entry in self.entradas.values():
            entry.clear()
        self.actualizar_visor()

    def navegar_punto(self, direccion):
        nuevo_indice = varbls.indice_edicion + direccion
        
        if nuevo_indice < 0:
            nuevo_indice = len(varbls.puntos_x) - 1
            
        elif nuevo_indice >= len(varbls.puntos_x):
            nuevo_indice = 0
            
        varbls.indice_edicion = nuevo_indice
        self.cargar_datos_punto_actual()
        self.actualizar_visor()

    def cargar_datos_punto_actual(self):
        idx = varbls.indice_edicion
        self.lbl_indice.setText(f"<b>P{idx}</b>")
        
        self.entradas['x'].setText(str(varbls.puntos_x[idx]))
        self.entradas['y'].setText(str(varbls.puntos_y[idx]))
        self.entradas['z'].setText(str(varbls.puntos_z[idx]))

    def guardar_punto_editado(self):
        try:
            idx = varbls.indice_edicion
            self.guardar_historial()
            varbls.puntos_x[idx] = float(self.entradas['x'].text())
            varbls.puntos_y[idx] = float(self.entradas['y'].text())
            varbls.puntos_z[idx] = float(self.entradas['z'].text())
            
            self.actualizar_visor()
        except ValueError:
            QMessageBox.warning(self, "Error", "Asegúrate de ingresar valores numéricos válidos.")

    def guardar_historial(self):
        estado_actual = (
            varbls.puntos_x.copy(),
            varbls.puntos_y.copy(),
            varbls.puntos_z.copy()
        )
        varbls.historial.append(estado_actual)
        
        if len(varbls.historial) > 20:
            varbls.historial.pop(0)

    def deshacer(self):
        if not varbls.historial:
            return

        ultimo_estado = varbls.historial.pop()
        
        varbls.puntos_x = ultimo_estado[0]
        varbls.puntos_y = ultimo_estado[1]
        varbls.puntos_z = ultimo_estado[2]
        
        if varbls.indice_edicion >= len(varbls.puntos_x):
            varbls.indice_edicion = max(0, len(varbls.puntos_x) - 1)
            if hasattr(self, 'cargar_datos_punto_actual') and varbls.puntos_x:
                self.cargar_datos_punto_actual()

        self.actualizar_visor()

    def cambiar_espaciado_grid(self, direccion):
        nuevo_idx = varbls.idx_espacio + direccion
        
        if nuevo_idx < 0:
            nuevo_idx = len(varbls.espcd) - 1
            
        elif nuevo_idx >= len(varbls.espcd):
            nuevo_idx = 0
        
        varbls.idx_espacio = nuevo_idx
        valor_actual = varbls.espcd[nuevo_idx]
        
        self.lbl_valor_grid.setText(f"<b>{valor_actual} cm</b>")
        
        self.grid.setSpacing(x=valor_actual, y=valor_actual)
            
    def actualizar_tam_puntos(self):
        try:
            nuevo_tam = int(self.entry_tam_puntos.text())
            if nuevo_tam > 0:
                varbls.tam_puntos = nuevo_tam
                self.actualizar_visor() 
            else:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Valor no válido", "Por favor ingresa un número entero positivo para el tamaño del punto.")
            self.entry_tam_puntos.setText(str(varbls.tam_puntos))
    
    def cambiar_vel(self, direccion):
        nuevo_idx = varbls.idx_vel + direccion
        
        if nuevo_idx < 0:
            nuevo_idx = len(varbls.vel) - 1
            
        elif nuevo_idx >= len(varbls.vel):
            nuevo_idx = 0
        
        varbls.idx_vel = nuevo_idx
        
        self.lbl_valor_vel.setText(f"<b>{nuevo_idx+1}</b>")

    def posicionar_robot(self, band=0):
        try:
            if band == 0:
                x = float(self.entradas_sim['x'].text())
                y = float(self.entradas_sim['y'].text())
                z = float(self.entradas_sim['z'].text())
            else:
                _, _, _, T4, _, _ = Jacobiano(varbls.q)
                x = T4[0]
                y = T4[1]
                z = T4[2]
        
            q2, q3 = cinematicaInversa(x, y, varbls.codo_arriba)
            
            if q2 is None:
                QMessageBox.warning(self, "Aviso", "Punto fuera del alcance del Robot.")
                return
            
            q = [z, q2, q3, 0]
            varbls.q = q
            T1, T2, T3, T4, Rot, _ = Jacobiano(q)
            
            self.actualizar_robot(T1, T2, T3, T4, Rot)
        except:
            QMessageBox.warning(self, "Aviso", "Ingresa un punto válido.")

    def cambiar_postura_codo(self, estado):
        varbls.codo_arriba = self.sw_codo.isChecked()
        
        if varbls.codo_arriba:
            self.sw_codo.setText("Pose 2")
        else:
            self.sw_codo.setText("Pose 1")
        
        self.posicionar_robot(1)
    
    def inicializar_simulacion(self):
        
        if varbls.bezier is None or len(varbls.bezier) == 0:
            QMessageBox.warning(self, "Aviso", "No hay una trayectoria calculada para simular.")
            return
        
        self.btn_ejec.setEnabled(False) 
        self.barra_progreso.setValue(0)
        
        I = varbls.bezier.shape[0]
        qx, qy, qz = normlzr_dist(varbls.bezier.T, I)
        self.t = np.linspace(0, self.t_prueba, I)
        self.Spx = obtener_splines(self.t, qx)
        self.Spy = obtener_splines(self.t, qy)
        self.Spz = obtener_splines(self.t, qz)
        
        muestras = 1000
        
        tiempos = np.linspace(self.t[0], self.t[-1], muestras)
 
        x = np.zeros(muestras)
        y = np.zeros(muestras)
        z = np.zeros(muestras)
 
        # Evaluar la trayectoria
        for i, tk in enumerate(tiempos):
            x[i], _ = evaluar_splines_c(self.Spx, self.t, tk)
            y[i], _ = evaluar_splines_c(self.Spy, self.t, tk)
            z[i], _ = evaluar_splines_c(self.Spz, self.t, tk)
 
        # Distancia entre puntos consecutivos
        dx = np.diff(x)
        dy = np.diff(y)
 
        distancias = np.sqrt(dx**2 + dy**2)
 
        # Longitud total de la trayectoria
        L = np.sum(distancias)
 
        # Tiempo total
        self.t_final = L / varbls.vel[varbls.idx_vel]
        
        self.t = np.linspace(0, self.t_final, I)
        self.Spx = obtener_splines(self.t, qx)
        self.Spy = obtener_splines(self.t, qy)
        self.Spz = obtener_splines(self.t, qz)
        
        Ks = np.array([3, 3, 3])
        self.D = np.diag(Ks)
        
        q2, q3 = cinematicaInversa(varbls.bezier[0,0], 
                                   varbls.bezier[0,1], 
                                   varbls.codo_arriba)
        
        if q2 is None:
            self.btn_ejec.setEnabled(True) 
            QMessageBox.warning(self, "Aviso", "Punto fuera del alcance del Robot.")
            return
        
        q = [varbls.bezier[0,2], q2, q3, 0]
        varbls.q = q
        T1, T2, T3, T4, Rot, _ = Jacobiano(q)
        
        self.actualizar_robot(T1, T2, T3, T4, Rot)
        
        QTimer.singleShot(1200, self.pausa)
        
    def pausa(self):
        self.t_inicial = time.time()
        self.timer.start(16)

    def simulacion(self):
        tk = time.time() - self.t_inicial
        
        T1, T2, T3, T4, Rot, J = Jacobiano(varbls.q)
        
        qkx, qpkx = evaluar_splines_c(self.Spx, self.t, tk)
        qky, qpky = evaluar_splines_c(self.Spy, self.t, tk)
        qkz, qpkz = evaluar_splines_c(self.Spz, self.t, tk)
        
        xyd = np.asarray((qkx,qky, qkz))
        xypd = np.asarray((qpkx,qpky, qpkz))
        
        # Control
        Ji = np.linalg.pinv(J[0:3,:])
        
        e = xyd - T4
        qp = Ji @ (xypd + self.D @ (e))
        varbls.q = varbls.q + qp * 0.016666
        self.actualizar_robot(T1,T2,T3,T4,Rot) 
        
        porcentaje = int((tk / self.t_final) * 100)
        porcentaje = max(0, min(100, porcentaje)) 
        self.barra_progreso.setValue(porcentaje)
        
        if tk >= self.t_final:
            self.parar_simulacion(1)
        
    def parar_simulacion(self, bandera=0):
        self.timer.stop() 
        self.btn_ejec.setEnabled(True) 
        if bandera == 1:
            self.barra_progreso.setValue(100) 
        else:
            QMessageBox.information(self, "Aviso", "Simulación detenida")
            
    def alternar_pantalla_completa(self):
        if self.isFullScreen():
            self.showNormal() 
        else:
            self.showFullScreen() 

        
if __name__ == "__main__":
    import ctypes
    if sys.platform == "win32":
        myappid = "hypertera.simuladorscara.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication.instance()
    if app is None: app = QApplication(sys.argv)
    if sys.platform == "darwin":
        nombre_icono = "icon.icns"
    else:
        nombre_icono = "icon.ico"
    app.setWindowIcon(QIcon(resolver_ruta(nombre_icono)))
    ventana = InterfazScara()
    ventana.show()
    sys.exit(app.exec())