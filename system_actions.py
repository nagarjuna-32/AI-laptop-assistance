import os
import shutil
import subprocess
import pyautogui
import screen_brightness_control as sbc
import ctypes
import psutil
from datetime import datetime
import win32gui
import win32con
import win32process
import winreg

# Module level clipboard simulation
copied_item_path = None

def _start(target: str) -> None:
    """Start a Windows app reliably.

    - If target is a known executable name, we try to run it.
    - If it's a command, we use shell=True fallback.
    """
    exe = target.split()[0]
    if shutil.which(exe):
        subprocess.Popen([target], shell=True)
        return
    # Fallback: try using shell
    subprocess.Popen(target, shell=True)


def open_app(command: str) -> bool:
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
        "spotify": ["spotify", "music"],
        "whatsapp": ["whatsapp"],
        "camera": ["camera", "webcam"],
        "youtube": ["youtube", "u tube", "utube"],
        "task manager": ["task manager", "taskmgr"],
        "device manager": ["device manager", "devmgmt"],
        "services": ["services", "services.msc"],
        "registry editor": ["registry editor", "regedit"],
        "powershell": ["powershell"],
    }

    def match(key: str) -> bool:
        for s in synonyms.get(key, [key]):
            if s in cmd:
                return True
        return False

    # Browser / common apps
    if "chrome" in cmd or "google chrome" in cmd:
        _start("start chrome")
        return True

    if match("camera"):
        _start("start microsoft.windows.camera:")
        return True

    if match("youtube"):
        _start("start https://www.youtube.com")
        return True

    if match("vs code"):
        _start("code")
        return True

    if "notepad" in cmd:
        _start("notepad")
        return True

    if "calculator" in cmd or "calc" in cmd:
        _start("calc")
        return True

    if match("spotify"):
        _start("start spotify:")
        return True

    if match("whatsapp"):
        _start("start whatsapp:")
        return True

    # Windows system apps
    if match("file explorer"):
        _start("explorer shell:MyComputerFolder")
        return True

    if match("settings"):
        _start("start ms-settings:")
        return True

    if match("cmd"):
        _start("start cmd")
        return True

    if match("terminal"):
        _start("start wt")
        return True

    if match("powershell"):
        _start("start powershell")
        return True

    if match("paint"):
        _start("mspaint")
        return True

    if match("control panel"):
        _start("control")
        return True

    if match("task manager"):
        _start("taskmgr")
        return True

    if match("device manager"):
        _start("devmgmt.msc")
        return True

    if match("services"):
        _start("services.msc")
        return True

    if match("registry editor"):
        _start("regedit")
        return True

    # Special folders
    for fld in ["downloads", "documents", "desktop", "screenshots"]:
        if fld in cmd:
            open_special_folder(fld)
            return True

    # Check if a folder exists on the Desktop matching the remaining words
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    words_to_remove = {"open", "folder", "directory", "the", "named", "called", "a", "d", "name", "card"}
    cmd_words = cmd.split()
    cleaned_words = [w for w in cmd_words if w not in words_to_remove]
    
    name = "_".join(cleaned_words)
    name_spaces = " ".join(cleaned_words)
    
    for n in [name, name_spaces]:
        if n:
            path = os.path.join(desktop, n)
            if os.path.exists(path) and os.path.isdir(path):
                os.startfile(path)
                return True

    return False


def control_volume(action):
    if action == "up":
        pyautogui.press("volumeup")
    elif action == "down":
        pyautogui.press("volumedown")


def control_brightness(action):
    try:
        current = sbc.get_brightness()[0]
        if action == "up":
            sbc.set_brightness(min(current + 10, 100))
        elif action == "down":
            sbc.set_brightness(max(current - 10, 0))
    except Exception as e:
        print(f"Error adjusting brightness: {e}")


