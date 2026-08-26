import sys
import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from CinematicaScara import Cinematica

class Grafica(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.view = gl.GLViewWidget()
        layout.addWidget(self.view)
        self.view.setCameraPosition(distance=18, elevation=30, azimuth=45)
        self.view.addItem(gl.GLGridItem())  # Rejilla base opcional

        self.Base = gl.GLScatterPlotItem(color=(1, 1, 1, 1.0), size=0.3, pxMode=False)
        self.Art1 = gl.GLScatterPlotItem(color=(1.0, 1.0, 1.0, 1.0), size=0.3, pxMode=False)
        self.Art2 = gl.GLScatterPlotItem(color=(1.0, 1.0, 1.0, 1.0), size=0.3, pxMode=False)
        self.Art3 = gl.GLScatterPlotItem(color=(1.0, 1.0, 1.0, 1.0), size=0.3, pxMode=False)
        self.Art4 = gl.GLScatterPlotItem(color=(1.0, 1.0, 1.0, 1.0), size=0.3, pxMode=False)

        self.Eslbn = gl.GLLinePlotItem(color=(1, 1, 1, 1), width=10, antialias=True)
        
        self.x4 = gl.GLLinePlotItem(color=(1.0, 0.0, 0.0, 1), width=5, antialias=True)
        self.y4 = gl.GLLinePlotItem(color=(0.0, 1.0, 0.0, 1), width=5, antialias=True)
        self.z4 = gl.GLLinePlotItem(color=(0.0, 0.0, 1.0, 1), width=5, antialias=True)

        self.view.addItem(self.Base)
        self.view.addItem(self.Art1)
        self.view.addItem(self.Art2)
        self.view.addItem(self.Art3)
        self.view.addItem(self.Art4)
        self.view.addItem(self.Eslbn)
        
        self.view.addItem(self.x4)
        self.view.addItem(self.y4)
        self.view.addItem(self.z4)

        self.angle = 0.0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(16) 

    def update_scene(self):
        """Calcula las trayectorias espaciales y actualiza los vértices directamente."""
        self.angle += 0.01
        
        Cero = np.array([
            0,
            0,
            0
        ])
        
        q = [2*abs(np.cos(self.angle))+0.2, 1.5*np.sin(self.angle/2), 
             2.5*np.sin(self.angle*1.5), self.angle*3]
        
        T1, T2, T3, T4, Rot, Rot2, Rot3 = Cinematica(q)
        
        # Marco Base
        xb = np.array([0.8, 0, 0])
        
        yb = np.array([0, 0.8, 0])
        
        zb = np.array([0, 0, 0.8])
        
        # Marco 4
        xb_rot =  Rot3 @ xb
        x4f = T4 + xb_rot
        
        yb_rot =  Rot3 @ yb
        y4f = T4 + yb_rot
        
        zb_rot =  Rot3 @ zb
        z4f = T4 + zb_rot
        
        self.Base.setData(pos=np.array([Cero]))
        self.Art1.setData(pos=np.array([T1]))
        self.Art2.setData(pos=np.array([T2]))
        self.Art3.setData(pos=np.array([T3]))
        self.Art4.setData(pos=np.array([T4]))

        line_vertices = np.vstack([Cero, T1, T2, T3, T4])
        self.Eslbn.setData(pos=line_vertices)
        
        # Marco 4
        line_vertices = np.vstack([T4, x4f])
        self.x4.setData(pos=line_vertices)
        line_vertices = np.vstack([T4, y4f])
        self.y4.setData(pos=line_vertices)
        line_vertices = np.vstack([T4, z4f])
        self.z4.setData(pos=line_vertices)
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Animación Scara")
        self.resize(1024, 768)

        self.gl_scene = Grafica()
        self.setCentralWidget(self.gl_scene)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
