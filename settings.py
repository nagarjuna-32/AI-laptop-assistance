import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "antigravity_path": "",
    "browser": "default",
    "auto_execute": True
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # Ensure all default keys exist
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        print(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS

def save_settings(settings_dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings_dict, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False
