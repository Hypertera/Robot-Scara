from PySide6.QtWidgets import (QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, 
                               QStackedWidget, QCheckBox, 
                               QProgressBar, QLineEdit,
                               QSlider)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon

class TabControles(QWidget):
    def __init__(self, ventana_principal, etiqueta, 
                 etiqueta2, etiqueta4, etiqueta5, sw_lbl):
        
        super().__init__()
        self.main = ventana_principal
        self.etiqueta = etiqueta
        self.etiqueta2 = etiqueta2
        self.sw_lbl = sw_lbl
        self.etiqueta4 = etiqueta4
        self.vel = [1, 2, 4, 6, 8, 10]
        
        layout_horizontal = QHBoxLayout(self)
        layout_horizontal.setContentsMargins(10, 10, 10, 10)
        
        self.sidebar = QWidget()
        self.sidebar.setMaximumWidth(280)
        self.sidebar.setStyleSheet("background-color: #232627; border-radius: 10px;")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setAlignment(Qt.AlignTop)
        
        self.widget_conexion = QWidget()
        layout_con = QVBoxLayout(self.widget_conexion)
        layout_con.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_estado_robot = QLabel("<b>ROBOT DESCONECTADO</b>")
        self.lbl_estado_robot.setAlignment(Qt.AlignCenter)
        self.lbl_estado_robot.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold;")
        
        self.btn_conectar = self.main.crear_boton("Conectar", "#2e5883", "#274b70")
        self.btn_conectar.clicked.connect(self.main.conectar_robot_real)
        
        layout_con.addWidget(self.lbl_estado_robot)
        self.btn_conectar.setFixedWidth(180)
        self.btn_conectar.setFixedHeight(36)
        layout_con.addWidget(self.btn_conectar, alignment=Qt.AlignHCenter)
        
        self.sidebar_layout.addWidget(self.widget_conexion)
        
        self.sidebar_layout.addSpacing(60)
        
        self.layout_nav = QHBoxLayout()
        self.btn_prev = self.main.crear_boton("<", "#232627", "#232627")
        self.btn_prev.setFont(etiqueta5)
        self.btn_prev.setStyleSheet("background-color: #232627; border:2px solid #212424,")
        self.btn_prev.clicked.connect(self.alternar_modo_barra)
        
        self.lbl_seg = QLabel("<b>CONTROL MANUAL</b>")
        self.lbl_seg.setFont(self.etiqueta)
        self.lbl_seg.setAlignment(Qt.AlignCenter)
        
        self.btn_next = self.main.crear_boton(">", "#232627", "#232627")
        self.btn_next.setFont(etiqueta5)
        self.btn_next.setStyleSheet("background-color: #232627; border:2px solid #212424,")
        self.btn_next.clicked.connect(self.alternar_modo_barra)
        
        self.layout_nav.addWidget(self.btn_prev, alignment=Qt.AlignLeft)
        self.layout_nav.addWidget(self.lbl_seg, alignment=Qt.AlignHCenter)
        self.layout_nav.addWidget(self.btn_next, alignment=Qt.AlignRight)
        
        self.sidebar_layout.addLayout(self.layout_nav)
        
        self.stacked_controles = QStackedWidget()
        
        self.pantalla_jogging = self.crear_subpantalla_manual()
        self.pantalla_jogging.setEnabled(False)
        self.pantalla_trayectoria = self.crear_subpantalla_trayectoria()
        
        self.stacked_controles.addWidget(self.pantalla_jogging)     
        self.stacked_controles.addWidget(self.pantalla_trayectoria) 
        
        self.sidebar_layout.addWidget(self.stacked_controles)
        layout_horizontal.addWidget(self.sidebar)
        
        layout_horizontal.addWidget(self.main.view2)
        
        self.main.timerRobot = QTimer()
        self.main.timerRobot.timeout.connect(self.main.bucle_princpl)
        
    def crear_subpantalla_manual(self):
        
        vista = QWidget()
        layout = QVBoxLayout(vista)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout_x = QHBoxLayout()
        layout_y = QHBoxLayout()
        layout_z = QHBoxLayout()
        band =0
        
        layout.addSpacing(40)
        
        lbl_pos = QLabel("<b>POSICIONAR ROBOT</b>")
        lbl_pos.setFont(self.etiqueta)
        lbl_pos.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_pos)
        
        layout.addSpacing(10)
        
        self.entradas_sim = {}
        for eje in ['X', 'Y', 'Z']:
            lbl_sim = QLabel(f"{eje}:")
            lbl_sim.setFont(self.etiqueta)
            
            entry_sim = QLineEdit()
            entry_sim.setPlaceholderText("cm")
            entry_sim.setFont(self.etiqueta2)
            entry_sim.setStyleSheet("""
                QLineEdit {
                    background-color: #3d3d3d; 
                    border: 2px solid #555; 
                    border-radius: 8px;
                    padding: 5px;
                    color: #ffffff;
                }
                QLineEdit::placeholder {
                    color: #888888;
                    font-style: italic;
                }
            """)
            
            if band == 0:
                layout_x.addWidget(lbl_sim)
                layout_x.addWidget(entry_sim)
            elif band == 1:
                layout_y.addWidget(lbl_sim)
                layout_y.addWidget(entry_sim)
            elif band == 2:
                layout_z.addWidget(lbl_sim)
                layout_z.addWidget(entry_sim)
            
            self.entradas_sim[eje.lower()] = entry_sim
            
            band += 1
        
        layout.addLayout(layout_x)
        layout.addLayout(layout_y)
        layout.addLayout(layout_z)
        
        lista_entries_sim = [
            self.entradas_sim['x'], 
            self.entradas_sim['y'], 
            self.entradas_sim['z']
        ]
        lista_entries_sim[0].returnPressed.connect(lambda: lista_entries_sim[1].setFocus())
        
        lista_entries_sim[1].returnPressed.connect(lambda: lista_entries_sim[2].setFocus())
        
        lista_entries_sim[2].returnPressed.connect(self.main.posicionar_robot)
        
        layout.addSpacing(10)
        
        layout_colocar = QHBoxLayout()
        
        self.btn_pos = self.main.crear_boton("Colocar", "#2e5883", "#274b70")
        self.btn_pos.clicked.connect(self.main.posicionar_robot)
        layout_colocar.addWidget(self.btn_pos)
        self.btn_pos.setFixedWidth(180)
        self.btn_pos.setFixedHeight(36)
        
        self.btn_casa = self.main.crear_boton("", "#2e5883", "#274b70")
        self.btn_casa.clicked.connect(self.main.pose_casa)
        layout_colocar.addWidget(self.btn_casa)
        self.btn_casa.setFixedWidth(70)
        self.btn_casa.setFixedHeight(36)
        self.btn_casa.setIcon(QIcon(self.main.ruta_casa))
        self.btn_casa.setIconSize(QSize(30, 30))
        
        layout.addLayout(layout_colocar)
        
        self.sw_codo = QCheckBox("Pose 1")
        self.sw_codo.setFont(self.sw_lbl)
        self.sw_codo.setCursor(Qt.PointingHandCursor)
       
        self.sw_codo.setStyleSheet(f"""
            QCheckBox {{ spacing: 12px; font-size: 15px; font-weight: bold; color: #ffffff; }}
            QCheckBox::indicator {{ width: 42px; height: 26px; border-radius: 10px; }}
            QCheckBox::indicator:unchecked {{ background-color: #232627; image: url('{self.main.ruta_switch_off}'); alignment: left; }}
            QCheckBox::indicator:checked {{ background-color: #232627; image: url('{self.main.ruta_switch_on}'); alignment: right; }}
        """)
        
        self.sw_codo.stateChanged.connect(self.main.cambiar_postura_codo)
        layout.addWidget(self.sw_codo, alignment=Qt.AlignHCenter)
        self.sw_codo_root = self.sw_codo 
        layout.addSpacing(20)
        
        lbl_art = QLabel("<b>ARTICULACIONES</b>")
        lbl_art.setFont(self.etiqueta)
        lbl_art.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_art)
        
        layout.addSpacing(5)
        
        self.botones_jog = {}
        for art in ['A1', 'A2', 'A3']:
            layout_art = QHBoxLayout()
                
            btn_menos = self.main.crear_boton("", "#455364", "#34495e")
            btn_menos.pressed.connect(lambda checked=False, a=art: self.main.mover_art(a, -1))
            btn_menos.released.connect(self.main.detnr_art)
            
            lbl_nombre = QLabel(f"<b>{art}</b>")
            lbl_nombre.setAlignment(Qt.AlignCenter)
            lbl_nombre.setFont(self.etiqueta)
            lbl_nombre.setStyleSheet("font-size: 20px; min-width: 40px;")
            
            btn_mas = self.main.crear_boton("", "#455364", "#34495e")
            if art == "A1":
                btn_menos.setIcon(QIcon(self.main.ruta_abajo))
                btn_menos.setIconSize(QSize(16, 16))
                
                btn_mas.setIcon(QIcon(self.main.ruta_arriba))
                btn_mas.setIconSize(QSize(16, 16))
            else:
                btn_menos.setIcon(QIcon(self.main.ruta_izq))
                btn_menos.setIconSize(QSize(16, 16))
                
                btn_mas.setIcon(QIcon(self.main.ruta_der))
                btn_mas.setIconSize(QSize(16, 16))
                
            btn_menos.setFixedHeight(45)
            btn_mas.setFixedHeight(45)
            
            btn_mas.pressed.connect(lambda checked=False, a=art: self.main.mover_art(a, 1))
            btn_mas.released.connect(self.main.detnr_art)
            
            layout_art.addWidget(btn_menos)
            layout_art.addWidget(lbl_nombre)
            layout_art.addWidget(btn_mas)
            layout.addLayout(layout_art)
            
            self.botones_jog[art] = (btn_menos, btn_mas)
        
        layout.addSpacing(15)
        
        layout_vel = QHBoxLayout()
        lbl_vel = QLabel("<b>Velocidad XY:</b>")
        lbl_vel.setFont(self.etiqueta)
        lbl_vel.setStyleSheet("font-size: 17px; color: #ffffff;")
        
        self.lbl_val_vel = QLabel("<b>50%</b>")
        self.lbl_val_vel.setFont(self.etiqueta)
        self.lbl_val_vel.setStyleSheet("font-size: 17px; color: #ffffff; font-weight: bold;")
        self.lbl_val_vel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout_vel.addWidget(lbl_vel)
        layout_vel.addWidget(self.lbl_val_vel)
        layout.addLayout(layout_vel)
        
        self.slider_vel = QSlider(Qt.Horizontal)
        
        self.slider_vel.setMinimum(10)
        self.slider_vel.setMaximum(100)
        self.slider_vel.setValue(50)
        self.slider_vel.setSingleStep(5)
        
        self.slider_vel.valueChanged.connect(self.main.actlzr_vel_xy)
        
        layout.addWidget(self.slider_vel)
        
        layout.addSpacing(15)
        
        layout_vel_z = QHBoxLayout()
        lbl_vel = QLabel("<b>Velocidad Z:</b>")
        lbl_vel.setFont(self.etiqueta)
        lbl_vel.setStyleSheet("font-size: 17px; color: #ffffff;")
        
        self.lbl_val_vel_z = QLabel("<b>75%</b>")
        self.lbl_val_vel_z.setFont(self.etiqueta)
        self.lbl_val_vel_z.setStyleSheet("font-size: 17px; color: #ffffff; font-weight: bold;")
        self.lbl_val_vel_z.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout_vel_z.addWidget(lbl_vel)
        layout_vel_z.addWidget(self.lbl_val_vel_z)
        layout.addLayout(layout_vel_z)
        
        self.slider_vel_z = QSlider(Qt.Horizontal)
        
        self.slider_vel_z.setMinimum(10)
        self.slider_vel_z.setMaximum(100)
        self.slider_vel_z.setValue(75)
        self.slider_vel_z.setSingleStep(5)
        
        self.slider_vel_z.valueChanged.connect(self.main.actlzr_vel_z)
        
        layout.addWidget(self.slider_vel_z)
        
        layout.addStretch()
        return vista

    def crear_subpantalla_trayectoria(self):
        vista = QWidget()
        layout = QVBoxLayout(vista)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addSpacing(40)
        
        lbl_vel = QLabel("<b>VELOCIDAD XY</b>")
        lbl_vel.setFont(self.etiqueta)
        lbl_vel.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_vel)
        
        layout_nav_grid = QHBoxLayout()
        
        self.btn_vel_menos = self.main.crear_boton("<", "#455364", "#34495e")
        self.btn_vel_menos.setFont(self.etiqueta4)
        self.btn_vel_menos.clicked.connect(lambda: self.main.cambiar_vel(-1))
        idx = self.main.idx_vel
        self.lbl_valor_vel = QLabel(f"<b>{self.vel[idx]} cm/s</b>")
        self.lbl_valor_vel.setAlignment(Qt.AlignCenter)
        self.lbl_valor_vel.setFont(self.etiqueta)
        self.lbl_valor_vel.setStyleSheet("font-size: 20px;")
        
        self.btn_vel_mas = self.main.crear_boton(">", "#455364", "#34495e")
        self.btn_vel_mas.setFont(self.etiqueta4)
        self.btn_vel_mas.clicked.connect(lambda: self.main.cambiar_vel(1))
        
        layout_nav_grid.addWidget(self.btn_vel_menos)
        layout_nav_grid.addWidget(self.lbl_valor_vel)
        layout_nav_grid.addWidget(self.btn_vel_mas)
        layout.addLayout(layout_nav_grid)
        
        layout.addSpacing(5)
        
        lbl_gain = QLabel("<b>GANANCIAS<br>DEL CONTROLADOR")
        lbl_gain.setFont(self.etiqueta)
        lbl_gain.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_gain)
        
        
        self.labels_ganancias = {}
        
        ganancias = ['Kx', 'Ky']
        
        for g in ganancias:
            layout_g = QHBoxLayout()
            layout_g.setAlignment(Qt.AlignCenter)
            
            lbl_nombre = QLabel(f"<b>{g}:</b>")
            lbl_nombre.setFont(self.etiqueta)
            lbl_nombre.setStyleSheet("font-size: 20px; color: #ffffff,")
            
            btn_menos = self.main.crear_boton("-", "#73180e", "#931c10")
            btn_menos.setFixedWidth(50)
            btn_menos.setFont(self.etiqueta4)
            btn_menos.clicked.connect(lambda checked=False, var=g: self.main.cambiar_ganancia(var, -0.2))
            
            btn_menos.setAutoRepeat(True)       
            btn_menos.setAutoRepeatDelay(400) 
            btn_menos.setAutoRepeatInterval(70)
            
            valor_inicial = self.main.obtener_texto_ganancia(g)
            lbl_valor = QLabel(f"<b>{valor_inicial}</b>")
            lbl_valor.setAlignment(Qt.AlignCenter)
            lbl_valor.setFont(self.etiqueta)
            lbl_valor.setStyleSheet("font-size: 20px; color: #f1c40f,")
            lbl_valor.setFixedWidth(50)
            
            btn_mas = self.main.crear_boton("+", "#2e5883", "#274b70")
            btn_mas.setFixedWidth(50)
            btn_mas.setFont(self.etiqueta4)
            btn_mas.clicked.connect(lambda checked=False, var=g: self.main.cambiar_ganancia(var, 0.2))
            
            btn_mas.setAutoRepeat(True)       
            btn_mas.setAutoRepeatDelay(400) 
            btn_mas.setAutoRepeatInterval(70)
            
            layout_g.addWidget(lbl_nombre)
            layout_g.addWidget(btn_menos)
            layout_g.addWidget(lbl_valor)
            layout_g.addWidget(btn_mas)
            
            layout.addLayout(layout_g)
            
            self.labels_ganancias[g.lower()] = lbl_valor
        
        layout.addSpacing(10)
        
        self.sw_codo2 = QCheckBox("Pose 1")
        self.sw_codo2.setFont(self.sw_lbl)
        self.sw_codo2.setCursor(Qt.PointingHandCursor)
       
        self.sw_codo2.setStyleSheet(f"""
            QCheckBox {{ spacing: 12px; font-size: 15px; font-weight: bold; color: #ffffff; }}
            QCheckBox::indicator {{ width: 42px; height: 26px; border-radius: 10px; }}
            QCheckBox::indicator:unchecked {{ background-color: #232627; image: url('{self.main.ruta_switch_off}'); alignment: left; }}
            QCheckBox::indicator:checked {{ background-color: #232627; image: url('{self.main.ruta_switch_on}'); alignment: right; }}
        """)
        
        self.sw_codo2.stateChanged.connect(self.main.cambiar_postura_codo)
        
        lbl_seg = QLabel("<b>EJECUCIÓN</b>")
        lbl_seg.setFont(self.etiqueta)
        lbl_seg.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_seg)
        
        self.btn_ejec = self.main.crear_boton("▶ Simulación", "#2e5883", "#274b70")
        self.btn_ejec.clicked.connect(self.main.ini_seguimiento)
        layout.addWidget(self.btn_ejec)

        self.btn_SCARA = self.main.crear_boton("▶ Robot SCARA", "#2e5883", "#274b70")
        self.btn_SCARA.clicked.connect(self.main.ini_seguimiento_SCARA)
        self.btn_SCARA.setEnabled(False)
        layout.addWidget(self.btn_SCARA)
        
        layout.addWidget(self.sw_codo2, alignment=Qt.AlignHCenter)
        self.sw_codo_root2 = self.sw_codo2 
        
        self.btn_parar = self.main.crear_boton("Parar Ejecución", "#73180e", "#931c10")
        self.btn_parar.clicked.connect(self.main.parar)
        
        layout.addStretch()
        layout.addWidget(self.btn_parar)
        self.btn_parar.setEnabled(False)
        
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
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        
        layout.addWidget(self.barra_progreso)
        
        return vista

    def alternar_modo_barra(self):
        """ Cambia entre la pantalla de Jogging (0) y la de Trayectoria (1) """
        if self.stacked_controles.currentIndex() == 0:
            self.stacked_controles.setCurrentIndex(1) 
            self.lbl_seg.setText("<b>SEGUIMIENTO</b>")
        else:
            self.stacked_controles.setCurrentIndex(0) 
            self.lbl_seg.setText("<b>CONTROL MANUAL</b>")