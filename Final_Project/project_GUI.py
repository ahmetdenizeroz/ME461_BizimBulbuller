import tkinter as tk
from tkinter import ttk
import subprocess

def open_noros():
    """Opens the NOROS stage and runs noros_pathfinding.py."""
    subprocess.Popen(["python3", "noros_pathfinding.py"])  # Use python3 for Linux

def open_yesros():
    """Opens the YESROS stage window."""
    yesros_window = tk.Toplevel(root)
    yesros_window.title("YESROS Stage")
    yesros_label = tk.Label(yesros_window, text="YESROS Stage - ROS Individual Testing", font=("Arial", 14))
    yesros_label.pack(pady=10)

def open_rosros():
    """Opens the ROSROS stage window."""
    rosros_window = tk.Toplevel(root)
    rosros_window.title("ROSROS Stage")
    rosros_label = tk.Label(rosros_window, text="ROSROS Stage - Group Robot Dance", font=("Arial", 14))
    rosros_label.pack(pady=10)

# Main GUI Window
root = tk.Tk()
root.title("ME 461 Project - Main Interface")
root.geometry("400x300")

# Header Label
title_label = tk.Label(root, text="ME 461 Project - Musical Chairs", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

# Section Buttons
noros_button = ttk.Button(root, text="NOROS - No ROS", command=open_noros)
noros_button.pack(pady=5)

yesros_button = ttk.Button(root, text="YESROS - ROS Individual Testing", command=open_yesros)
yesros_button.pack(pady=5)

rosros_button = ttk.Button(root, text="ROSROS - Group Challenge", command=open_rosros)
rosros_button.pack(pady=5)

# Run GUI
root.mainloop()
