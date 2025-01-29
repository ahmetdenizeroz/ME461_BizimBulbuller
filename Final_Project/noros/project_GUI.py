import tkinter as tk
from tkinter import ttk
import subprocess

class MainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ME 461 Project - Main Interface")
        self.root.geometry("500x350")
        self.root.resizable(False, False)  # Prevent resizing for cleaner UI

        # Apply TTK styling for aesthetics
        style = ttk.Style()
        style.theme_use("clam")  # 'clam', 'alt', 'default', or 'classic'
        style.configure("TFrame", background="#EAF6F6")
        style.configure("TLabel", background="#17202A", foreground="white", font=("Arial", 12))
        style.configure("TButton", font=("Arial", 12, "bold"), padding=10)
        
        # Center the window on the screen
        self.center_window(500, 350)

        # Main Frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # Header Label (Title)
        self.title_label = ttk.Label(
            self.main_frame, text="🎵 ME 461 Project - Musical Chairs 🎵",
            font=("Arial", 16, "bold"), background="#EAF6F6"
        )
        self.title_label.pack(pady=20)

        # Buttons for Game Stages
        self.create_buttons()

    def create_buttons(self):
        """Creates the stage selection buttons."""
        btn_style = {"width": 30}  # Standard button width

        self.noros_button = ttk.Button(
            self.main_frame, text="NOROS - No ROS Mode",
            command=self.open_noros, **btn_style
        )
        self.noros_button.pack(pady=10)

        self.yesros_button = ttk.Button(
            self.main_frame, text="YESROS - ROS Individual Testing",
            command=self.open_yesros, **btn_style
        )
        self.yesros_button.pack(pady=10)

        self.rosros_button = ttk.Button(
            self.main_frame, text="ROSROS - Group Challenge",
            command=self.open_rosros, **btn_style
        )
        self.rosros_button.pack(pady=10)

    def open_noros(self):
        """Opens the NOROS stage and runs noros_gui.py."""
        subprocess.Popen(["python3", "noros_gui.py"])  # Use python3 for Linux

    def open_yesros(self):
        """Opens the YESROS stage window."""
        yesros_window = tk.Toplevel(self.root)
        yesros_window.title("YESROS Stage")
        ttk.Label(yesros_window, text="YESROS Stage - ROS Individual Testing", font=("Arial", 14)).pack(pady=20)

    def open_rosros(self):
        """Opens the ROSROS stage window."""
        rosros_window = tk.Toplevel(self.root)
        rosros_window.title("ROSROS Stage")
        ttk.Label(rosros_window, text="ROSROS Stage - Group Robot Dance", font=("Arial", 14)).pack(pady=20)

    def center_window(self, width, height):
        """Centers the window on the screen."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width - width) // 2
        y_position = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x_position}+{y_position}")

# Run GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = MainGUI(root)
    root.mainloop()

