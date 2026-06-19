import os
import subprocess
import webbrowser
import settings
from speaker import speak

def launch_app(app_name):
    # Standardize name
    app = app_name.lower().strip()
    
    # Load user configuration
    cfg = settings.load_settings()
    pref_browser = cfg.get("browser", "default")
    
    # URL launcher helper respecting browser settings
    def open_web(url):
        if pref_browser == "chrome":
            try:
                # Try launching Chrome directly on Windows
                subprocess.Popen(["chrome", url], shell=True)
                return True
            except Exception:
                pass
        elif pref_browser == "edge":
            try:
                subprocess.Popen(["msedge", url], shell=True)
                return True
            except Exception:
                pass
        # Fallback to default browser
        webbrowser.open(url)
        return True

    # 1. ChatGPT (Web only)
    if "chatgpt" in app or "chat gpt" in app:
        open_web("https://chatgpt.com")
        return "Opening ChatGPT."

    # 2. Gemini (Web only)
    elif "gemini" in app:
        open_web("https://gemini.google.com")
        return "Opening Gemini."

    # 3. YouTube (Web only)
    elif "youtube" in app:
        open_web("https://youtube.com")
        return "Opening YouTube."

    # 4. WhatsApp
    elif "whatsapp" in app:
        local_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "WhatsApp.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "WhatsApp", "WhatsApp.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "WhatsApp", "WhatsApp.exe")
        ]
        
        # Check if local WhatsApp binary exists
        launched = False
        for path in local_paths:
            if path and os.path.exists(path):
                subprocess.Popen([path])
                launched = True
                break
                
        if launched:
            return "Opening WhatsApp."
        else:
            open_web("https://web.whatsapp.com")
            return "App not found. Opening web version."

    # 5. Spotify
    elif "spotify" in app:
        local_paths = [
            os.path.join(os.environ.get("APPDATA", ""), "Spotify", "Spotify.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "Spotify.exe")
        ]
        
        launched = False
        for path in local_paths:
            if path and os.path.exists(path):
                subprocess.Popen([path])
                launched = True
                break
                
        if launched:
            return "Opening Spotify."
        else:
            open_web("https://open.spotify.com")
            return "App not found. Opening web version."

    # 6. Antigravity IDE
    elif "antigravity" in app:
        ide_path = cfg.get("antigravity_path", "")
        if not ide_path or not os.path.exists(ide_path):
            return "Please set app path in settings."
        try:
            subprocess.Popen([ide_path])
            return "Opening Antigravity IDE."
        except Exception as e:
            print(f"Error launching Antigravity IDE: {e}")
            return "Failed to open Antigravity IDE from set path."

    # Fallback to generic system action
    return None
