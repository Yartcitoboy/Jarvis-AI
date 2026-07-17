import os
import webbrowser
import subprocess
import pyautogui
import time

def execute_command(command_str):
    """
    Parsea y ejecuta comandos del sistema.
    Formato esperado: [COMMAND: open_web | url: https://www.youtube.com]
    """
    try:
        command_str = command_str.strip()
        if not command_str.startswith("[COMMAND:") or not command_str.endswith("]"):
            return None
        
        # Quitar los corchetes exteriores
        content = command_str[9:-1] # Quita "[COMMAND: " y el "]" final
        parts = [p.strip() for p in content.split("|")]
        
        cmd_type = parts[0]
        params = {}
        for part in parts[1:]:
            if ":" in part:
                k, v = part.split(":", 1)
                params[k.strip()] = v.strip()
                
        print(f"\n[JARVIS ACCIÓN] Ejecutando: {cmd_type} con parámetros {params}")
        
        if cmd_type == "open_web":
            url = params.get("url")
            if url:
                if not url.startswith("http"):
                    url = "https://" + url
                webbrowser.open(url)
                return f"Web abierta: {url}"
                
        elif cmd_type == "open_app":
            app = params.get("app", "").lower()
            if app == "notepad" or app == "bloc de notas":
                subprocess.Popen("notepad.exe")
                return "Notepad abierto."
            elif app == "vscode" or app == "code":
                os.system("start code")
                return "VS Code abierto."
            elif app == "obsidian":
                os.system("start obsidian://")
                return "Obsidian abierto."
            else:
                try:
                    os.system(f"start {app}")
                    return f"Ejecutando inicio de {app}"
                except Exception as e:
                    return f"No se pudo iniciar la aplicación {app}: {e}"
                    
        elif cmd_type == "close_tab":
            # Usar pyautogui para simular Ctrl + W (atajo universal para cerrar pestaña)
            pyautogui.hotkey('ctrl', 'w')
            return "Pestaña cerrada."
            
        elif cmd_type == "close_app":
            app = params.get("app", "").lower()
            # Asignar nombres comunes a sus ejecutables
            if "chrome" in app: exe = "chrome.exe"
            elif "edge" in app: exe = "msedge.exe"
            elif "firefox" in app: exe = "firefox.exe"
            elif "bloc" in app or "notepad" in app: exe = "notepad.exe"
            elif "code" in app or "visual" in app: exe = "Code.exe"
            else: exe = f"{app}.exe"
            
            os.system(f"taskkill /F /IM {exe}")
            return f"Aplicación {exe} cerrada."
                    
        elif cmd_type == "take_note":
            text = params.get("text")
            if text:
                note_file = "notas_jarvis.txt"
                with open(note_file, "a", encoding="utf-8") as f:
                    import datetime
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{now}] {text}\n")
                print(f"[JARVIS SISTEMA] Nota guardada en {note_file}: '{text}'")
                return f"Nota guardada."
                
        elif cmd_type == "quit":
            print("[JARVIS SISTEMA] Apagando el sistema por orden del usuario.")
            # Forzamos el cierre de la aplicación
            import sys
            import os
            os._exit(0)
            return "Apagando..."
                
    except Exception as e:
        print(f"[JARVIS ERROR] Fallo al ejecutar el comando: {e}")
        
    return None