def close_app(command: str) -> bool:
    target = command.lower().replace("close", "").strip()
    if not target:
        return False
        
    words_to_remove = {"the", "folder", "directory", "a", "an", "named", "called", "app", "application", "window"}
    target_words = target.split()
    cleaned_words = [w for w in target_words if w not in words_to_remove]
    target_clean = " ".join(cleaned_words)
    if not target_clean:
        target_clean = target
    
    synonyms = {
        "vs code": ["code", "visual studio code", "vscode"],
        "chrome": ["chrome", "google chrome"],
        "notepad": ["notepad"],
        "calculator": ["calc", "calculator"],
        "spotify": ["spotify"],
        "whatsapp": ["whatsapp"],
        "cmd": ["cmd", "command prompt"],
        "terminal": ["wt", "windows terminal"],
        "paint": ["mspaint", "paint"],
    }
    
    closed_any = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            match = False
            if target_clean == proc_name or target_clean + ".exe" == proc_name or target == proc_name or target + ".exe" == proc_name:
                match = True
            else:
                for key, syns in synonyms.items():
                    if target_clean == key or target_clean in syns or target == key or target in syns:
                        if any(s in proc_name for s in syns):
                            match = True
                            break
            if match:
                proc.terminate()
                closed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    if not closed_any:
        try:
            import pygetwindow as gw
            windows = []
            for win in gw.getAllWindows():
                if win.title and target_clean.lower() in win.title.lower():
                    windows.append(win)
            if windows:
                for win in windows:
                    win.close()
                closed_any = True
        except Exception:
            pass

    return closed_any


def lock_screen() -> None:
    ctypes.windll.user32.LockWorkStation()


def suspend_pc() -> None:
    ctypes.windll.powrprof.SetSuspendState(0, 1, 0)


def shutdown_pc(restart: bool = False) -> None:
    flag = "/r" if restart else "/s"
    os.system(f"shutdown {flag} /t 5")


# ----------------- WINDOW MANAGEMENT -----------------
def minimize_active_window() -> bool:
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        return True
    return False


def maximize_active_window() -> bool:
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        return True
    return False


def switch_window(title_query: str) -> bool:
    def enum_windows_callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title_query.lower() in title.lower():
                extra.append(hwnd)
        return True
    
    hwnds = []
    win32gui.EnumWindows(enum_windows_callback, hwnds)
    if hwnds:
        hwnd = hwnds[0]
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            # Fallback in case of focus restriction
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            return True
    return False


# ----------------- DIRECTORY SHORTCUTS -----------------
def open_special_folder(folder_name: str) -> bool:
    user_profile = os.environ["USERPROFILE"]
    paths = {
        "downloads": os.path.join(user_profile, "Downloads"),
        "documents": os.path.join(user_profile, "Documents"),
        "desktop": os.path.join(user_profile, "Desktop"),
        "screenshots": os.path.join(user_profile, "Pictures", "Screenshots")
    }
    path = paths.get(folder_name.lower())
    if path:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        os.startfile(path)
        return True
    return False


# ----------------- FILE OPERATIONS -----------------
def copy_item(src_path: str) -> bool:
    global copied_item_path
    if os.path.exists(src_path):
        copied_item_path = src_path
        return True
    return False


def paste_item(dest_dir: str) -> str:
    global copied_item_path
    if not copied_item_path or not os.path.exists(copied_item_path):
        return "No copied files or folders in clipboard."
    
    name = os.path.basename(copied_item_path)
    dest_path = os.path.join(dest_dir, name)
    try:
        if os.path.isdir(copied_item_path):
            shutil.copytree(copied_item_path, dest_path)
        else:
            shutil.copy2(copied_item_path, dest_path)
        return f"Pasted {name} into {dest_dir}."
    except Exception as e:
        return f"Failed to paste: {e}"


def move_item(src_path: str, dest_dir: str) -> bool:
    if not os.path.exists(src_path) or not os.path.exists(dest_dir):
        return False
    name = os.path.basename(src_path)
    dest_path = os.path.join(dest_dir, name)
    try:
        shutil.move(src_path, dest_path)
        return True
    except Exception:
        return False


