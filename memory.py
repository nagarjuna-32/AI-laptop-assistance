import json
import os

FILE = "memory.json"

def remember(data):
    memory = []

    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            memory = json.load(f)

    memory.append(data.strip())

    with open(FILE, "w") as f:
        json.dump(memory, f, indent=4)

def show_memory():
    if not os.path.exists(FILE):
        return "Nothing saved."

    with open(FILE, "r") as f:
        memory = json.load(f)

    return ". ".join(memory)
