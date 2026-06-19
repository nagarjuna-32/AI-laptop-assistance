import pyaudio
import db
import threading
from datetime import datetime

# Global lock to prevent PortAudio concurrency crashes
pyaudio_lock = threading.Lock()

def get_input_devices():
    with pyaudio_lock:
        p = pyaudio.PyAudio()
        devices = []
        try:
            info = p.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount', 0)
            for i in range(0, numdevices):
                device_info = p.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels', 0) > 0:
                    devices.append({
                        "index": i,
                        "name": device_info.get('name')
                    })
        except Exception as e:
            print(f"Error querying input devices: {e}")
        finally:
            p.terminate()
        return devices

def get_device_priority_and_type(name: str):
    name_lower = name.lower()
    if "bluetooth" in name_lower:
        return 1, "Bluetooth"
    elif "headset" in name_lower or "headphones" in name_lower or "wired" in name_lower:
        return 2, "Wired Headset"
    elif "realtek" in name_lower:
        return 3, "Realtek Audio"
    else:
        return 4, "Built-in / Other"

def sync_voice_devices():
    devices = get_input_devices()
    db.clear_voice_devices()
    for d in devices:
        priority, dev_type = get_device_priority_and_type(d["name"])
        db.add_voice_device(d["name"], dev_type, priority, selected=0)
    return devices

def get_active_mic():
    # Sync current devices
    devices = sync_voice_devices()
    if not devices:
        return None
        
    # Check if a user selected device is stored and currently active
    manual_selection = db.get_setting("selected_microphone", "")
    if manual_selection:
        for d in devices:
            if d["name"] == manual_selection:
                db.set_selected_device(d["name"])
                return d
                
    # Otherwise select best by priority
    best_device = None
    best_priority = 9999
    
    for d in devices:
        priority, _ = get_device_priority_and_type(d["name"])
        if priority < best_priority:
            best_priority = priority
            best_device = d
            
    if best_device:
        db.set_selected_device(best_device["name"])
        
    return best_device

def get_active_mic_index():
    mic = get_active_mic()
    return mic["index"] if mic else None

def get_active_mic_name():
    mic = get_active_mic()
    return mic["name"] if mic else "No Microphone Detected"

def select_device_by_name(name):
    devices = get_input_devices()
    found = False
    for d in devices:
        if d["name"] == name:
            db.set_setting("selected_microphone", name)
            db.set_selected_device(name)
            found = True
            break
    return found
