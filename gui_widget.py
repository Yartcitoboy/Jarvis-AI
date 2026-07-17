import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient

class JarvisWidget(QWidget):
    # Señal para avisar al controlador principal que queremos interactuar
    request_listen = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.state = "IDLE" # Estados posibles: IDLE, LISTENING, THINKING, SPEAKING
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 1
        
        self.initUI()
        
        # Timer para animar a 30 FPS aproximadamente
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)
        
        self.oldPos = self.pos()

    def initUI(self):
        # Ventana sin bordes y siempre por encima de las demás
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(250, 250)
        self.center_window()
        
    def center_window(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_animation(self):
        self.angle = (self.angle + 5) % 360
        self.pulse += 2 * self.pulse_dir
        if self.pulse > 50:
            self.pulse_dir = -1
        elif self.pulse < 0:
            self.pulse_dir = 1
            
        self.update() # Forzar repintado de la interfaz
        
    def set_state(self, new_state):
        self.state = new_state
        if self.state == "SLEEP":
            self.timer.setInterval(200) # 5 FPS (Bajo consumo de CPU)
        else:
            self.timer.setInterval(30) # ~33 FPS (Fluido)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Colores dinámicos según el estado
        if self.state == "SLEEP":
            color = QColor(100, 100, 100, 80) # Gris oscuro
            ring_speed = 0.2
        elif self.state == "IDLE":
            color = QColor(0, 150, 255, 150 + self.pulse) # Azul vibrante
            ring_speed = 1
        elif self.state == "LISTENING":
            color = QColor(0, 255, 100, 200) # Verde
            ring_speed = 3
        elif self.state == "THINKING":
            color = QColor(255, 150, 0, 200) # Naranja/Dorado
            ring_speed = 8
        elif self.state == "SPEAKING":
            color = QColor(0, 255, 255, 200) # Cyan brillante
            ring_speed = 5
        else:
            color = QColor(255, 255, 255, 100)
            ring_speed = 1
            
        # Dibujar gradiente central (El 'núcleo' de energía)
        pulse_effect = self.pulse / 2 if self.state == "SPEAKING" else 0
        gradient = QRadialGradient(center_x, center_y, 50 + pulse_effect)
        gradient.setColorAt(0, color)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - 70), int(center_y - 70), 140, 140)
        
        # Dibujar anillos futuristas giratorios
        pen = QPen(color, 4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        painter.translate(center_x, center_y)
        
        # Anillo exterior
        painter.rotate(self.angle * ring_speed)
        painter.drawArc(-90, -90, 180, 180, 0, 16 * 120)
        painter.drawArc(-90, -90, 180, 180, 16 * 180, 16 * 120)
        painter.rotate(-self.angle * ring_speed)
        
        # Anillo interior girando en sentido contrario
        painter.rotate(-self.angle * ring_speed * 1.5)
        painter.drawArc(-75, -75, 150, 150, 16 * 90, 16 * 200)
        
    def mousePressEvent(self, event):
        # Click izquierdo para arrastrar
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
        # Click derecho para activar la escucha
        elif event.button() == Qt.RightButton:
            if self.state == "IDLE":
                self.request_listen.emit()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
