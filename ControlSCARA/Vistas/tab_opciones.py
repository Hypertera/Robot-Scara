from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt

class TabOpciones(QWidget):
    def __init__(self, ventana_principal, etiqueta, 
                 etiqueta2, etiqueta3, etiqueta4, etiqueta5,
                 varbls):
        super().__init__()
        self.main = ventana_principal
        
        self.layout_opciones = QVBoxLayout(self)
        self.layout_opciones.setAlignment(Qt.AlignCenter)
        
        lbl_t1 = QLabel("<b>CREACIÓN DE TRAYECTORIAS</b>")
        lbl_t1.setFont(etiqueta3)
        
        lbl_esp = QLabel("<b>·Espaciado de la cuadricula (GRID)</b>")
        lbl_esp.setFont(etiqueta)
        
        lbl_tam = QLabel("<b>·Tamaño de los puntos de control</b>")
        lbl_tam.setFont(etiqueta)
        
        self.layout_opciones.addWidget(lbl_t1)
        self.layout_opciones.setSpacing(15)
        self.layout_opciones.addWidget(lbl_esp)
        
        layout_nav_grid = QHBoxLayout()
        layout_nav_grid.setAlignment(Qt.AlignLeft)

        self.btn_grid_menos = self.main.crear_boton("<", "#455364", "#34495e")
        self.btn_grid_menos.setFont(etiqueta4)
        self.btn_grid_menos.clicked.connect(lambda: self.main.cambiar_espaciado_grid(-1))
        self.btn_grid_menos.setFixedWidth(80)
        
        self.lbl_valor_grid = QLabel(f"<b>{varbls.espcd[varbls.idx_espacio]} cm</b>")
        self.lbl_valor_grid.setFont(etiqueta2)
        self.lbl_valor_grid.setAlignment(Qt.AlignLeft)
        self.lbl_valor_grid.setStyleSheet("font-size: 25px,")
        self.lbl_valor_grid.setFixedWidth(80)
        
        self.btn_grid_mas = self.main.crear_boton(">", "#455364", "#34495e")
        self.btn_grid_mas.setFont(etiqueta4)
        self.btn_grid_mas.clicked.connect(lambda: self.main.cambiar_espaciado_grid(1))
        self.btn_grid_mas.setFixedWidth(80)
        
        layout_nav_grid.addWidget(self.btn_grid_menos, alignment=Qt.AlignRight)
        layout_nav_grid.addWidget(self.lbl_valor_grid)
        layout_nav_grid.addWidget(self.btn_grid_mas, alignment=Qt.AlignLeft)
        self.layout_opciones.addLayout(layout_nav_grid)
        
        self.layout_opciones.addSpacing(10)
        
        self.layout_opciones.addWidget(lbl_tam)
        
        self.entry_tam_puntos = QLineEdit()
        self.entry_tam_puntos.setMaximumWidth(250)
        self.entry_tam_puntos.setText(str(varbls.tam_puntos))
        self.entry_tam_puntos.setPlaceholderText("Ej: 10")
        
        self.entry_tam_puntos.setFont(etiqueta)
        self.entry_tam_puntos.setStyleSheet("font-size: 25px; background-color: #3d3d3d; border-radius: 10px; border: 1px solid #555; padding: 8px; color: white; text-align: center,")
        self.entry_tam_puntos.editingFinished.connect(self.main.actualizar_tam_puntos)
        self.entry_tam_puntos.setAlignment(Qt.AlignCenter)
        self.layout_opciones.addWidget(self.entry_tam_puntos)
        
        lbl_t1 = QLabel("<b>ROBOT</b>")
        lbl_t1.setFont(etiqueta3)
        
        lbl_cal = QLabel("<b>·Calibración de encoders</b>")
        lbl_cal.setFont(etiqueta)
        
        layout_cal = QHBoxLayout()
        layout_cal.setAlignment(Qt.AlignLeft)
        
        self.btn_cargar_cal = self.main.crear_boton("Calibrar", "#2e5883", "#274b70")
        self.btn_cargar_cal.setFixedWidth(200)
        self.btn_cargar_cal.clicked.connect(self.main.calibrar)
        self.btn_cargar_cal.setEnabled(False)
        
        self.btn_guardar_cal = self.main.crear_boton("Cargar", "#2e5883", "#274b70")
        self.btn_guardar_cal.setFixedWidth(200)
        self.btn_guardar_cal.clicked.connect(self.main.cargar_calib)
        self.btn_guardar_cal.setEnabled(False)
        
        layout_cal.addWidget(self.btn_cargar_cal)
        layout_cal.addWidget(self.btn_guardar_cal)
        
        self.layout_opciones.addSpacing(40)
        self.layout_opciones.addWidget(lbl_t1)
        self.layout_opciones.addWidget(lbl_cal)
        self.layout_opciones.addLayout(layout_cal)
        
        lbl_mot = QLabel("<b>·Habilitar/Deshabilitar motores</b>")
        lbl_mot.setFont(etiqueta)
        
        self.btn_habilitar = self.main.crear_boton("habilitar", "#2e5883", "#274b70")
        self.btn_habilitar.setFixedWidth(200)
        self.btn_habilitar.clicked.connect(self.main.activar_desactivar)
        self.btn_habilitar.setEnabled(False)
        
        self.layout_opciones.addWidget(lbl_mot)
        self.layout_opciones.addWidget(self.btn_habilitar)