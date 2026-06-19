import base64
import os
import time
from datetime import datetime
import pyautogui
import pygetwindow as gw
from openai import OpenAI
from config import OPENAI_API_KEY

def encode_image(image_path: str) -> str:
    """Encodes a local file as base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def capture_screen(output_path: str = None) -> str:
    """Takes a full screen screenshot and returns the file path."""
    folder = os.path.join(os.environ["USERPROFILE"], "Pictures", "Screenshots")
    os.makedirs(folder, exist_ok=True)
    if not output_path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = os.path.join(folder, f"Screen_{timestamp}.png")
    
    screenshot = pyautogui.screenshot()
    screenshot.save(output_path)
    return output_path

def capture_active_window() -> str:
    """Captures the active foreground window, crops to its bounding box, and saves it."""
    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            x = rect[0]
            y = rect[1]
            w = rect[2] - x
            h = rect[3] - y
            
            # Avoid invalid dimensions
            if w > 0 and h > 0:
                screenshot = pyautogui.screenshot(region=(x, y, w, h))
                folder = os.path.join(os.environ["USERPROFILE"], "Pictures", "Screenshots")
                os.makedirs(folder, exist_ok=True)
                path = os.path.join(folder, f"ActiveWin_{int(time.time())}.png")
                screenshot.save(path)
                return path
    except Exception as e:
        print(f"Error capturing foreground window: {e}")
    # Fallback to full screen
    return capture_screen()

def capture_window_by_title(title_query: str) -> str:
    """Finds a window by title, activates it, crops to its coordinates, and saves the image."""
    try:
        windows = gw.getWindowsWithTitle(title_query)
        if windows:
            win = windows[0]
            try:
                win.activate()
            except Exception:
                pass  # Ignore if already focused or error focusing
            time.sleep(0.3)
            
            screenshot = pyautogui.screenshot(region=(win.left, win.top, win.width, win.height))
            folder = os.path.join(os.environ["USERPROFILE"], "Pictures", "Screenshots")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"Win_{win.title[:15].replace(' ', '_')}_{int(time.time())}.png")
            screenshot.save(path)
            return path
    except Exception as e:
        print(f"Failed to capture window by title: {e}")
    return None

def analyze_image_with_ai(image_path: str, prompt: str) -> str:
    """Uses GPT-4o-mini vision model to analyze a screenshot based on the prompt."""
    if not OPENAI_API_KEY:
        return "I can't access vision analysis capabilities because your OpenAI API key is not configured."
        
    if not os.path.exists(image_path):
        return f"Screenshot file {image_path} could not be found."
        
    try:
        base64_image = encode_image(image_path)
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Vision API call failed: {e}"

def analyze_screen_error() -> str:
    """Captures the screen and asks the model to identify and debug any visible error messages."""
    path = capture_active_window()
    prompt = "Look at this screenshot and identify any error messages, crashes, tracebacks, or bugs. Explain what is causing the error and how to fix it."
    return analyze_image_with_ai(path, prompt)

def explain_screen_code() -> str:
    """Captures the screen and asks the model to explain any visible code on screen."""
    path = capture_active_window()
    prompt = "Look at this screenshot, identify any visible source code or terminal commands, and explain what the code is doing."
    return analyze_image_with_ai(path, prompt)

def analyze_ui_layout() -> str:
    """Captures screen and audits the GUI/UI elements for visual bugs or formatting issues."""
    path = capture_active_window()
    prompt = "Look at this screenshot and evaluate its user interface layout. Identify any overlapping text, broken elements, misalignment, or design flaws."
    return analyze_image_with_ai(path, prompt)
