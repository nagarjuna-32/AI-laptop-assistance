import os
import shutil
import subprocess
import pyautogui
import screen_brightness_control as sbc


def _start(target: str) -> None:
    """Start a Windows app reliably.

    - If target is a known executable name, we try to run it.
    - If it's a command, we use shell=True fallback.
    """
    # If it's an executable present on PATH, start it directly.
    exe = target.split()[0]
    if shutil.which(exe):
        subprocess.Popen([target], shell=True)
        return

    # Fallback: try using shell
    subprocess.Popen(target, shell=True)


def open_app(command: str) -> None:
    cmd = command.lower().strip()

    # Normalize common variations from speech recognition.
    synonyms = {
        "vs code": ["vs code", "vscode", "visual studio code"],
        "file explorer": ["file explorer", "explorer", "windows explorer", "my computer"],
        "settings": ["settings", "windows settings"],
        "cmd": ["command prompt", "cmd", "command"],
        "terminal": ["windows terminal", "terminal"],
        "paint": ["paint", "paint app"],
        "control panel": ["control panel", "control"],
    }

    def match(key: str) -> bool:
        for s in synonyms.get(key, [key]):
            if s in cmd:
                return True
        return False

    # Browser / common apps
    if "chrome" in cmd or "google chrome" in cmd:
        _start("start chrome")
        return

    if match("vs code"):
        # `code` is the usual VSCode CLI after "shell command" setup
        _start("code")
        return

    if "notepad" in cmd:
        _start("notepad")
        return

    if "calculator" in cmd or "calc" in cmd:
        _start("calc")
        return

    # Windows system apps
    if match("file explorer"):
        # Opens Explorer to "This PC".
        _start("explorer shell:MyComputerFolder")
        return

    if match("settings"):
        # Launch Windows Settings app.
        _start("start ms-settings:")
        return

    if match("cmd"):
        _start("start cmd")
        return

    if match("terminal"):
        _start("start wt")
        return

    if match("paint"):
        _start("mspaint")
        return

    if match("control panel"):
        _start("control")
        return

    # If not recognized, do nothing (main.py will go to AI for non-open commands).
    # But for "open" commands, main.py calls open_app() directly.
    # Keep it silent here to avoid circular imports with speaker.


def control_volume(action):
    if action == "up":
        pyautogui.press("volumeup")
    elif action == "down":
        pyautogui.press("volumedown")


def control_brightness(action):
    current = sbc.get_brightness()[0]

    if action == "up":
        sbc.set_brightness(min(current + 10, 100))
    elif action == "down":
        sbc.set_brightness(max(current - 10, 0))

