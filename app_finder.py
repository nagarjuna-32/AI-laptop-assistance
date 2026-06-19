import os
import db
import webbrowser

def find_antigravity_ide():
    # 1. Check if path is already saved in DB and valid
    path_info = db.get_app_path("Antigravity IDE")
    if path_info and path_info["executable_path"] and os.path.exists(path_info["executable_path"]):
        return path_info["executable_path"]
        
    # 2. Search common locations
    search_roots = [
        os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
        "C:\\Users\\Public\\Desktop",
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
        "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs",
        os.environ.get("PROGRAMFILES", "C:\\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("APPDATA", "")
    ]
    
    # shallow walk scan
    for root in search_roots:
        if not root or not os.path.exists(root):
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                # Restrict depth to 2 folders
                depth = dirpath.replace(root, "").count(os.path.sep)
                if depth > 2:
                    dirnames[:] = [] # stop recursion
                    continue
                    
                for f in filenames:
                    f_lower = f.lower()
                    if "antigravity" in f_lower and (f_lower.endswith(".exe") or f_lower.endswith(".lnk")):
                        full_path = os.path.join(dirpath, f)
                        # Save path
                        db.set_app_path("Antigravity IDE", full_path, "")
                        return full_path
        except Exception:
            pass
            
    return None

def open_default_web(url):
    # Retrieve browser setting
    pref = db.get_setting("browser_pref", "default")
    if pref == "chrome":
        try:
            import subprocess
            subprocess.Popen(["chrome", url], shell=True)
            return True
        except Exception:
            pass
    elif pref == "edge":
        try:
            import subprocess
            subprocess.Popen(["msedge", url], shell=True)
            return True
        except Exception:
            pass
            
    # Default OS browser
    webbrowser.open(url)
    return True
