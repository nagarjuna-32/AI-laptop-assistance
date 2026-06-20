from listener import listen
from speaker import speak
from ai import ask_ai
from memory import remember, show_memory
import system_actions
from system_actions import open_app, control_volume, control_brightness, close_app, lock_screen, suspend_pc, shutdown_pc, manage_file_folder
from web_actions import google_search, youtube_play
from whatsapp import send_whatsapp
from gui import JarvisGUI
from threading import Thread
import db
import intent
import app_finder
import mic_manager
import tray_service
import queue
import sys
import os
import subprocess
from datetime import datetime
import time

# Thread-safe command queue
command_queue = queue.Queue()
is_listening_enabled = True

def set_listening_enabled(enabled):
    global is_listening_enabled
    is_listening_enabled = enabled
    print(f"Background listener status changed: {is_listening_enabled}")

def get_startup_greeting() -> str:
    now = datetime.now()
    hr = now.hour
    time_greeting = "Good morning" if 5 <= hr < 12 else ("Good afternoon" if 12 <= hr < 17 else "Good evening")
    return f"Welcome back Arjun. Chinni is online and listening. {time_greeting}."

def is_yes(text: str) -> bool:
    cleaned = intent.clean_text(text)
    return any(w in cleaned for w in ["yes", "confirm", "proceed", "yeah", "sure", "ok", "go ahead", "yep", "do it"])

def is_no(text: str) -> bool:
    cleaned = intent.clean_text(text)
    return any(w in cleaned for w in ["no", "cancel", "stop", "dont", "do not", "never mind", "nope", "cancel it"])

