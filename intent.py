import re
import json
import db

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    text = text.lower().strip()
    
    # Remove leading noise prefixes (including Chinni and Aegis)
    noise_prefixes = [
        r"^please\s+", r"^can you\s+", r"^could you\s+", r"^would you\s+",
        r"^chinni\s+", r"^hey chinni\s+", r"^arjun\s+", r"^hey arjun\s+",
        r"^aegis\s+", r"^hey aegis\s+", r"^jarvis\s+", r"^hey jarvis\s+",
        r"^just\s+", r"^tell me\s+", r"^make a\s+", r"^do a\s+", r"^go to\s+"
    ]
    for pattern in noise_prefixes:
        text = re.sub(pattern, "", text)
        
    replacements = {
        r"\bcoding\s+mode\b": "coding mood",
        r"\bcoding\s+mood\b": "coding mood",
        r"\bstudy\s+mode\b": "study mode",
        r"\bwhats\s+app\b": "whatsapp",
        r"\bwhatsap\b": "whatsapp",
        r"\bwatsep\b": "whatsapp",
        r"\bwhatsup\b": "whatsapp",
        r"\bu\s+tube\b": "youtube",
        r"\butube\b": "youtube",
        r"\byou\s+tube\b": "youtube",
        r"\bcrome\b": "chrome",
        r"\bgrom\b": "chrome",
        r"\bxplorer\b": "file explorer",
        r"\bblue\s+tooth\b": "bluetooth",
        r"\bblutooth\b": "bluetooth",
        r"\bblutut\b": "bluetooth",
        r"\bvscode\b": "vs code",
        r"\bvicode\b": "vs code",
        r"\bspottyfy\b": "spotify",
        r"\bspotty\s+fire\b": "spotify",
        r"\bwaifai\b": "wifi",
        r"\by-fai\b": "wifi",
        r"\bpent\b": "paint",
        r"\bnotpad\b": "notepad",
        r"\bnot\s+pad\b": "notepad",
        r"\bcalcy\b": "calculator",
        r"\bcemra\b": "camera",
        r"\bcamra\b": "camera",
        r"\bkey\s+board\b": "keyboard",
        r"\bfile\s+explorer\b": "file explorer",
        r"\bsettings\b": "settings",
        r"\bcontrol\s+panel\b": "control panel"
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
        
    return text.strip()

def detectIntent(userText: str) -> dict:
    original_text = userText
    cleaned = clean_text(userText)
    
    result = {
        "intent": "UNKNOWN",
        "command": "",
        "target": "",
        "confidence": 50,
        "needsConfirmation": False,
        "clarification": ""
    }
    
    if not cleaned:
        result["clarification"] = "I didn't catch that clearly. Please repeat."
        return result

    # ----------------- PRIORITY 1 & 2: CUSTOM COMMANDS (MACROS & ALIASES) -----------------
    all_enabled_custom = db.get_all_custom_commands()
    
    # 1. Exact Match on trigger_phrase
    for cmd in all_enabled_custom:
        if not cmd["enabled"]:
            continue
        trigger = cmd["trigger_phrase"].lower().strip()
        if cleaned == trigger:
            result["intent"] = "CUSTOM_COMMAND"
            result["command"] = "custom"
            result["target"] = trigger
            result["confidence"] = 100
            result["needsConfirmation"] = False
            return result

    # 2. Similar Custom Command / Alias Match
    prefixes = ["start", "activate", "open", "turn on", "enable", "run", "switch on", "launch"]
    for cmd in all_enabled_custom:
        if not cmd["enabled"]:
            continue
        trigger = cmd["trigger_phrase"].lower().strip()
        
        # Check aliases list
        for alias in cmd["aliases"]:
            alias_clean = alias.lower().strip()
            if cleaned == alias_clean:
                result["intent"] = "CUSTOM_COMMAND"
                result["command"] = "custom"
                result["target"] = trigger
                result["confidence"] = 100
                result["needsConfirmation"] = False
                return result
                
        # Check prefixes + trigger
        for pref in prefixes:
            if cleaned == f"{pref} {trigger}":
                result["intent"] = "CUSTOM_COMMAND"
                result["command"] = "custom"
                result["target"] = trigger
                result["confidence"] = 100
                result["needsConfirmation"] = False
                return result
            # Check prefixes + aliases
            for alias in cmd["aliases"]:
                alias_clean = alias.lower().strip()
                if cleaned == f"{pref} {alias_clean}":
                    result["intent"] = "CUSTOM_COMMAND"
                    result["command"] = "custom"
                    result["target"] = trigger
                    result["confidence"] = 100
                    result["needsConfirmation"] = False
                    return result

    # ----------------- AMBIGUITY / CLARIFICATION CHECK -----------------
    if ("open" in cleaned or "launch" in cleaned or "start" in cleaned) and ("music" in cleaned or "song" in cleaned or "play" in cleaned) and ("chrome" in cleaned or "browser" in cleaned):
        result["intent"] = "UNKNOWN"
        result["command"] = "clarify"
        result["target"] = "open chrome or play music"
        result["confidence"] = 70
        result["needsConfirmation"] = True
        result["clarification"] = "Do you want me to open Chrome or search music?"
        return result

    # ----------------- PRIORITY 3: SYSTEM / APP COMMANDS -----------------
    # Volume control
    if "volume" in cleaned or any(w in cleaned for w in ["louder", "quieter", "mute"]):
        action = "down" if any(w in cleaned for w in ["down", "decrease", "lower", "reduce", "quieter", "mute"]) else "up"
        result["intent"] = "SYSTEM_SETTING"
        result["command"] = "volume " + action
        result["target"] = "Volume"
        result["confidence"] = 95
        result["needsConfirmation"] = False
        return result

    # Brightness control
    if "brightness" in cleaned or any(w in cleaned for w in ["brighter", "dim", "darker"]):
        action = "down" if any(w in cleaned for w in ["down", "decrease", "lower", "reduce", "dim", "darker"]) else "up"
        result["intent"] = "SYSTEM_SETTING"
        result["command"] = "brightness " + action
        result["target"] = "Brightness"
        result["confidence"] = 95
        result["needsConfirmation"] = False
        return result

    # Windows dark / light mode toggle
    if "dark mode" in cleaned or "light mode" in cleaned or "night mode" in cleaned:
        action = "dark" if ("dark" in cleaned or "night" in cleaned) else "light"
        result["intent"] = "SYSTEM_SETTING"
        result["command"] = "theme_" + action
        result["target"] = "Window Theme"
        result["confidence"] = 95
        result["needsConfirmation"] = False
        return result

    # WiFi toggle
    if "wifi" in cleaned or "wi-fi" in cleaned or "internet" in cleaned:
        if any(w in cleaned for w in ["on", "enable", "activate", "start"]):
            cmd = "wifi_on"
        elif any(w in cleaned for w in ["off", "disable", "deactivate", "stop"]):
            cmd = "wifi_off"
        else:
            cmd = "wifi_toggle"
        result["intent"] = "SYSTEM_SETTING"
        result["command"] = cmd
        result["target"] = "WiFi"
        result["confidence"] = 92
        result["needsConfirmation"] = False
        return result

    # Bluetooth toggle
    if "bluetooth" in cleaned:
        state = "on" if any(w in cleaned for w in ["on", "enable", "activate", "start"]) else "off"
        result["intent"] = "SYSTEM_SETTING"
        result["command"] = "turn " + state
        result["target"] = "Bluetooth"
        result["confidence"] = 95
        result["needsConfirmation"] = False
        return result

    # Window minimizing / maximizing / focus switching
    if "minimize" in cleaned:
        result["intent"] = "WINDOW_ACTION"
        result["command"] = "minimize"
        result["target"] = cleaned.replace("minimize", "").strip()
        result["confidence"] = 95
        result["needsConfirmation"] = False
        return result

    if "maximize" in cleaned:
        result["intent"] = "WINDOW_ACTION"
        result["command"] = "maximize"
        result["target"] = cleaned.replace("maximize", "").strip()
        result["confidence"] = 95
        result["needsConfirmation"] = False
        return result

    if "switch to" in cleaned or "focus" in cleaned:
        target = cleaned.replace("switch to", "").replace("focus on", "").replace("focus", "").strip()
        result["intent"] = "WINDOW_ACTION"
        result["command"] = "switch"
        result["target"] = target
        result["confidence"] = 95
        result["needsConfirmation"] = False
        return result

    # Screenshots and recordings
    if "screenshot" in cleaned or "capture screen" in cleaned:
        result["intent"] = "SCREEN_ACTION"
        result["command"] = "screenshot"
        result["target"] = "screenshot"
        result["confidence"] = 95
        result["needsConfirmation"] = False
        return result

    if "record screen" in cleaned or "screen recording" in cleaned:
        result["intent"] = "SCREEN_ACTION"
        result["command"] = "record"
        result["target"] = "recording"
        result["confidence"] = 95
        result["needsConfirmation"] = False
        return result

    # File Operations (copy, paste, move, rename, zip, unzip, create, delete)
    is_file_op = any(w in cleaned for w in ["create", "add", "make", "new", "delete", "remove", "format", "rename", "copy", "paste", "move", "zip", "extract", "unzip"])
    if is_file_op:
        op = "create"
        for o in ["delete", "remove", "format", "rename", "copy", "paste", "move", "zip", "extract", "unzip"]:
            if o in cleaned:
                op = o
                break
        
        result["intent"] = "FILE_ACTION"
        result["command"] = op
        result["target"] = cleaned.replace(op, "").replace("file", "").replace("folder", "").strip()
        result["confidence"] = 90
        
        # Deleting and formatting are dangerous
        if op in ["delete", "remove", "format"]:
            result["needsConfirmation"] = True
        return result

    # PC Power Commands
    power_actions = ["shutdown", "restart", "sleep", "suspend", "lock"]
    for pa in power_actions:
        if pa in cleaned:
            result["intent"] = "SYSTEM_SETTING"
            result["command"] = pa
            result["target"] = "PC PowerState"
            result["confidence"] = 98
            if pa in ["shutdown", "restart"]:
                result["needsConfirmation"] = True
            else:
                result["needsConfirmation"] = False
            return result

    # Close Apps
    close_keywords = ["close", "exit", "quit", "stop", "terminate", "close app"]
    
    # Close Mode shortcut check
    if "close" in cleaned and any(m in cleaned for m in ["study mode", "coding mode", "coding mood", "placement mode", "project mode"]):
        result["intent"] = "CLOSE_APP"
        result["command"] = "close_mode"
        result["target"] = "study mode" if "study" in cleaned else ("coding mood" if "coding" in cleaned else ("placement mode" if "placement" in cleaned else "project mode"))
        result["confidence"] = 98
        result["needsConfirmation"] = False
        return result

    apps = [
        "youtube", "chrome", "spotify", "whatsapp", "vs code", "notepad", 
        "calculator", "file explorer", "settings", "cmd", "terminal", 
        "paint", "control panel", "camera", "notion", "chatgpt", "gemini", "antigravity",
        "task manager", "device manager", "services", "registry editor", "powershell",
        "downloads", "documents", "desktop", "screenshots"
    ]
    matched_close_app = None
    for app in apps:
        if app in cleaned:
            matched_close_app = app
            break
            
    if matched_close_app and (any(cleaned.startswith(kw) for kw in close_keywords) or "close" in cleaned):
        result["intent"] = "CLOSE_APP"
        result["command"] = "close"
        result["target"] = matched_close_app
        result["confidence"] = 95
        return result

    # Open Apps / System Panels
    open_keywords = ["open", "launch", "start", "run", "open the app", "open app"]
    has_open_kw = any(cleaned.startswith(kw) or cleaned.startswith("launch") or cleaned.startswith("start") for kw in open_keywords)
    matched_app = None
    for app in apps:
        if app in cleaned:
            matched_app = app
            break
            
    if matched_app and (has_open_kw or cleaned == matched_app or cleaned.endswith(matched_app)):
        result["intent"] = "OPEN_APP"
        result["command"] = "open"
        app_name_map = {
            "youtube": "YouTube", "chrome": "Chrome", "spotify": "Spotify", "whatsapp": "WhatsApp",
            "vs code": "VS Code", "notepad": "Notepad", "calculator": "Calculator",
            "file explorer": "File Explorer", "settings": "Settings", "cmd": "Command Prompt",
            "terminal": "Windows Terminal", "paint": "Paint", "control panel": "Control Panel",
            "camera": "Camera", "notion": "Notion", "chatgpt": "ChatGPT", "gemini": "Gemini",
            "antigravity": "Antigravity IDE", "task manager": "Task Manager", "device manager": "Device Manager",
            "services": "Services", "registry editor": "Registry Editor", "powershell": "PowerShell",
            "downloads": "Downloads", "documents": "Documents", "desktop": "Desktop", "screenshots": "Screenshots"
        }
        result["target"] = app_name_map.get(matched_app, matched_app)
        result["confidence"] = 95
        
        # Risk check: Raw terminal commands or uninstall actions are dangerous
        risky_apps = ["gpay", "paypal", "pay", "payment", "bank", "uninstall"]
        if any(ra in cleaned for ra in risky_apps):
            result["needsConfirmation"] = True
        return result

    # ----------------- PRIORITY 4: WEB / BROWSER SEARCHES -----------------
    # Play YouTube
    if "play" in cleaned or "youtube" in cleaned:
        query = cleaned.replace("play video", "").replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
        if query:
            result["intent"] = "PLAY_YOUTUBE"
            result["command"] = "play"
            result["target"] = query
            result["confidence"] = 95
            return result

    # Search Web
    if "search" in cleaned or "google" in cleaned or "look up" in cleaned:
        query = cleaned.replace("search for", "").replace("search", "").replace("google", "").replace("look up", "").strip()
        if query:
            result["intent"] = "SEARCH_WEB"
            result["command"] = "search"
            result["target"] = query
            result["confidence"] = 95
            return result

    # ----------------- DANGEROUS CHECKS (MESSAGES / CALLS) -----------------
    if any(w in cleaned for w in ["message", "whatsapp message", "text message", "send message", "msg", "send"]):
        result["intent"] = "SEND_MESSAGE"
        result["command"] = "send_message"
        result["target"] = cleaned
        result["confidence"] = 85
        result["needsConfirmation"] = True
        return result

    if "call" in cleaned:
        result["intent"] = "MAKE_CALL"
        result["command"] = "make_call"
        result["target"] = cleaned.replace("make a call", "").replace("call", "").strip()
        result["confidence"] = 85
        result["needsConfirmation"] = True
        return result

    # ----------------- PRIORITY 5: AI / CHATBOT QUESTIONS -----------------
    # Notes (Safe)
    if any(w in cleaned for w in ["remember", "create note", "write note", "save note", "note down"]):
        result["intent"] = "CREATE_NOTE"
        result["command"] = "remember"
        result["target"] = cleaned.replace("remember that", "").replace("remember", "").replace("create note", "").replace("write note", "").strip()
        result["confidence"] = 90
        result["needsConfirmation"] = False
        return result

    # ----------------- SYSTEM INFO CHECKS (TIME / DATE) -----------------
    if any(w in cleaned for w in ["time", "date", "clock"]):
        if any(w in cleaned for w in ["what", "tell", "current", "today", "now", "get"]):
            result["intent"] = "SYSTEM_INFO"
            result["command"] = "time" if "time" in cleaned or "clock" in cleaned else "date"
            result["target"] = "time" if "time" in cleaned or "clock" in cleaned else "date"
            result["confidence"] = 95
            result["needsConfirmation"] = False
            return result

    ai_questions = ["who", "what", "where", "when", "why", "how", "explain", "tell me", "define", "what's", "is"]
    is_question = any(cleaned.startswith(q) for q in ai_questions) or "?" in original_text
    if is_question or len(cleaned.split()) > 3:
        result["intent"] = "ASK_AI"
        result["command"] = "answer_question"
        result["target"] = original_text
        result["confidence"] = 98
        result["needsConfirmation"] = False
        return result

    # ----------------- PRIORITY 6: FALLBACK TO UNKNOWN -----------------
    result["intent"] = "UNKNOWN"
    result["command"] = "clarify"
    result["target"] = original_text
    result["confidence"] = 40
    result["needsConfirmation"] = True
    result["clarification"] = "I didn't catch that clearly. Please repeat."
    return result

