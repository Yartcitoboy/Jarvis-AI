import sys
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject

from gui_widget import JarvisWidget
from voice_handler import VoiceHandler
from assistant_brain import AssistantBrain
from settings_ui import JarvisSettingsPanel
from overlay_ui import JarvisHUDOverlay

class AssistantController(QObject):
    state_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.voice = VoiceHandler()
        self.brain = AssistantBrain()
        self.is_busy = False
        self.hud = None  # Se asigna en main()
        import time
        self.last_active_time = time.time()
        self.is_sleeping = False

    def start_interaction(self, inline_payload=None):
        """Inicia el ciclo: Escuchar -> Pensar -> Hablar"""
        if self.is_busy:
            return
        self.is_busy = True
        
        import time
        self.last_active_time = time.time()
        self.is_sleeping = False
        
        # Se ejecuta en un hilo separado para que la interfaz gráfica siga rotando fluidamente
        threading.Thread(target=self._interaction_loop, args=(inline_payload,), daemon=True).start()
        
    def wake_word_loop(self):
        """Hilo en segundo plano que escucha todo el tiempo buscando la palabra 'Jarvis'"""
        print("Buscando la palabra 'Jarvis' de fondo...")
        import time
        while True:
            if not self.is_busy:
                # Si pasa 1 minuto (60 seg) sin interactuar, entra en reposo
                if not self.is_sleeping and (time.time() - self.last_active_time > 60):
                    self.is_sleeping = True
                    self.state_changed.emit("SLEEP")
                    print("Jarvis ha entrado en modo reposo (Bajo consumo).")
                
                activated, payload = self.voice.listen_for_wake_word("jarvis")
                if activated:
                    print("¡Palabra clave detectada!")
                    if payload:
                        print(f"Comando integrado detectado: '{payload}'")
                    self.start_interaction(inline_payload=payload if payload else None)
            else:
                time.sleep(0.5)
                
    def proactive_loop(self):
        """Hilo de fondo para comentarios espontáneos"""
        import time
        # Esperar 45 segundos tras arrancar antes de poder hablar de forma proactiva
        time.sleep(45)
        while True:
            if not self.is_busy and not self.is_sleeping:
                time_since_last_action = time.time() - self.last_active_time
                # Comentario espontáneo si no hay actividad en 3 minutos (180 seg)
                if time_since_last_action > 180:
                    self.trigger_proactive_speech()
            time.sleep(10)
            
    def trigger_proactive_speech(self):
        if self.is_busy:
            return
        self.is_busy = True
        try:
            self.state_changed.emit("THINKING")
            prompt = (
                "[Nota del sistema: Genera un comentario proactivo espontáneo para el usuario. "
                "Comenta sobre el estado de la PC o pregúntale si necesita ayuda con n8n o su perfil de Obsidian. "
                "Sé extremadamente breve (máximo 1 oración) y salúdalo como Señor.]"
            )
            response_text = self.brain.ask(prompt)
            
            speak_text = response_text
            if response_text.strip().startswith("[COMMAND:"):
                end_idx = response_text.find("]")
                if end_idx != -1:
                    command_part = response_text[:end_idx + 1]
                    speak_text = response_text[end_idx + 1:].strip()
                    from skills_handler import execute_command
                    threading.Thread(target=execute_command, args=(command_part,), daemon=True).start()
            
            self.state_changed.emit("SPEAKING")
            if self.hud:
                self.hud.show_subtitle(speak_text)
            self.voice.speak(speak_text)
            if self.hud:
                self.hud.clear_subtitle()
            import time
            self.last_active_time = time.time()
        except Exception as e:
            print(f"Error en habla proactiva: {e}")
        finally:
            self.state_changed.emit("IDLE")
            self.is_busy = False
        
    def _interaction_loop(self, inline_payload=None):
        try:
            if inline_payload:
                user_text = inline_payload
                print(f"Tú (De voz directa): {user_text}")
            else:
                # 1. Escuchar
                self.state_changed.emit("LISTENING")
                user_text = self.voice.listen()
            
            if not user_text:
                return
                
            if not inline_payload:
                print(f"Tú: {user_text}")
                
            # Disparar HUD visual si se detecta escaneo de pantalla
            user_lower = user_text.lower()
            is_vision = any(w in user_lower for w in ["pantalla", "mira esto", "mira mi pantalla", "qué tengo abierto", "analiza mi pantalla"])
            if is_vision and self.hud:
                self.hud.trigger_analysis_hud("SYS_SCAN: ANALIZANDO PANTALLA")
                
            # 2. Pensar
            self.state_changed.emit("THINKING")
            response_text = self.brain.ask(user_text)
            
            # Separar el comando del texto hablado
            speak_text = response_text
            
            if response_text.strip().startswith("[COMMAND:"):
                # Buscar dónde termina el comando
                end_idx = response_text.find("]")
                if end_idx != -1:
                    command_part = response_text[:end_idx + 1]
                    # El texto que se va a leer en voz alta es todo lo que viene después de los corchetes
                    speak_text = response_text[end_idx + 1:].strip()
                    
                    # Importar y ejecutar el comando en segundo plano
                    from skills_handler import execute_command
                    threading.Thread(target=execute_command, args=(command_part,), daemon=True).start()
            
            # 3. Hablar (usando el texto limpio de comandos)
            self.state_changed.emit("SPEAKING")
            if self.hud:
                self.hud.show_subtitle(speak_text)
            self.voice.speak(speak_text)
            if self.hud:
                self.hud.clear_subtitle()
        except Exception as e:
            print(f"Error en el ciclo de interacción: {e}")
        finally:
            # Aseguramos que pase lo que pase, el estado vuelva a IDLE y se libere para la siguiente pregunta
            self.state_changed.emit("IDLE")
            self.is_busy = False

def main():
    app = QApplication(sys.argv)
    
    controller = AssistantController()
    widget = JarvisWidget()
    hud = JarvisHUDOverlay()
    settings_panel = JarvisSettingsPanel()
    
    # Asignar HUD al controlador para subtítulos y objetivos
    controller.hud = hud
    
    # Conectar señales del widget principal
    widget.request_listen.connect(controller.start_interaction)
    widget.request_settings.connect(settings_panel.show)
    controller.state_changed.connect(widget.set_state)
    
    # Conectar señales del panel de control
    settings_panel.settings_changed.connect(lambda data: (
        widget.set_theme_color(data["color"]),
        hud.set_theme_color(data["color"])
    ))
    settings_panel.widget_toggle.connect(lambda visible: (
        widget.show() if visible else widget.hide()
    ))
    
    # Mostrar el HUD de fondo interactivo
    hud.show()
    widget.show()
    
    # Saludo de arranque dinámico en segundo plano
    threading.Thread(target=controller.voice.play_startup_sound, daemon=True).start()
    
    # Inicializar audio secuencialmente para evitar colisiones de micrófono en hilos concurrentes
    def init_audio():
        controller.voice.calibrate_microphone()
        controller.wake_word_loop()
        
    threading.Thread(target=init_audio, daemon=True).start()
    threading.Thread(target=controller.proactive_loop, daemon=True).start()
    
    print("="*40)
    print("J.A.R.V.I.S INICIADO CON ÉXITO")
    print("Instrucciones:")
    print(" - Arrastra el núcleo con clic IZQUIERDO para moverlo.")
    print(" - Haz DOBLE CLIC IZQUIERDO en el núcleo para abrir el panel de control.")
    print(" - Di 'Jarvis' o haz clic DERECHO sobre el núcleo para hablarle.")
    print("="*40)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
