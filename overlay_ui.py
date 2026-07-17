import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QFont

class JarvisHUDOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.subtitle_text = ""
        self.target_text = ""
        self.target_rect = None
        self.theme_color = QColor(0, 229, 255, 200) # Cian por defecto
        
    def initUI(self):
        # Pantalla completa, sin bordes, transparente e invisible a los clics (click-through)
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.SubWindow | 
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Ocupar toda la pantalla primaria
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Etiqueta de subtítulos flotantes
        self.sub_label = QLabel(self)
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Segoe UI', 'Consolas', monospace;
            font-size: 20px;
            font-weight: bold;
            background-color: rgba(10, 14, 23, 180);
            border: 1px solid #00e5ff;
            border-radius: 6px;
            padding: 10px 20px;
        """)
        self.sub_label.hide()
        
        # Temporizador para ocultar notificaciones de HUD
        self.hud_timer = QTimer(self)
        self.hud_timer.setSingleShot(True)
        self.hud_timer.timeout.connect(self.clear_hud)
        
    def set_theme_color(self, hex_color):
        # Cambiar el color del HUD dinámicamente
        self.theme_color = QColor(hex_color)
        self.theme_color.setAlpha(200)
        self.sub_label.setStyleSheet(f"""
            color: #ffffff;
            font-family: 'Segoe UI', 'Consolas', monospace;
            font-size: 20px;
            font-weight: bold;
            background-color: rgba(10, 14, 23, 190);
            border: 1.5px solid {hex_color};
            border-radius: 6px;
            padding: 10px 20px;
        """)
        self.update()
        
    def show_subtitle(self, text):
        if not text:
            self.sub_label.hide()
            return
            
        self.sub_label.setText(text)
        self.sub_label.adjustSize()
        
        # Centrar horizontalmente al fondo de la pantalla
        x = (self.width() - self.sub_label.width()) // 2
        y = int(self.height() * 0.85)
        self.sub_label.move(x, y)
        self.sub_label.show()
        
    def clear_subtitle(self):
        self.sub_label.hide()
        
    def trigger_analysis_hud(self, message="ANALIZANDO PANTALLA..."):
        self.target_text = message
        # Definir una caja de objetivo en el centro de la pantalla
        w, h = 400, 300
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2
        self.target_rect = QRect(x, y, w, h)
        
        self.update()
        self.hud_timer.start(5000) # Mostrar HUD por 5 segundos
        
    def clear_hud(self):
        self.target_text = ""
        self.target_rect = None
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dibujar bordes decorativos estilo Iron Man HUD
        pen = QPen(self.theme_color, 2)
        painter.setPen(pen)
        
        # 1. Cantoneras de pantalla
        offset = 30
        length = 40
        # Arriba Izquierda
        painter.drawLine(offset, offset, offset + length, offset)
        painter.drawLine(offset, offset, offset, offset + length)
        # Arriba Derecha
        painter.drawLine(self.width() - offset, offset, self.width() - offset - length, offset)
        painter.drawLine(self.width() - offset, offset, self.width() - offset, offset + length)
        # Abajo Izquierda
        painter.drawLine(offset, self.height() - offset, offset + length, self.height() - offset)
        painter.drawLine(offset, self.height() - offset, offset, self.height() - offset - length)
        # Abajo Derecha
        painter.drawLine(self.width() - offset, self.height() - offset, self.width() - offset - length, self.height() - offset)
        painter.drawLine(self.width() - offset, self.height() - offset, self.width() - offset, self.height() - offset - length)
        
        # 2. Caja de Objetivo Central (Target Box) si está activa
        if self.target_rect and self.target_text:
            # Dibujar caja de objetivo punteada
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.target_rect)
            
            # Líneas de cruz central
            cx = self.target_rect.x() + self.target_rect.width() // 2
            cy = self.target_rect.y() + self.target_rect.height() // 2
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(cx - 20, cy, cx + 20, cy)
            painter.drawLine(cx, cy - 20, cx, cy + 20)
            
            # Texto del objetivo
            painter.setFont(QFont("Consolas", 14, QFont.Bold))
            painter.drawText(
                self.target_rect.x() + 10, 
                self.target_rect.y() - 10, 
                f">> {self.target_text}"
            )
            
            # Dibujar un pequeño gráfico decorativo en las esquinas de la caja
            r = self.target_rect
            painter.drawArc(r.x() - 10, r.y() - 10, 20, 20, 90 * 16, 90 * 16)
            painter.drawArc(r.right() - 10, r.y() - 10, 20, 20, 0 * 16, 90 * 16)
            painter.drawArc(r.x() - 10, r.bottom() - 10, 20, 20, 180 * 16, 90 * 16)
            painter.drawArc(r.right() - 10, r.bottom() - 10, 20, 20, 270 * 16, 90 * 16)
            
        # 3. Datos del sistema de fondo en la esquina superior derecha
        painter.setFont(QFont("Consolas", 9))
        painter.drawText(self.width() - 250, 60, "SYS_STATUS: ACTIVE")
        painter.drawText(self.width() - 250, 75, "NEURAL_NET: OLLAMA_LOCAL")
        painter.drawText(self.width() - 250, 90, "PROTOCOL: STARK_HUD_V1.2")
