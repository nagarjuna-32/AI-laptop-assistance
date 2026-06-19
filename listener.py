import speech_recognition as sr
import mic_manager

# Reusable recognizer configured for optimal sensitivity
recognizer = sr.Recognizer()
recognizer.energy_threshold = 150  # Lower base threshold for better sensitivity
recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_damping = 0.15
recognizer.dynamic_energy_ratio = 1.5

last_adjusted_mic = None

def listen():
    global last_adjusted_mic
    index = mic_manager.get_active_mic_index()
    
    with mic_manager.pyaudio_lock:
        source = sr.Microphone(device_index=index)

    try:
        with source as src:
            # Calibrate ambient noise only when mic changes
            if last_adjusted_mic != index:
                print(f"Calibrating mic {index} for ambient noise...")
                recognizer.adjust_for_ambient_noise(src, duration=1.0)
                last_adjusted_mic = index
                print(f"Calibration completed. Threshold set to: {recognizer.energy_threshold}")

            print("Listening... Speak now.")
            audio = recognizer.listen(src, timeout=5, phrase_time_limit=8)
            
    except sr.WaitTimeoutError:
        return ""
    except Exception as e:
        print(f"Audio capture error: {e}")
        return ""

    try:
        # Use en-IN for Indian accent optimization
        text = recognizer.recognize_google(audio, language="en-IN")
        print("You said:", text)
        return text.lower()

    except sr.UnknownValueError:
        return ""

    except sr.RequestError as e:
        print(f"Google speech API request error: {e}")
        return ""

