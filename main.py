from listener import listen
from speaker import speak
from ai import ask_ai
from memory import remember, show_memory
from system_actions import open_app, control_volume, control_brightness
from web_actions import google_search, youtube_play
from gui import JarvisGUI
from threading import Thread

gui = JarvisGUI()

def jarvis_loop():
    speak("Jarvis is online")

    while True:
        command = listen()

        if not command:
            continue

        print("Command:", command)
        gui.update_status(command)

        if "open" in command:
            open_app(command)

        elif "search" in command:
            google_search(command.replace("search", ""))

        elif "play" in command:
            youtube_play(command.replace("play", ""))

        elif "volume up" in command:
            control_volume("up")

        elif "volume down" in command:
            control_volume("down")

        elif "brightness up" in command:
            control_brightness("up")

        elif "brightness down" in command:
            control_brightness("down")

        elif "remember" in command:
            remember(command.replace("remember", ""))
            speak("Saved")

        elif "what do you remember" in command:
            speak(show_memory())

        elif "exit" in command:
            speak("Goodbye")
            break

        else:
            speak("Thinking...")
            answer = ask_ai(command)
            speak(answer)

Thread(target=jarvis_loop, daemon=True).start()
gui.run()

