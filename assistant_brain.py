import json
import requests
import datetime
import os
import base64
import io
import pyautogui

class AssistantBrain:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.reload_config()
        self.history = []
        self._init_history()
        
    def _init_history(self):
        self.history = [
            {
                "role": "system", 
                "content": (
                    "Eres J.A.R.V.I.S., un asistente de inteligencia artificial leal, educado y altamente inteligente. "
                    "Responde siempre de forma súper corta (1 o 2 oraciones máximo) a menos que se te pida explícitamente algo largo o técnico. Sé rápido y conciso.\n\n"
                    "Puedes ejecutar comandos en la PC del usuario usando este formato especial al inicio de tu respuesta:\n"
                    "- Para abrir páginas web: [COMMAND: open_web | url: <url_completa>]\n"
                    "- Para abrir aplicaciones: [COMMAND: open_app | app: <notepad | vscode | obsidian>]\n"
                    "- Para cerrar pestaña del navegador: [COMMAND: close_tab]\n"
                    "- Para cerrar una aplicación: [COMMAND: close_app | app: <nombre_app>]\n"
                    "- Para tomar una nota rápida de texto: [COMMAND: take_note | text: <contenido_de_la_nota>]\n"
                    "- Para automatizar o enviar mensajes por n8n: [COMMAND: trigger_n8n | workflow: <whatsapp/gmail/etc> | payload: <mensaje o datos>]\n"
                    "- Para actualizar tus datos memorizados en Obsidian: [COMMAND: update_memory | key: <clave> | val: <valor>]\n"
                    "- Para apagar o cerrar a Jarvis completamente: [COMMAND: quit]\n\n"
                    "Ejemplo si el usuario te dice un hecho nuevo sobre él (ej. 'Mi cumpleaños es el 5 de marzo'):\n"
                    "[COMMAND: update_memory | key: cumpleaños | val: 05/03/2002] Entendido, recordaré que su cumpleaños es el 5 de marzo, señor.\n"
                    "Ejemplo para n8n: [COMMAND: trigger_n8n | workflow: whatsapp | payload: Hola mamá] Mensaje enviado.\n"
                    "No inventes otros comandos. Si no necesitas ejecutar ninguna acción física, responde de forma conversacional normal."
                )
            }
        ]
        
    def reload_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)["api"]
            
    def _get_obsidian_context(self):
        vault_path = self.config.get("obsidian_vault_path", "Obsidian_Vault")
        context = ""
        
        # Leer perfil base
        try:
            profile_path = os.path.join(vault_path, "perfil.md")
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    context += "### Datos de Perfil:\n" + f.read() + "\n"
        except Exception as e:
            print(f"Error leyendo perfil de Obsidian: {e}")
            
        # Leer memoria auto-actualizada
        try:
            memory_path = os.path.join(vault_path, "memoria.md")
            if os.path.exists(memory_path):
                with open(memory_path, "r", encoding="utf-8") as f:
                    context += "### Datos Memorizados:\n" + f.read() + "\n"
        except Exception as e:
            print(f"Error leyendo memoria de Obsidian: {e}")
            
        if context:
            return f"\n[Nota del sistema: Contexto de memoria en Obsidian:\n{context}]"
        return ""
        
    def _capture_screen_base64(self):
        try:
            screenshot = pyautogui.screenshot()
            screenshot.thumbnail((1024, 576))  # Redimensionar para optimizar tokens y latencia
            buffered = io.BytesIO()
            screenshot.save(buffered, format="JPEG", quality=80)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return img_str
        except Exception as e:
            print(f"Error al capturar la pantalla: {e}")
            return None

    def ask(self, user_text):
        self.reload_config()
        
        # Enrutador Multi-Agente
        user_lower = user_text.lower()
        is_vision = any(w in user_lower for w in ["pantalla", "mira esto", "mira mi pantalla", "qué tengo abierto", "analiza mi pantalla"])
        is_deep_thought = any(w in user_lower for w in ["analiza en detalle", "código", "programa", "escribe un", "desarrolla", "planifica", "explica detalladamente"])
        is_command_heavy = any(w in user_lower for w in ["abre", "cierra", "envía", "manda", "recuerda", "apágate"])
        
        # Modelo y agentes dinámicos
        if is_vision:
            print("[MULTI-AGENTE] Enrutando al Agente de Visión...")
            return self._run_vision_agent(user_text)
        elif is_deep_thought:
            print("[MULTI-AGENTE] Enrutando al Agente de Pensamiento Profundo...")
            return self._run_deep_thinking_agent(user_text)
        elif is_command_heavy:
            print("[MULTI-AGENTE] Enrutando al Agente de Construcción de Comandos...")
            return self._run_default_agent(user_text, is_builder=True)
        else:
            print("[MULTI-AGENTE] Enrutando al Agente de Respuesta Rápida...")
            return self._run_default_agent(user_text, is_builder=False)

    def _get_free_vision_models(self):
        try:
            r = requests.get("https://openrouter.ai/api/v1/models", timeout=5)
            r.raise_for_status()
            models_data = r.json().get("data", [])
            free_vision = []
            for m in models_data:
                m_id = m["id"].lower()
                if (":free" in m_id 
                    and m.get("architecture") 
                    and "image" in m["architecture"].get("input_modalities", [])
                    and "safety" not in m_id
                    and "moderation" not in m_id):
                    free_vision.append(m["id"])
                    
            if free_vision:
                # Priorizar modelos VL (Vision-Language), Qwen, Gemma-4 o Llama
                def sort_key(model_id):
                    model_id_lower = model_id.lower()
                    score = 0
                    if "vl" in model_id_lower: score += 10
                    if "qwen" in model_id_lower: score += 8
                    if "gemma" in model_id_lower: score += 6
                    if "llama" in model_id_lower: score += 4
                    return score
                
                free_vision.sort(key=sort_key, reverse=True)
                return free_vision
        except Exception as e:
            print(f"Error consultando modelos de visión dinámicos: {e}")
        return ["nvidia/nemotron-nano-12b-v2-vl:free", "google/gemma-4-31b-it:free"]

    def _run_vision_agent(self, user_text):
        img_b64 = self._capture_screen_base64()
        if not img_b64:
            return "Lo siento señor, no he podido capturar la pantalla en este momento."
            
        print("[JARVIS SISTEMA] Pantalla capturada. Analizando imagen...")
        
        headers = {
            "Authorization": f"Bearer {self.config['openrouter_key']}",
            "Content-Type": "application/json"
        }
        
        obsidian_info = self._get_obsidian_context()
        now = datetime.datetime.now()
        timestamp_info = f"\n[Nota del sistema: Hora actual local: {now.strftime('%d/%m/%Y %H:%M:%S')}]"
        
        messages = [
            {"role": "system", "content": self.history[0]["content"] + obsidian_info},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text + timestamp_info},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}"
                        }
                    }
                ]
            }
        ]
        
        free_vision_models = self._get_free_vision_models()
        
        for model in free_vision_models:
            print(f"Intentando analizar pantalla con el modelo visual: {model}...")
            data = {
                "model": model,
                "messages": messages
            }
            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=20)
                response.raise_for_status()
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    reply = result["choices"][0]["message"]["content"]
                    self.history.append({"role": "user", "content": user_text + " [Analizando pantalla]"})
                    self.history.append({"role": "assistant", "content": reply})
                    return reply
            except Exception as e:
                print(f"Error con modelo visual {model}: {e}")
                
        return "Lo siento señor, he tenido un problema analizando su pantalla a través de todos los modelos de la red."

    def _run_deep_thinking_agent(self, user_text):
        # Usamos DeepSeek-R1 (modelo de razonamiento de largo pensamiento) si está libre, o Llama-3-70b
        model = "deepseek/deepseek-r1:free"
        headers = {
            "Authorization": f"Bearer {self.config['openrouter_key']}",
            "Content-Type": "application/json"
        }
        
        obsidian_info = self._get_obsidian_context()
        now = datetime.datetime.now()
        timestamp_info = f"\n[Nota del sistema: La fecha/hora es {now.strftime('%d/%m/%Y %H:%M:%S')}. Estás en modo de Razonamiento Profundo. Tómate tu tiempo para responder de manera óptima pero precisa.]"
        
        self.history.append({"role": "user", "content": user_text + timestamp_info + obsidian_info})
        
        data = {
            "model": model,
            "messages": self.history
        }
        
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                reply = result["choices"][0]["message"]["content"]
                
                # Quitar el bloque <think> si lo tiene DeepSeek para la lectura hablada
                clean_reply = reply
                if "<think>" in reply and "</think>" in reply:
                    clean_reply = reply.split("</think>")[1].strip()
                    
                self.history.append({"role": "assistant", "content": clean_reply})
                return clean_reply
        except Exception as e:
            print(f"Error con DeepSeek R1: {e}. Probando fallback casual...")
            self.history.pop()  # Limpiar último input
            
        return self._run_default_agent(user_text, is_builder=False)

    def _run_default_agent(self, user_text, is_builder=False):
        headers = {
            "Authorization": f"Bearer {self.config['openrouter_key']}",
            "Content-Type": "application/json"
        }
        
        obsidian_info = self._get_obsidian_context()
        now = datetime.datetime.now()
        timestamp_info = f"\n[Nota del sistema: La fecha y hora actual local es {now.strftime('%d/%m/%Y %H:%M:%S')}]"
        
        self.history.append({"role": "user", "content": user_text + timestamp_info + obsidian_info})
        
        # En caso de constructor de comandos, priorizamos Gemini 2.5 Flash por velocidad y precisión de formato
        model = self.config.get("openrouter_model", "google/gemini-2.5-flash:free")
        
        # Intentar llamada
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
                return reply
        except Exception as e:
            print(f"Error en agente por defecto: {e}. Conectando a Ollama Local...")
            self.history.pop()  # Limpiar último input para no duplicar en Ollama
            
        return self._ask_ollama(user_text)

    def _ask_ollama(self, user_text):
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
            return "Lo siento señor, no he podido establecer comunicación con la red ni con la IA local."
