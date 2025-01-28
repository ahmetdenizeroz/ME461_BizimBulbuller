# THEMAIN.py

import tkinter as tk
from tkinter import messagebox
import subprocess
import socket
import time

# Suppose we have a single PicoComm-like approach:
# For demonstration, let's do a small wrapper here:
class PicoConnectionManager:
    def __init__(self, ip="192.168.185.106", port=8080):
        self.ip = ip
        self.port = port
        self.client = None

    def connect(self):
        """Attempt to connect to the Pico once."""
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.ip, self.port))
            print("Connected to Pico!")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self.client = None
            return False

    def is_connected(self):
        return self.client is not None

    def send_command(self, cmd):
        if self.client is None:
            return
        try:
            self.client.sendall(cmd.encode())
        except:
            self.client = None

    def close(self):
        if self.client:
            self.client.close()
        self.client = None


class MainLauncherApp:
    """
    Main GUI to select gamemodes:
      - NoROS
      - YESROS
      - ROSROS
    Also attempts Pico connection and displays connection status.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("ME461 Project - Main Launcher")
        self.root.geometry("500x400")

        self.pico_manager = PicoConnectionManager()

        # Title
        tk.Label(self.root, text="ME461 Project - Musical Chairs", font=("Arial", 16, "bold")).pack(pady=10)

        # Connection status
        self.status_label = tk.Label(self.root, text="Attempting Connection...", font=("Arial", 12))
        self.status_label.pack(pady=5)

        # Connect once at startup
        self.check_connection()

        # Buttons
        self.noros_button = tk.Button(self.root, text="NoROS", font=("Arial", 12),
                                      command=self.launch_noros)
        self.noros_button.pack(pady=10)

        self.yesros_button = tk.Button(self.root, text="YESROS", font=("Arial", 12),
                                       command=self.launch_yesros)
        self.yesros_button.pack(pady=10)

        self.rosros_button = tk.Button(self.root, text="ROSROS", font=("Arial", 12),
                                       command=self.launch_rosros)
        self.rosros_button.pack(pady=10)

    def check_connection(self):
        """Try connecting once; update the label accordingly."""
        success = self.pico_manager.connect()
        if success:
            self.status_label.config(text="Connected to Pico: OK", fg="green")
        else:
            self.status_label.config(text="Not Connected to Pico", fg="red")

    def launch_noros(self):
        """
        Launches the NoROS subgame.
        We'll pass the existing connection manager's info somehow, or let the subgame
        re-attempt if connection is lost.
        """
        # Option 1: Launch as a separate Python process (like your older code).
        # subprocess.Popen(["python3", "noros.py"])
        #
        # Option 2: Import noros.py as a module and launch it in the same process:
        import noros
        # Create a new Toplevel for the NoROS game, passing the Pico manager
        noros.NorosGame(self.root, self.pico_manager)

    def launch_yesros(self):
        tk.messagebox.showinfo("YESROS", "YESROS Stage not yet implemented.")

    def launch_rosros(self):
        tk.messagebox.showinfo("ROSROS", "ROSROS Stage not yet implemented.")


def main():
    root = tk.Tk()
    app = MainLauncherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