def execute_command(res: dict, raw_data: str):
    intent_name = res["intent"]
    cmd = res["command"]
    target = res["target"]
    
    # Safety Check: OS Access setup confirmation rule
    allowed = db.get_setting("os_access_allowed", "0")
    if allowed == "0" and intent_name not in ["ASK_AI", "SYSTEM_INFO"]:
        speak("Please allow system control access in the popup dialog first.")
        return

    # 1. Custom command sequence execution
    if intent_name == "CUSTOM_COMMAND":
        actions = db.get_custom_command_by_phrase(target)
        if actions:
            # speak(f"{target.title()} activated.")
            for a in actions:
                command_queue.put(("manual", a))

    # 2. Window operations
    elif intent_name == "WINDOW_ACTION":
        if cmd == "minimize":
            system_actions.minimize_active_window()
        elif cmd == "maximize":
            system_actions.maximize_active_window()
        elif cmd == "switch":
            system_actions.switch_window(target)

    # 3. Screen operations
    elif intent_name == "SCREEN_ACTION":
        if cmd == "screenshot":
            path = system_actions.take_screenshot()
            db.add_action_log(raw_data, "SCREEN_ACTION", f"Captured screenshot to {path}", "executed")
        elif cmd == "record":
            system_actions.trigger_screen_recording()

    # 4. File actions
    elif intent_name == "FILE_ACTION":
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        
        if cmd == "create":
            response = manage_file_folder(f"create {target}")
            # speak(response)
        elif cmd in ["delete", "remove"]:
            response = manage_file_folder(f"delete {target}")
            # speak(response)
        elif cmd == "copy":
            path = os.path.join(desktop, target)
            if not os.path.exists(path):
                for f in os.listdir(desktop):
                    if target.lower() in f.lower():
                        path = os.path.join(desktop, f)
                        break
            if os.path.exists(path):
                system_actions.copy_item(path)
                # speak(f"Copied {os.path.basename(path)} to clipboard.")
        elif cmd == "paste":
            response = system_actions.paste_item(desktop)
            # speak(response)
        elif cmd == "rename":
            parts = target.split(" to ")
            if len(parts) == 2:
                old_name, new_name = parts[0].strip(), parts[1].strip()
                path = os.path.join(desktop, old_name)
                if not os.path.exists(path):
                    for f in os.listdir(desktop):
                        if old_name.lower() in f.lower():
                            path = os.path.join(desktop, f)
                            break
                if os.path.exists(path):
                    response = system_actions.rename_item(path, new_name)
                    # speak(response)
        elif cmd == "zip":
            path = os.path.join(desktop, target)
            if not os.path.exists(path):
                for f in os.listdir(desktop):
                    if target.lower() in f.lower():
                        path = os.path.join(desktop, f)
                        break
            if os.path.exists(path):
                response = system_actions.zip_item(path)
                # speak(response)
        elif cmd in ["unzip", "extract"]:
            path = os.path.join(desktop, target)
            if not os.path.exists(path):
                for f in os.listdir(desktop):
                    if target.lower() in f.lower() and f.endswith(".zip"):
                        path = os.path.join(desktop, f)
                        break
            if os.path.exists(path):
                response = system_actions.extract_zip(path)
                # speak(response)

    # 5. Open Apps / Website Launcher
    elif intent_name == "OPEN_APP":
        app_name = target.lower().strip()
        
        # Check dynamic database lookup first
        app_info = db.get_app_path(target)
        if app_info and (app_info["executable_path"] or app_info["web_fallback"]):
            exe_path = app_info["executable_path"]
            web_fallback = app_info["web_fallback"]
            if exe_path and os.path.exists(exe_path):
                subprocess.Popen([exe_path], shell=True)
                # speak(f"Opening {target}.")
            elif web_fallback:
                # speak(f"Opening {target} in default browser.")
                app_finder.open_default_web(web_fallback)
            else:
                # speak(f"Set path or fallback in preferences for {target}.")
                gui.show_page("settings")
                
        # Fallbacks for popular defaults
        elif "chatgpt" in app_name:
            # speak("Opening ChatGPT in default browser.")
            app_finder.open_default_web("https://chatgpt.com")
        elif "gemini" in app_name:
            # speak("Opening Gemini in default browser.")
            app_finder.open_default_web("https://gemini.google.com")
        elif "youtube" in app_name:
            # speak("Opening YouTube in default browser.")
            app_finder.open_default_web("https://youtube.com")
        elif "whatsapp" in app_name:
            local_paths = [
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "WhatsApp.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "WhatsApp", "WhatsApp.exe"),
                os.path.join(os.environ.get("ProgramFiles", ""), "WhatsApp", "WhatsApp.exe")
            ]
            launched = False
            for p in local_paths:
                if p and os.path.exists(p):
                    subprocess.Popen([p])
                    # speak("Opening WhatsApp.")
                    launched = True
                    break
            if not launched:
                # speak("App not found. Opening web version.")
                app_finder.open_default_web("https://web.whatsapp.com")
        elif "spotify" in app_name:
            local_paths = [
                os.path.join(os.environ.get("APPDATA", ""), "Spotify", "Spotify.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "Spotify.exe")
            ]
            launched = False
            for p in local_paths:
                if p and os.path.exists(p):
                    subprocess.Popen([p])
                    # speak("Opening Spotify.")
                    launched = True
                    break
            if not launched:
                # speak("App not found. Opening web version.")
                app_finder.open_default_web("https://open.spotify.com")
        elif "antigravity" in app_name:
            ide_path = app_finder.find_antigravity_ide()
            if ide_path and os.path.exists(ide_path):
                subprocess.Popen([ide_path], shell=True)
                # speak("Opening Antigravity IDE.")
            else:
                # speak("Please set Antigravity IDE executable path in settings.")
                gui.show_page("settings")
        else:
            open_app(target)

    # 6. Close App
    elif intent_name == "CLOSE_APP":
        if cmd == "close_mode":
            if target == "study mode":
                close_app("chatgpt")
                close_app("youtube")
                close_app("whatsapp")
                close_app("chrome")
                close_app("browser")
            elif target == "coding mood":
                close_app("gemini")
                close_app("chatgpt")
                close_app("antigravity")
                close_app("spotify")
                close_app("chrome")
                close_app("browser")
            elif target == "placement mode":
                close_app("resume")
                close_app("linkedin")
                close_app("chatgpt")
                close_app("interview dashboard")
                close_app("chrome")
                close_app("browser")
            elif target == "project mode":
                close_app("aiplacement")
                close_app("portfolio")
                close_app("full stack projects")
                close_app("internship tasks")
                close_app("chrome")
                close_app("browser")
        else:
            close_app(target)
            
    # 7. Play YouTube
    elif intent_name == "PLAY_YOUTUBE":
        youtube_play(target)
        
    # 8. Web Search
    elif intent_name == "SEARCH_WEB":
        app_finder.open_default_web(f"https://www.google.com/search?q={target}")
        
    # 9. System Settings Control
    elif intent_name == "SYSTEM_SETTING":
        if cmd == "delete":
            manage_file_folder(f"delete {target}")
        elif cmd == "create":
            manage_file_folder(f"create {target}")
        elif cmd == "theme_dark":
            system_actions.set_dark_mode(True)
        elif cmd == "theme_light":
            system_actions.set_dark_mode(False)
        elif cmd == "wifi_on":
            system_actions.set_wifi_state(True)
        elif cmd == "wifi_off":
            system_actions.set_wifi_state(False)
        elif cmd.startswith("turn "):
            state = "On" if "on" in cmd else "Off"
            try:
                subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", "toggle_bluetooth.ps1", "-BluetoothStatus", state],
                    capture_output=True,
                    text=True
                )
            except Exception:
                pass
        elif cmd == "volume up":
            control_volume("up")
        elif cmd == "volume down":
            control_volume("down")
        elif cmd == "brightness up":
            control_brightness("up")
        elif cmd == "brightness down":
            control_brightness("down")
        elif cmd == "shutdown":
            shutdown_pc(restart=False)
        elif cmd == "restart":
            shutdown_pc(restart=True)
        elif cmd in ["sleep", "suspend"]:
            suspend_pc()
        elif cmd == "lock":
            lock_screen()
            
    # 10. Messages (Dangerous)
    elif intent_name == "SEND_MESSAGE":
        import re
        nums = re.findall(r'\b\+?\d{10,12}\b', target)
        if nums:
            number = nums[0]
            message = target
            for n in nums:
                message = message.replace(n, "")
            message = message.replace("send message to", "").replace("message to", "").replace("send message", "").replace("saying", "").replace("whatsapp", "").strip()
            if not message:
                message = "Hello from Chinni"
            send_whatsapp(number, message)
            
    # 11. Calls (Dangerous)
    elif intent_name == "MAKE_CALL":
        os.system("start ms-phone:")
        
    # 12. Create Notes
    elif intent_name == "CREATE_NOTE":
        db.add_note("Voice Note", target)
        gui.refresh_notes_ui()
        
    # 13. AI Chatbot
    elif intent_name == "ASK_AI":
        speak("Thinking...")
        answer = ask_ai(target)
        speak(answer)
        
    # 14. System Info (Time / Date)
    elif intent_name == "SYSTEM_INFO":
        now = datetime.now()
        if cmd == "time":
            time_str = now.strftime("%I:%M %p")
            speak(f"Arjun, the time is {time_str}.")
        elif cmd == "date":
            date_str = now.strftime("%B %d, %Y")
            speak(f"Arjun, today's date is {date_str}.")

