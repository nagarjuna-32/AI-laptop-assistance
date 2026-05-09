import tkinter as tk

class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS")
        self.root.geometry("400x500")
        self.root.configure(bg="black")

        self.label = tk.Label(
            self.root,
            text="JARVIS",
            font=("Arial", 30),
            fg="cyan",
            bg="black"
        )
        self.label.pack(pady=20)

        self.status = tk.Label(
            self.root,
            text="Status: Idle",
            font=("Arial", 12),
            fg="white",
            bg="black"
        )
        self.status.pack()

    def update_status(self, text):
        self.status.config(text=f"Status: {text}")
        self.root.update()

    def run(self):
        self.root.mainloop()
