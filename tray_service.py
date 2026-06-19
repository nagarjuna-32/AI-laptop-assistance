import os
import sys
import threading
import win32api
import win32con
import win32gui
import winreg

class TrayService:
    def __init__(self, title, icon_path=None, on_quit=None, on_restore=None):
        self.title = title
        self.icon_path = icon_path
        self.on_quit = on_quit
        self.on_restore = on_restore
        
        self.hwnd = None
        self.notify_id = None
        
        # Register window class for message handling
        message_map = {
            win32con.WM_DESTROY: self.on_destroy,
            win32con.WM_COMMAND: self.on_command,
            win32con.WM_USER + 20: self.on_tray_icon_event
        }
        
        wc = win32gui.WNDCLASS()
        self.hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "ChinniTrayClass"
        wc.lpfnWndProc = message_map
        
        try:
            self.class_atom = win32gui.RegisterClass(wc)
        except Exception:
            pass  # Class already registered
            
        # Create a hidden window for event loop
        self.hwnd = win32gui.CreateWindow(
            "ChinniTrayClass", 
            "Chinni Tray Window", 
            win32con.WS_OVERLAPPED | win32con.WS_SYSMENU, 
            0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 
            0, 0, self.hinst, None
        )
        win32gui.UpdateWindow(self.hwnd)
        
        # Load icon if available, otherwise fallback to default
        if icon_path and os.path.exists(icon_path):
            try:
                icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                self.hicon = win32gui.LoadImage(self.hinst, icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags)
            except Exception:
                self.hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        else:
            self.hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
            
        self.add_icon()
        
    def add_icon(self):
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, self.hicon, self.title)
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        self.notify_id = nid
        
    def show_menu(self):
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1023, "Restore Chinni AI OS")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1024, "Exit")
        
        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        
    def on_tray_icon_event(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_LBUTTONDBLCLK or lparam == win32con.WM_LBUTTONUP:
            if self.on_restore:
                self.on_restore()
        elif lparam == win32con.WM_RBUTTONUP:
            self.show_menu()
        return True
        
    def on_command(self, hwnd, msg, wparam, lparam):
        id_code = win32api.LOWORD(wparam)
        if id_code == 1023:
            if self.on_restore:
                self.on_restore()
        elif id_code == 1024:
            if self.on_quit:
                self.on_quit()
            win32gui.DestroyWindow(self.hwnd)
        return True
        
    def on_destroy(self, hwnd, msg, wparam, lparam):
        if self.notify_id:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self.notify_id)
        win32gui.PostQuitMessage(0)
        return True
        
    def start_loop(self):
        win32gui.PumpMessages()

def start_tray_service(title, icon_path=None, on_quit=None, on_restore=None):
    def run():
        tray = TrayService(title, icon_path, on_quit, on_restore)
        tray.start_loop()
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t

def add_to_startup():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    exe_path = sys.executable
    script_path = os.path.abspath(sys.argv[0])
    command = f'"{exe_path}" "{script_path}"'
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ChinniAI", 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Failed to add startup registry: {e}")
        return False

def remove_from_startup():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "ChinniAI")
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Failed to remove startup registry: {e}")
        return False

def is_startup_enabled():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "ChinniAI")
        winreg.CloseKey(key)
        return True
    except Exception:
        return False