# Main orchestrator loop
def jarvis_loop():
    # Speak startup greeting once
    greeting = get_startup_greeting()
    gui.update_intent_details({
        "heard": "System Startup",
        "intent": "STARTUP_GREETING",
        "target": "Arjun",
        "confidence": 100,
        "preview": greeting
    })
    speak(greeting)
    
    gui.start_listening()
    
    current_state = "idle" # idle, confirming, clarifying
    pending_action = None
    
    while True:
        try:
            source, data = command_queue.get()
            
            if data and data.lower().strip() in ["exit", "goodbye", "close chinni", "close assistant"]:
                speak("Goodbye Arjun.")
                gui.root.quit()
                sys.exit()
                
            # Wake word filtering
            wake_enabled = db.get_setting("wake_command_enabled", "0") == "1"
            if source == "voice" and wake_enabled and current_state == "idle":
                wake_words = ["hey chinni", "chinni", "hey aegis", "aegis"]
                matched_wake = None
                for w in wake_words:
                    if data.lower().startswith(w):
                        matched_wake = w
                        break
                if matched_wake:
                    data = data[len(matched_wake):].strip()
                    if not data:
                        speak("Yes Arjun?")
                        continue
                else:
                    print(f"Wake word filter: Ignored command '{data}'")
                    continue
                    
            if current_state == "idle":
                if source in ["voice", "manual"]:
                    cleaned = intent.clean_text(data)
                    if not cleaned:
                        continue
                        
                    res = intent.detectIntent(cleaned)
                    intent_name = res["intent"]
                    cmd = res["command"]
                    target = res["target"]
                    confidence = res["confidence"]
                    
                    auto_exec = db.get_setting("auto_execute_safe", "1") == "1"
                    needs_confirm = res["needsConfirmation"] or not auto_exec
                    if intent_name == "CUSTOM_COMMAND":
                        needs_confirm = False
                        
                    clarification = res.get("clarification", "")
                    
                    # Previews
                    preview = ""
                    if intent_name == "OPEN_APP":
                        preview = f"Open {target}"
                    elif intent_name == "CLOSE_APP":
                        preview = f"Close {target}"
                    elif intent_name == "PLAY_YOUTUBE":
                        preview = f"Play '{target}' on YouTube"
                    elif intent_name == "SEARCH_WEB":
                        preview = f"Search Google for '{target}'"
                    elif intent_name == "SYSTEM_SETTING":
                        preview = f"Perform system action: {cmd} {target}"
                    elif intent_name == "WINDOW_ACTION":
                        preview = f"Adjust Window: {cmd} {target}"
                    elif intent_name == "SCREEN_ACTION":
                        preview = f"Screen Utility: {cmd} {target}"
                    elif intent_name == "FILE_ACTION":
                        preview = f"File Operation: {cmd} {target}"
                    elif intent_name == "SEND_MESSAGE":
                        preview = f"Send WhatsApp message"
                    elif intent_name == "MAKE_CALL":
                        preview = f"Call {target}"
                    elif intent_name == "CREATE_NOTE":
                        preview = f"Remember note: {target}"
                    elif intent_name == "ASK_AI":
                        preview = f"Ask AI: {target}"
                    elif intent_name == "SYSTEM_INFO":
                        preview = f"Get local system {target}"
                    elif intent_name == "CUSTOM_COMMAND":
                        preview = f"Run custom sequence: {target}"
                    else:
                        preview = f"Clarification required: {target}"
                        
                    gui.update_intent_details({
                        "heard": data,
                        "intent": intent_name,
                        "target": target,
                        "confidence": confidence,
                        "preview": preview
                    })
                    
                    # 1. Clarification check
                    if intent_name == "UNKNOWN" or confidence < 80:
                        prompt_text = clarification if clarification else f"I heard: '{data}'. Did you mean something else?"
                        speak(prompt_text)
                        
                        current_state = "clarifying"
                        pending_action = {
                            "intent": intent_name,
                            "command": cmd,
                            "target": target,
                            "preview": preview,
                            "raw": data,
                            "clarification": prompt_text
                        }
                        gui.set_waiting_for_confirmation(True)
                        gui.update_status("Waiting for clarification...")
                        
                    # 2. Confirmation check
                    elif needs_confirm:
                        speak(f"Are you sure you want to {preview}?")
                        
                        current_state = "confirming"
                        pending_action = {
                            "intent": intent_name,
                            "command": cmd,
                            "target": target,
                            "preview": preview,
                            "raw": data
                        }
                        gui.set_waiting_for_confirmation(True)
                        gui.update_status("Waiting for confirmation...")
                        
                    # 3. Direct execution
                    else:
                        gui.update_status(f"Executing: {preview}")
                        execute_command(res, data)
                        db.add_action_log(data, intent_name, preview, "executed")
                        gui.refresh_history_ui()
                        gui.update_status("Online & Idle")
                        
            elif current_state == "confirming":
                if source == "gui_confirm" or (source == "voice" and is_yes(data)):
                    gui.update_status(f"Executing: {pending_action['preview']}")
                    res = {
                        "intent": pending_action["intent"],
                        "command": pending_action["command"],
                        "target": pending_action["target"]
                    }
                    execute_command(res, pending_action["raw"])
                    db.add_action_log(pending_action["raw"], pending_action["intent"], pending_action["preview"], "executed")
                    
                    current_state = "idle"
                    pending_action = None
                    gui.set_waiting_for_confirmation(False)
                    gui.refresh_history_ui()
                    gui.update_status("Online & Idle")
                    
                elif source == "gui_cancel" or (source == "voice" and is_no(data)):
                    speak("Action cancelled.")
                    db.add_action_log(pending_action["raw"], pending_action["intent"], pending_action["preview"], "cancelled")
                    
                    current_state = "idle"
                    pending_action = None
                    gui.set_waiting_for_confirmation(False)
                    gui.refresh_history_ui()
                    gui.update_status("Online & Idle")
                    
                elif source == "manual":
                    speak("Confirmation cancelled. Processing new command.")
                    db.add_action_log(pending_action["raw"], pending_action["intent"], pending_action["preview"], "cancelled")
                    
                    current_state = "idle"
                    pending_action = None
                    gui.set_waiting_for_confirmation(False)
                    gui.refresh_history_ui()
                    command_queue.put(("manual", data))
                    
                elif source == "voice":
                    speak(f"Please say Yes or No to confirm: {pending_action['preview']}.")
                    
            elif current_state == "clarifying":
                if source == "manual":
                    speak("Clarification cancelled. Processing new command.")
                    db.add_action_log(pending_action["raw"], pending_action["intent"], pending_action["preview"], "cancelled")
                    
                    current_state = "idle"
                    pending_action = None
                    gui.set_waiting_for_confirmation(False)
                    gui.refresh_history_ui()
                    command_queue.put(("manual", data))
                    
                elif source == "gui_cancel" or (source == "voice" and is_no(data)):
                    speak("Action cancelled.")
                    db.add_action_log(pending_action["raw"], pending_action["intent"], pending_action["preview"], "cancelled")
                    
                    current_state = "idle"
                    pending_action = None
                    gui.set_waiting_for_confirmation(False)
                    gui.refresh_history_ui()
                    gui.update_status("Online & Idle")
                    
                elif source == "gui_confirm" or (source == "voice" and is_yes(data)):
                    if pending_action["clarification"] == "Do you want me to open Chrome or search music?":
                        speak("Please clarify by saying: Open Chrome, or Search Music.")
                    else:
                        gui.update_status(f"Executing: {pending_action['preview']}")
                        res = {
                            "intent": pending_action["intent"],
                            "command": pending_action["command"],
                            "target": pending_action["target"]
                        }
                        execute_command(res, pending_action["raw"])
                        db.add_action_log(pending_action["raw"], pending_action["intent"], pending_action["preview"], "executed")
                        
                        current_state = "idle"
                        pending_action = None
                        gui.set_waiting_for_confirmation(False)
                        gui.refresh_history_ui()
                        gui.update_status("Online & Idle")
                        
                elif source == "voice":
                    cleaned_voice = intent.clean_text(data)
                    if "chrome" in cleaned_voice:
                        speak("Opening Chrome.")
                        open_app("chrome")
                        db.add_action_log(pending_action["raw"], "OPEN_APP", "Open Chrome", "executed")
                        current_state = "idle"
                        pending_action = None
                        gui.set_waiting_for_confirmation(False)
                        gui.refresh_history_ui()
                        gui.update_status("Online & Idle")
                    elif "music" in cleaned_voice or "search" in cleaned_voice or "play" in cleaned_voice:
                        speak("Playing music.")
                        youtube_play("music")
                        db.add_action_log(pending_action["raw"], "PLAY_YOUTUBE", "Play music on YouTube", "executed")
                        current_state = "idle"
                        pending_action = None
                        gui.set_waiting_for_confirmation(False)
                        gui.refresh_history_ui()
                        gui.update_status("Online & Idle")
                    else:
                        speak("Processing new command.")
                        db.add_action_log(pending_action["raw"], pending_action["intent"], pending_action["preview"], "cancelled")
                        current_state = "idle"
                        pending_action = None
                        gui.set_waiting_for_confirmation(False)
                        gui.refresh_history_ui()
                        command_queue.put(("voice", data))
                        
        except Exception as e:
            print(f"Error in Chinni orchestrator loop: {e}")

