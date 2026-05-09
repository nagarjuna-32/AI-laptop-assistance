import speech_recognition as sr

MIC_INDEX = 1

def listen():
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    with sr.Microphone(device_index=MIC_INDEX) as source:
        print("Adjusting noise...")
        r.adjust_for_ambient_noise(source, duration=1)

        print("Listening... speak now.")

        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            print("No voice detected.")
            return ""

    try:
        text = r.recognize_google(audio)
        print("You said:", text)
        return text.lower()

    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""

    except sr.RequestError:
        print("Internet issue / Google speech API issue.")
        return ""
