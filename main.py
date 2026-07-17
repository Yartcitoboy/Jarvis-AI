import sys
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject

from gui_widget import JarvisWidget
from voice_handler import VoiceHandler
from assistant_brain import AssistantBrain

class AssistantController(QObject):
    state_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.voice = VoiceHandler()
        self.brain = AssistantBrain()
        self.is_busy = False
        import time
        self.last_active_time = time.time()
        self.is_sleeping = False

    def start_interaction(self):
        """Inicia el ciclo: Escuchar -> Pensar -> Hablar"""
        if self.is_busy:
            return
        self.is_busy = True
        
        import time
        self.last_active_time = time.time()
        self.is_sleeping = False
        
        # Se ejecuta en un hilo separado para que la interfaz gráfica siga rotando fluidamente
        threading.Thread(target=self._interaction_loop, daemon=True).start()
        
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
                
                activated = self.voice.listen_for_wake_word("jarvis")
                if activated:
                    print("¡Palabra clave detectada!")
                    self.start_interaction()
            else:
                time.sleep(0.5)
        
    def _interaction_loop(self):
        try:
            # 1. Escuchar
            self.state_changed.emit("LISTENING")
            user_text = self.voice.listen()
            
            if not user_text:
                return
                
            print(f"Tú: {user_text}")
                
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
            self.voice.speak(speak_text)
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
    
    # Conectar la interfaz gráfica con el controlador de cerebro/voz
    widget.request_listen.connect(controller.start_interaction)
    controller.state_changed.connect(widget.set_state)
    
    # Reproducir sonido de arranque
    threading.Thread(target=controller.voice.play_startup_sound, daemon=True).start()
    
    # Iniciar la escucha de la palabra clave "Jarvis" en segundo plano
    threading.Thread(target=controller.wake_word_loop, daemon=True).start()
    
    widget.show()
    
    print("="*40)
    print("J.A.R.V.I.S INICIADO CON ÉXITO")
    print("Instrucciones:")
    print(" - Arrastra el núcleo con clic IZQUIERDO para moverlo.")
    print(" - Di 'Jarvis' o haz clic DERECHO sobre el núcleo para hablarle.")
    print("="*40)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
