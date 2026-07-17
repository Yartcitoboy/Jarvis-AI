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
        # Fijamos la sensibilidad en 400 y APAGAMOS el ajuste dinámico
        # Así no subirá la sensibilidad después de gritar "Jarvis"
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = False
        
        pygame.mixer.init()
        
    def play_startup_sound(self):
        sound_file = self.config.get("startup_sound", "Jarvis.mp3")
        if os.path.exists(sound_file):
            print(f"Reproduciendo sonido de inicio: {sound_file}")
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        else:
            print(f"No se encontró el archivo de sonido: {sound_file}")

    def listen_for_wake_word(self, wake_word="jarvis"):
        with sr.Microphone() as source:
            # Eliminamos el adjust_for_ambient_noise aquí para no confundir tu voz con "ruido"
            try:
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                text = self.recognizer.recognize_google(audio, language="es-ES").lower()
                if wake_word in text:
                    return True
            except:
                pass
        return False

    def listen(self):
        with sr.Microphone() as source:
            print("Escuchando (Habla ahora)...")
            try:
                # Aumentamos el timeout para darte más tiempo para empezar a hablar
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
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