# Speech listener thread
def voice_listener_thread():
    try:
        last_mic_name = mic_manager.get_active_mic_name()
    except Exception:
        last_mic_name = "Unknown Microphone"
        
    while True:
        # Check active mic changes in between recording cycles
        try:
            current_mic_name = mic_manager.get_active_mic_name()
            if current_mic_name != last_mic_name:
                print(f"Microphone shifted: {last_mic_name} -> {current_mic_name}")
                last_mic_name = current_mic_name
                gui.sync_dashboard_mic_info()
                speak(f"Microphone switched to {current_mic_name}")
        except Exception as e:
            print(f"Mic switch monitor error: {e}")

        text = listen()
        if text:
            if is_listening_enabled:
                command_queue.put(("voice", text))
            else:
                print(f"Mic muted, skipped input: {text}")

def on_confirm():
    command_queue.put(("gui_confirm", None))

def on_cancel():
    command_queue.put(("gui_cancel", None))

def on_manual_submit(text):
    command_queue.put(("manual", text))

def restore_window():
    gui.root.deiconify()
    gui.root.state('normal')

if __name__ == "__main__":
    gui = JarvisGUI()
    
    gui.on_confirm_callback = on_confirm
    gui.on_cancel_callback = on_cancel
    gui.on_manual_submit_callback = on_manual_submit
    gui.on_toggle_listening_callback = set_listening_enabled
    
    # Initialize native win32 system tray
    tray_service.start_tray_service(
        title="Chinni AI OS",
        icon_path=None,
        on_quit=gui.quit_app,
        on_restore=restore_window
    )
    
    # Delayed background startup thread launch to avoid PyAudio/PortAudio DLL conflicts
    def start_services():
        Thread(target=jarvis_loop, daemon=True).start()
        Thread(target=voice_listener_thread, daemon=True).start()
        print("Chinni background service threads active.")
        
    gui.root.after(2000, start_services)
    gui.sync_dashboard_mic_info()
    
    gui.run()