def rename_item(old_path: str, new_name: str) -> str:
    if not os.path.exists(old_path):
        return "Source item does not exist."
    dir_name = os.path.dirname(old_path)
    new_path = os.path.join(dir_name, new_name)
    try:
        os.rename(old_path, new_path)
        return f"Renamed to {new_name}."
    except Exception as e:
        return f"Rename failed: {e}"


def zip_item(src_path: str) -> str:
    if not os.path.exists(src_path):
        return "Source item does not exist."
    
    zip_path = src_path + ".zip"
    try:
        if os.path.isdir(src_path):
            shutil.make_archive(src_path, 'zip', src_path)
        else:
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(src_path, os.path.basename(src_path))
        return f"Created zip file at {os.path.basename(zip_path)}."
    except Exception as e:
        return f"Zipping failed: {e}"


def extract_zip(zip_path: str, dest_dir: str = None) -> str:
    if not os.path.exists(zip_path) or not zip_path.endswith(".zip"):
        return "Invalid zip file path."
    if not dest_dir:
        dest_dir = os.path.dirname(zip_path)
    try:
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(dest_dir)
        return f"Extracted contents to {dest_dir}."
    except Exception as e:
        return f"Extraction failed: {e}"


def manage_file_folder(command: str) -> str:
    """Creates or deletes files/folders based on voice instructions."""
    cmd = command.lower().strip()
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    
    is_add = any(w in cmd for w in ["create", "add", "make", "new"])
    is_delete = any(w in cmd for w in ["delete", "remove"])
    
    if not (is_add or is_delete):
        return "I could not understand the file operation."
        
    is_file = "file" in cmd
    is_folder = "folder" in cmd or "directory" in cmd
    
    words_to_remove = {"create", "add", "make", "new", "delete", "remove", "file", "folder", "directory", "a", "an", "the", "named", "name", "called", "also", "with", "as"}
    cmd_words = cmd.split()
    cleaned_words = [w for w in cmd_words if w not in words_to_remove]
    
    name = "_".join(cleaned_words)
    if not name:
        return "Could not determine the file or folder name."
    
    if not is_file and not is_folder:
        if "." in name:
            is_file = True
        else:
            is_folder = True
            
    name = os.path.basename(name)
    path = os.path.join(desktop, name)
    
    if is_add:
        if is_folder:
            try:
                os.makedirs(path, exist_ok=True)
                return f"Created folder {name} on Desktop."
            except Exception:
                return f"Failed to create folder {name}."
        else:
            if "." not in name:
                name += ".txt"
                path += ".txt"
            try:
                with open(path, "w") as f:
                    f.write("")
                return f"Created file {name} on Desktop."
            except Exception:
                return f"Failed to create file {name}."
                
    elif is_delete:
        if not os.path.exists(path):
            return f"The item {name} does not exist on your Desktop."
            
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                return f"Deleted folder {name} from Desktop."
            except Exception:
                return f"Failed to delete folder {name}."
        else:
            try:
                os.remove(path)
                return f"Deleted file {name} from Desktop."
            except Exception:
                return f"Failed to delete file {name}."
    return "File action unrecognized."


# ----------------- SYSTEM SETTINGS -----------------
def set_wifi_state(enabled: bool) -> bool:
    state = "enabled" if enabled else "disabled"
    try:
        subprocess.run(
            f'netsh interface set interface name="Wi-Fi" admin={state}', 
            shell=True, capture_output=True, text=True
        )
        return True
    except Exception:
        return False


def set_dark_mode(enabled: bool) -> bool:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        value = 0 if enabled else 1
        winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
        winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error setting theme registry: {e}")
        return False


# ----------------- SCREEN OPERATIONS -----------------
def take_screenshot() -> str:
    folder = os.path.join(os.environ["USERPROFILE"], "Pictures", "Screenshots")
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"Screenshot_{timestamp}.png"
    path = os.path.join(folder, filename)
    pyautogui.screenshot(path)
    return path


def trigger_screen_recording() -> None:
    # Triggers Xbox Game Bar Recording toggle (Win + Alt + R)
    pyautogui.hotkey('win', 'alt', 'r')




