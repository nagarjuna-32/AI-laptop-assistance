import pyttsx3
import db
import pythoncom

def get_engine():
    """Initializes and returns a thread-safe TTS engine configured with the female voice."""
    pythoncom.CoInitialize()
    engine = pyttsx3.init()
    try:
        voices = engine.getProperty("voices")
        for v in voices:
            name = v.name.lower()
            if "zira" in name or "hazel" in name or "female" in name or "heera" in name:
                engine.setProperty("voice", v.id)
                break
        else:
            if len(voices) > 1:
                engine.setProperty("voice", voices[1].id)
    except Exception as e:
        print(f"Error selecting female voice: {e}")
    return engine

def speak(text):
    print("Chinni:", text)
    try:
        engine = get_engine()
        # Load user voice preferences dynamically
        rate = int(db.get_setting("voice_rate", "170"))
        volume = float(db.get_setting("voice_volume", "1.0"))
        
        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)
        
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS speak error: {e}")

def test_speak(text, rate, volume):
    try:
        engine = get_engine()
        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS test speak error: {e}")
