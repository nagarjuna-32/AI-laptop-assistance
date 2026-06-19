import webbrowser
import urllib.parse

def google_search(query):
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")

def youtube_play(query):
    webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")

