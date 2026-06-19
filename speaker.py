import pyttsx3
import db

# Initialize TTS Engine
engine = pyttsx3.init()

def select_female_voice():
    try:
        voices = engine.getProperty("voices")
        for v in voices:
            name = v.name.lower()
            if "zira" in name or "hazel" in name or "female" in name or "heera" in name:
                engine.setProperty("voice", v.id)
                return
        # Fallback to second voice if available (often female)
        if len(voices) > 1:
            engine.setProperty("voice", voices[1].id)
    except Exception as e:
        print(f"Error selecting female voice: {e}")

# Select female voice on startup
select_female_voice()

def speak(text):
    print("Chinni:", text)
    try:
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
        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS test speak error: {e}")
