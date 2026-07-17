import json
import os
import time
import speech_recognition as sr
import pygame
import asyncio
import edge_tts

class VoiceHandler:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)["voice"]
            
        self.recognizer = sr.Recognizer()
        # Sensibilidad inicial más baja (más sensible) por defecto
        self.recognizer.energy_threshold = 200
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 0.5 # Detectar el fin del habla mucho más rápido (por defecto es 0.8)
        
        pygame.mixer.init()
        
    def calibrate_microphone(self):
        """Calibra la sensibilidad del micrófono basándose en el ruido ambiental de la habitación"""
        try:
            print("[JARVIS SISTEMA] Calibrando micrófono para el ruido ambiental...")
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print(f"[JARVIS SISTEMA] Calibración terminada. Umbral de energía configurado en: {self.recognizer.energy_threshold}")
        except Exception as e:
            print(f"[JARVIS ERROR] No se pudo calibrar el micrófono: {e}")
        
    def play_startup_sound(self):
        # En vez de un MP3 estático, saludamos dinámicamente al señor
        greeting = "Sistemas en línea, señor. Todos los módulos operativos. ¿Qué desea ordenar?"
        self.speak(greeting)
 
    def listen_for_wake_word(self, wake_word="jarvis"):
        with sr.Microphone() as source:
            try:
                audio = self.recognizer.listen(source, timeout=1.5, phrase_time_limit=4)
                text = self.recognizer.recognize_google(audio, language="es-ES").lower()
                if wake_word in text:
                    parts = text.split(wake_word, 1)
                    payload = parts[1].strip() if len(parts) > 1 else ""
                    return True, payload
            except:
                pass
        return False, ""

    def listen(self, timeout=8, phrase_time_limit=15):
        with sr.Microphone() as source:
            print("Escuchando (Habla ahora)...")
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                print("Procesando voz...")
                text = self.recognizer.recognize_google(audio, language="es-ES")
                return text
            except sr.WaitTimeoutError:
                print("No detecté que hablaras (Timeout).")
                return None
            except sr.UnknownValueError:
                print("No pude entender el audio. Intenta hablar más claro o fuerte.")
                return ""
            except sr.RequestError as e:
                print(f"Error al contactar con el servicio de reconocimiento: {e}")
                return None
                
    def speak(self, text):
        print(f"Jarvis dice: {text}")
        audio_file = "temp_response.mp3"
        
        # Generar audio con edge-tts asíncrono
        communicate = edge_tts.Communicate(text, self.config.get("edge_voice", "es-ES-AlvaroNeural"))
        asyncio.run(communicate.save(audio_file))
        
        if os.path.exists(audio_file):
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
            try:
                os.remove(audio_file)
            except Exception as e:
                pass
