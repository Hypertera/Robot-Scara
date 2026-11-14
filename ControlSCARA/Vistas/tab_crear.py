from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QFrame
from PySide6.QtCore import Qt

class TabCrear(QWidget):
    def __init__(self, ventana_principal, etiqueta, 
                 etiqueta2, etiqueta4, sw_lbl):
        super().__init__()
        self.main = ventana_principal
        
        self.layout_grafica = QHBoxLayout(self)
        self.layout_grafica.setContentsMargins(10, 10, 10, 10)
        
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet("background-color: #232627; border-radius: 10px;")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        
        lbl = QLabel("CREAR TRAYECTORIA")
        lbl.setFont(etiqueta)
        lbl.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(lbl)
        
        self.sidebar_layout.addSpacing(20)
        
        layout_x = QHBoxLayout()
        layout_y = QHBoxLayout()
        layout_z = QHBoxLayout()
        band = 0
        
        self.entradas = {}
        lista_entries = []
        
        for eje in ['X', 'Y', 'Z']:
            lbl_eje = QLabel(f"{eje}:")
            lbl_eje.setFont(etiqueta)
            
            entry = QLineEdit()
            entry.setPlaceholderText("cm") 
            entry.setFont(etiqueta2)
            entry.setStyleSheet("""
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
                layout_x.addWidget(lbl_eje)
                layout_x.addWidget(entry)
            elif band == 1:
                layout_y.addWidget(lbl_eje)
                layout_y.addWidget(entry)
            elif band == 2:
                layout_z.addWidget(lbl_eje)
                layout_z.addWidget(entry)
            
            self.entradas[eje.lower()] = entry
            lista_entries.append(entry)
            band += 1
        
        self.sidebar_layout.addLayout(layout_x)
        self.sidebar_layout.addLayout(layout_y)
        self.sidebar_layout.addLayout(layout_z)
        
        lista_entries[0].returnPressed.connect(lambda: lista_entries[1].setFocus())
        lista_entries[1].returnPressed.connect(lambda: lista_entries[2].setFocus())
        
        def al_terminar_z():
            if self.widget_edicion.isVisible():
                self.main.guardar_punto_editado()
                lista_entries[0].setFocus()
            else:
                self.main.agregar_punto()  
                lista_entries[0].setFocus() 
                
        lista_entries[2].returnPressed.connect(al_terminar_z)
        
        self.widget_insercion = QWidget()
        layout_ins = QVBoxLayout(self.widget_insercion)
        layout_ins.setContentsMargins(0, 0, 0, 0)
        
        estilo_switch = f"""
            QCheckBox {{ spacing: 12px; font-size: 15px; font-weight: bold; color: #ffffff; }}
            QCheckBox::indicator {{ width: 42px; height: 26px; border-radius: 10px; }}
            QCheckBox::indicator:unchecked {{ background-color: #232627; image: url('{self.main.ruta_switch_off}'); alignment: left; }}
            QCheckBox::indicator:checked {{ background-color: #232627; image: url('{self.main.ruta_switch_on}'); alignment: right; }}
        """
        
        self.sw_insertar_inicio = QCheckBox("Añadir Reversa")
        self.sw_insertar_inicio.setFont(sw_lbl)
        self.sw_insertar_inicio.setChecked(False) 
        self.sw_insertar_inicio.setStyleSheet(estilo_switch)
        self.sw_insertar_inicio.stateChanged.connect(self.main.gestionar_cambio_modo_insercion)
        
        self.sidebar_layout.addWidget(self.sw_insertar_inicio)
        
        self.btn_añadir = self.main.crear_boton("Añadir Punto", "#2e5883", "#274b70")
        self.btn_añadir.clicked.connect(self.main.agregar_punto)
        
        self.btn_ir_modificar = self.main.crear_boton("Modificar Trayect", "#2e5883", "#274b70")
        self.btn_ir_modificar.clicked.connect(self.main.activar_modo_edicion)
        
        self.btn_borrar = self.main.crear_boton("Borrar Último", "#73180e", "#931c10")
        self.btn_borrar.clicked.connect(self.main.borrar_punto)
        self.btn_borrar.setShortcut("Backspace")

        self.btn_limpiar = self.main.crear_boton("Limpiar Todo", "#73180e", "#931c10")
        self.btn_limpiar.clicked.connect(self.main.limpiar_todo)
        self.btn_limpiar.setShortcut(self.main.atajo_limpiar)
        
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
        self.btn_prev = self.main.crear_boton("<", "#455364", "#34495e")
        self.btn_prev.setFont(etiqueta4)
        self.btn_prev.clicked.connect(lambda: self.main.navegar_punto(-1))
        
        self.btn_prev.setAutoRepeat(True)       
        self.btn_prev.setAutoRepeatDelay(400) 
        self.btn_prev.setAutoRepeatInterval(60)
        
        self.lbl_indice = QLabel("<b>P0</b>")
        self.lbl_indice.setAlignment(Qt.AlignCenter)
        self.lbl_indice.setFont(etiqueta)
        self.lbl_indice.setStyleSheet("font-size: 20px;")
        
        self.btn_next = self.main.crear_boton(">", "#455364", "#34495e")
        self.btn_next.setFont(etiqueta4)
        self.btn_next.clicked.connect(lambda: self.main.navegar_punto(1))
        
        self.btn_next.setAutoRepeat(True)       
        self.btn_next.setAutoRepeatDelay(400) 
        self.btn_next.setAutoRepeatInterval(60)
        
        layout_nav.addWidget(self.btn_prev)
        layout_nav.addWidget(self.lbl_indice)
        layout_nav.addWidget(self.btn_next)
        layout_edi.addLayout(layout_nav)

        self.btn_aplicar_cambio = self.main.crear_boton("Modificar Punto", "#2e5883", "#274b70")
        self.btn_aplicar_cambio.clicked.connect(self.main.guardar_punto_editado)
        
        self.btn_cancelar_edi = self.main.crear_boton("Regresar", "#73180e", "#931c10")
        self.btn_cancelar_edi.clicked.connect(self.main.desactivar_modo_edicion)

        layout_edi.addSpacing(10)
        layout_edi.addWidget(self.btn_aplicar_cambio)
        layout_edi.addWidget(self.btn_cancelar_edi)
        
        self.sidebar_layout.addWidget(self.widget_edicion)
        self.widget_edicion.hide()

        self.sidebar_layout.addStretch()
        self.sidebar_layout.addSpacing(15)
        
        lbl_vis = QLabel("<b>VISUALIZACIÓN</b>")
        lbl_vis.setFont(etiqueta)
        self.sidebar_layout.addWidget(lbl_vis)
        
        estilo_switch = f"""
            QCheckBox {{ spacing: 12px; font-size: 15px; font-weight: bold; color: #ffffff; }}
            QCheckBox::indicator {{ width: 42px; height: 26px; border-radius: 10px; }}
            QCheckBox::indicator:unchecked {{ background-color: #232627; image: url('{self.main.ruta_switch_off}'); alignment: left; }}
            QCheckBox::indicator:checked {{ background-color: #232627; image: url('{self.main.ruta_switch_on}'); alignment: right; }}
        """
        
        self.sw_puntos = QCheckBox("Mostrar Puntos")
        self.sw_puntos.setFont(sw_lbl)
        self.sw_puntos.setChecked(True) 
        self.sw_puntos.setStyleSheet(estilo_switch)
        self.sw_puntos.setCursor(Qt.PointingHandCursor)
        self.sw_puntos.stateChanged.connect(self.main.actualizar_visor_puntos)
        
        self.sw_lineas = QCheckBox("Mostrar Líneas Guía")
        self.sw_lineas.setFont(sw_lbl)
        self.sw_lineas.setChecked(True) 
        self.sw_lineas.setStyleSheet(estilo_switch)
        self.sw_lineas.setCursor(Qt.PointingHandCursor)
        self.sw_lineas.stateChanged.connect(self.main.actualizar_visor_puntos)
        
        self.sidebar_layout.addWidget(self.sw_puntos)
        self.sidebar_layout.addWidget(self.sw_lineas)
        
        self.layout_grafica.addWidget(self.sidebar)
        
        self.layout_grafica.addWidget(self.main.view)