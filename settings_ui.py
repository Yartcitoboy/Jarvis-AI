import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
import psutil

class JarvisSettingsPanel(QWidget):
    settings_changed = pyqtSignal(dict)
    widget_toggle = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # Temporizador para actualizar estadísticas del sistema cada segundo
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        
    def initUI(self):
        self.setWindowTitle("J.A.R.V.I.S. - Panel de Control")
        self.resize(350, 450)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        
        # Estilo futurista oscuro (Glassmorphic sci-fi style)
        self.setStyleSheet("""
            QWidget {
                background-color: #0a0e17;
                color: #00e5ff;
                font-family: 'Segoe UI', 'Consolas', monospace;
            }
            QLabel {
                font-size: 13px;
                padding: 4px;
            }
            QLabel#header {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                border-bottom: 2px solid #00e5ff;
                padding-bottom: 8px;
                margin-bottom: 10px;
            }
            QPushButton {
                background-color: #121e30;
                border: 1px solid #00e5ff;
                color: #00e5ff;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #00e5ff;
                color: #0a0e17;
            }
            QComboBox {
                background-color: #121e30;
                border: 1px solid #00e5ff;
                color: #00e5ff;
                padding: 5px;
                border-radius: 3px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border: 1px solid #00e5ff;
                background-color: #121e30;
            }
            QCheckBox::indicator:checked {
                background-color: #00e5ff;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("J.A.R.V.I.S. SYSTEM MONITOR")
        title_label.setObjectName("header")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Estadísticas del sistema
        self.cpu_label = QLabel("Carga CPU: -- %")
        self.ram_label = QLabel("Memoria RAM: -- %")
        self.disk_label = QLabel("Disco Duro: -- %")
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.disk_label)
        
        # Separador visual
        sep = QLabel("—" * 30)
        sep.setAlignment(Qt.AlignCenter)
        sep.setStyleSheet("color: #1f3654;")
        layout.addWidget(sep)
        
        # Selector de Tema de Color
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Tema Visual:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Holograma (Cian)", "Alerta (Rojo)", "Operativo (Verde)", "Neutro (Blanco)"])
        self.theme_combo.currentIndexChanged.connect(self.emit_settings)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
        # Checkbox Widget Visible
        self.widget_check = QCheckBox("Mostrar Núcleo en Pantalla")
        self.widget_check.setChecked(True)
        self.widget_check.stateChanged.connect(self.toggle_widget)
        layout.addWidget(self.widget_check)
        
        # Espaciador
        layout.addStretch()
        
        # Botón para Forzar Análisis de VRAM
        vram_btn = QPushButton("Liberar Caché de Modelos VRAM")
        vram_btn.clicked.connect(self.purge_vram)
        layout.addWidget(vram_btn)
        
        # Botón de cierre
        close_btn = QPushButton("Cerrar Panel")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        self.update_stats()
        
    def update_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            self.cpu_label.setText(f"Carga CPU:  [ {cpu}% ]")
            self.ram_label.setText(f"Memoria RAM: [ {ram}% ]")
            self.disk_label.setText(f"Disco Duro:  [ {disk}% ]")
        except Exception as e:
            pass
            
    def emit_settings(self):
        theme_name = self.theme_combo.currentText()
        color_map = {
            "Holograma (Cian)": "#00e5ff",
            "Alerta (Rojo)": "#ff1744",
            "Operativo (Verde)": "#00e676",
            "Neutro (Blanco)": "#ffffff"
        }
        color = color_map.get(theme_name, "#00e5ff")
        self.settings_changed.emit({"color": color, "theme_name": theme_name})
        
    def toggle_widget(self, state):
        visible = (state == Qt.Checked)
        self.widget_toggle.emit(visible)
        
    def purge_vram(self):
        # Purga de Ollama VRAM forzando la descarga de modelos
        import requests
        print("[JARVIS SISTEMA] Solicitando descarga de todos los modelos de VRAM...")
        try:
            # Enviar keep_alive a 0 para descargar modelos inactivos de Ollama
            requests.post("http://localhost:11434/api/generate", json={"model": "moondream", "keep_alive": 0}, timeout=1)
            requests.post("http://localhost:11434/api/generate", json={"model": "phi3", "keep_alive": 0}, timeout=1)
        except Exception:
            pass
