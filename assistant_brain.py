import json
import requests

class AssistantBrain:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.reload_config()
        self.history = [
            {
                "role": "system", 
                "content": (
                    "Eres J.A.R.V.I.S., un asistente de inteligencia artificial leal, educado y muy inteligente. "
                    "Responde siempre de forma súper corta (1 o 2 oraciones máximo) a menos que se te pida explícitamente algo largo. Sé rápido y conciso.\n\n"
                    "Tienes la capacidad de ejecutar comandos en la computadora del usuario usando un formato especial al inicio de tu respuesta. "
                    "Si el usuario te pide realizar una acción física o abrir/cerrar algo, debes incluir el comando exacto al principio de tu respuesta y luego tu confirmación hablada muy breve. "
                    "Los comandos disponibles son:\n"
                    "- Para abrir páginas web: [COMMAND: open_web | url: <url_completa>]\n"
                    "- Para abrir aplicaciones del sistema: [COMMAND: open_app | app: <notepad | vscode | obsidian>]\n"
                    "- Para cerrar la pestaña actual del navegador: [COMMAND: close_tab]\n"
                    "- Para cerrar una aplicación: [COMMAND: close_app | app: <nombre_app>]\n"
                    "- Para tomar una nota rápida de texto: [COMMAND: take_note | text: <contenido_de_la_nota>]\n"
                    "- Para automatizar o enviar mensajes por n8n: [COMMAND: trigger_n8n | workflow: <whatsapp/gmail/etc> | payload: <mensaje o datos>]\n"
                    "- Para apagar o cerrar a Jarvis completamente: [COMMAND: quit]\n\n"
                    "Ejemplo: Si el usuario dice 'abre youtube', tu respuesta exacta debe ser:\n"
                    "[COMMAND: open_web | url: https://www.youtube.com] Abriendo YouTube, señor.\n"
                    "Ejemplo: Si el usuario dice 'envía un mensaje a mi mamá diciendo hola', tu respuesta debe ser:\n"
                    "[COMMAND: trigger_n8n | workflow: whatsapp | payload: enviar hola a mamá] Mensaje enviado.\n"
                    "No inventes otros comandos. Si la petición es una conversación normal y no requiere abrir nada o tomar notas, responde normalmente sin ningún comando."
                )
            }
        ]
        
    def reload_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)["api"]
            
    def _get_obsidian_context(self):
        import os
        vault_path = self.config.get("obsidian_vault_path", "Obsidian_Vault")
        context = ""
        try:
            profile_path = os.path.join(vault_path, "perfil.md")
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    context += f.read() + "\n"
        except Exception as e:
            print(f"Error leyendo Obsidian: {e}")
            
        if context:
            return f"\n[Nota del sistema: Contexto desde tu memoria (Obsidian):\n{context}]"
        return ""
        
    def ask(self, user_text):
        self.reload_config()
        
        import datetime
        now = datetime.datetime.now()
        timestamp_info = f"\n[Nota del sistema: La fecha y hora actual local es {now.strftime('%d/%m/%Y %H:%M:%S')}]"
        
        obsidian_info = self._get_obsidian_context()
        
        self.history.append({"role": "user", "content": user_text + timestamp_info + obsidian_info})
        
        if self.config["engine"] == "openrouter":
            return self._ask_openrouter(user_text)
        else:
            return self._ask_ollama(user_text)
            
    def _get_free_models(self):
        try:
            r = requests.get("https://openrouter.ai/api/v1/models", timeout=5)
            r.raise_for_status()
            models_data = r.json().get("data", [])
            free_models = [m["id"] for m in models_data if ":free" in m["id"]]
            if free_models:
                return free_models
        except Exception as e:
            print(f"No se pudo consultar los modelos dinámicos: {e}")
            
        return [
            "google/gemma-4-31b-it:free",
            "tencent/hy3:free",
            "cohere/north-mini-code:free",
            "google/gemma-2-9b-it:free"
        ]

    def _ask_openrouter(self, user_text):
        headers = {
            "Authorization": f"Bearer {self.config['openrouter_key']}",
            "Content-Type": "application/json"
        }
        
        free_models = self._get_free_models()
        configured_model = self.config.get("openrouter_model")
        if configured_model in free_models:
            free_models.remove(configured_model)
        free_models.insert(0, configured_model)
        
        for model in free_models:
            print(f"Intentando generar respuesta con el modelo: {model}...")
            data = {
                "model": model,
                "messages": self.history
            }
            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    reply = result["choices"][0]["message"]["content"]
                    self.history.append({"role": "assistant", "content": reply})
                    
                    if model != configured_model:
                        print(f"Guardando nuevo modelo funcional por defecto: {model}")
                        self._save_working_model(model)
                    
                    return reply
                else:
                    print(f"Error en respuesta del modelo {model}: {result}")
            except requests.exceptions.HTTPError as e:
                print(f"Error HTTP con {model}: {e}")
                if e.response is not None:
                    print(f"Detalle: {e.response.text}")
            except Exception as e:
                print(f"Error inesperado con {model}: {e}")
                
        # --- PLAN B: FALLBACK AUTOMÁTICO A OLLAMA LOCAL ---
        print("\n[JARVIS ADVERTENCIA] Todos los modelos de OpenRouter fallaron o no hay internet.")
        print("Activando PLAN B: Conectando con la IA local (Ollama)...")
        # Cambiamos temporalmente el texto enviado para no duplicar en el historial
        self.history.pop() # Quitar el último mensaje duplicado antes de llamar a ask_ollama
        return self._ask_ollama(user_text)

    def _save_working_model(self, model):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                full_config = json.load(f)
            full_config["api"]["openrouter_model"] = model
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(full_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar el nuevo modelo por defecto: {e}")

    def _ask_ollama(self, user_text):
        # Aseguramos tener el prompt del usuario en el historial para Ollama
        # (ya que lo sacamos en la línea de arriba antes del fallback)
        import datetime
        now = datetime.datetime.now()
        timestamp_info = f"\n[Nota del sistema: La fecha y hora actual local es {now.strftime('%d/%m/%Y %H:%M:%S')}]"
        self.history.append({"role": "user", "content": user_text + timestamp_info})
        
        chat_url = self.config["ollama_url"].replace("/api/generate", "/api/chat")
        chat_data = {
            "model": self.config["ollama_model"],
            "messages": self.history,
            "stream": False
        }
        try:
            response = requests.post(chat_url, json=chat_data)
            response.raise_for_status()
            result = response.json()
            reply = result["message"]["content"]
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"Error con Ollama: {e}")
            return "Lo siento señor, tanto OpenRouter como Ollama local han fallado. No puedo responder en este momento."
