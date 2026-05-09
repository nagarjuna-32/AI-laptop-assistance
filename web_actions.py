import webbrowser
import pywhatkit

def google_search(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")

def youtube_play(query):
    pywhatkit.playonyt(query)
