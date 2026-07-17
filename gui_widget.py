import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGraphicsColorizeEffect
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient, QMovie, QRegion

class JarvisWidget(QWidget):
    # Señal para avisar al controlador principal que queremos interactuar
    request_listen = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.state = "IDLE" # Estados posibles: IDLE, LISTENING, THINKING, SPEAKING
        self.angle = 0
        self.initUI()
        
    def initUI(self):
        # Configurar la ventana para ser transparente, sin bordes y siempre arriba
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(300, 300)
        self.center_window()
        
        # Aplicar una máscara circular perfecta para ocultar los bordes negros del GIF si los tiene
        region = QRegion(QRect(0, 0, 300, 300), QRegion.Ellipse)
        self.setMask(region)
        
        self.state = "IDLE"
        
        # Contenedor del GIF
        self.gif_label = QLabel(self)
        self.gif_label.setGeometry(0, 0, 300, 300)
        self.gif_label.setAlignment(Qt.AlignCenter)
        
        # Cargar el GIF animado
        self.movie = QMovie("9c046e14e6ca7754d21dcd5c0deceea6.gif")
        self.movie.setScaledSize(self.size())
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        
        # Efecto de colorización para cambiar el tono según el estado
        self.color_effect = QGraphicsColorizeEffect(self)
        self.gif_label.setGraphicsEffect(self.color_effect)
        
        self.oldPos = self.pos()
        self.set_state("IDLE")

    def center_window(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def set_state(self, new_state):
        self.state = new_state
        
        # SLEEP: Gris oscuro, animación muy lenta
        if self.state == "SLEEP":
            self.color_effect.setColor(QColor(100, 100, 100))
            self.color_effect.setStrength(1.0)
            self.movie.setSpeed(20) 
            
        # IDLE: Azul cian natural
        elif self.state == "IDLE":
            self.color_effect.setColor(QColor(0, 150, 255))
            self.color_effect.setStrength(0.4)
            self.movie.setSpeed(100) 
            
        # LISTENING: Verde, un poco más rápido
        elif self.state == "LISTENING":
            self.color_effect.setColor(QColor(0, 255, 100))
            self.color_effect.setStrength(0.8)
            self.movie.setSpeed(150) 
            
        # THINKING: Naranja, girando rápidamente
        elif self.state == "THINKING":
            self.color_effect.setColor(QColor(255, 150, 0))
            self.color_effect.setStrength(0.8)
            self.movie.setSpeed(250) 
            
        # SPEAKING: Cian brillante y rápido
        elif self.state == "SPEAKING":
            self.color_effect.setColor(QColor(0, 255, 255))
            self.color_effect.setStrength(1.0)
            self.movie.setSpeed(200)

    # Permitir arrastrar la ventana manteniendo presionado el click izquierdo
    def mousePressEvent(self, event):
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
