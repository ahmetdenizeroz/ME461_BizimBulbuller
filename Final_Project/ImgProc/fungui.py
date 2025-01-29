import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
import sys
import cv2

# Import the ArucoGridDetector class
# Make sure aruco_grid_detector.py is in the same directory or adjust the import path accordingly
from GridDetectionFinal2 import ArucoGridDetector

class App:
    def __init__(self, root, detector):
        self.root = root
        self.detector = detector
        self.root.title("Aruco Grid Detector GUI")
        self.root.geometry("1920x1080")
        self.root.resizable(False, False)

        # Create frames for layout
        self.video_frame = ttk.Frame(root, width=1280, height=720)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10)

        self.controls_frame = ttk.Frame(root, width=640, height=720)
        self.controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky='N')

        # Video display label
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack()

        # Robot position label
        self.robot_pos_label = ttk.Label(self.controls_frame, text="Robot Position: N/A", font=("Arial", 16))
        self.robot_pos_label.pack(pady=10)

        # Other markers position label
        self.other_markers_label = ttk.Label(self.controls_frame, text="Other Markers:", font=("Arial", 16))
        self.other_markers_label.pack(pady=10)

        # Parameters Controls
        self.create_controls()

        # Start the video loop in a separate thread
        self.stop_event = threading.Event()
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_controls(self):
        """Create sliders and checkboxes for the six parameters."""
        controls = [
            {
                "name": "Cluster Distance",
                "setter": self.detector.set_cluster_dist,
                "type": "slider",
                "from_": 10,
                "to": 200,
                "default": self.detector.cluster_dist
            },
            {
                "name": "Update Threshold",
                "setter": self.detector.set_update_thresh,
                "type": "slider",
                "from_": 5,
                "to": 100,
                "default": self.detector.update_thresh
            },
            {
                "name": "Show Intersections",
                "setter": self.detector.set_show_intersections,
                "type": "checkbox",
                "default": self.detector.show_intersections
            },
            {
                "name": "Triangle Side",
                "setter": self.detector.set_triangle_side,
                "type": "slider",
                "from_": 5,
                "to": 500,
                "default": self.detector.triangle_side
            },
            {
                "name": "Show Lines",
                "setter": self.detector.set_show_lines,
                "type": "checkbox",
                "default": self.detector.show_lines
            },
            {
                "name": "Use Warp",
                "setter": self.detector.set_use_wrap,
                "type": "checkbox",
                "default": self.detector.use_wrap
            },
            {
                "name": "Detect Grid",
                "setter": self.detector.set_detect_grid_state,
                "type": "checkbox",
                "default": self.detector.detect_grid
            },
        ]

        for control in controls:
            if control["type"] == "slider":
                frame = ttk.Frame(self.controls_frame)
                frame.pack(fill='x', pady=5)

                label = ttk.Label(frame, text=control["name"], font=("Arial", 12))
                label.pack(anchor='w')

                slider = ttk.Scale(
                    frame, from_=control["from_"], to=control["to_"] if "to_" in control else control["to"],
                    orient='horizontal', command=lambda val, s=control["setter"], lbl=None: self.update_slider(val, s, lbl)
                )
                slider.set(control["default"])
                slider.pack(fill='x', padx=5)
                
                # Display current value
                value_label = ttk.Label(frame, text=str(control["default"]))
                value_label.pack(anchor='e')

                # Update value label on slider change
                slider.config(command=lambda val, s=control["setter"], lbl=value_label: self.update_slider(val, s, lbl))
            
            elif control["type"] == "checkbox":
                var = tk.IntVar(value=control["default"])
                check = ttk.Checkbutton(
                    self.controls_frame, text=control["name"],
                    variable=var,
                    command=lambda v=var, s=control["setter"]: s(v.get())
                )
                check.pack(anchor='w', pady=5)

    def update_slider(self, val, setter, label):
        """Update the setter and the label for sliders."""
        setter(int(float(val)))
        if label:
            label.config(text=str(int(float(val))))

    def video_loop(self):
        """Continuously get frames from the detector and update the GUI."""
        while not self.stop_event.is_set():
            success = self.detector.update_frame()
            if success:
                frame = self.detector.get_frame()
                if frame is not None:
                    # Convert the frame to RGB and then to PIL Image
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img = img.resize((1280, 720), Image.Resampling.LANCZOS)  # Updated resize method

                    imgtk = ImageTk.PhotoImage(image=img)

                    # Update the video label
                    self.video_label.imgtk = imgtk  # Keep a reference to avoid garbage collection
                    self.video_label.configure(image=imgtk)

                    # Update robot position
                    robot_label = self.detector.get_robot_cell_label()
                    if robot_label is not None:
                        self.robot_pos_label.config(text=f"Robot Position: {robot_label}")
                    else:
                        self.robot_pos_label.config(text="Robot Position: N/A")
                    '''
                    # Update other markers
                    other_markers = self.detector.get_other_markers_cells()
                    markers_text = "Other Markers:\n" + "\n".join([
                        f"ID: {mid}, Cell: {cell}, Angle: {angle:.1f}°"
                        for mid, cell, angle in other_markers
                    ]) if other_markers else "Other Markers: N/A"
                    self.other_markers_label.config(text=markers_text)
                    '''
            else:
                print("Failed to update frame.")

            time.sleep(0.03)  # Approximately 30 FPS

    def on_closing(self):
        """Handle the window closing event."""
        self.stop_event.set()
        self.detector.release()
        self.root.destroy()

def main():
    # Initialize the detector with your parameters
    # Replace these values with your actual robot ID, grid size, and cell size
    robot_id = 28
    rows = 3
    cols = 4
    cell_size = 100  # e.g., in millimeters

    detector = ArucoGridDetector(robot_id=robot_id, rows=rows, cols=cols, cell_size=cell_size, camera_index=0)

    # Initialize the GUI
    root = tk.Tk()
    app = App(root, detector)
    root.mainloop()

if __name__ == "__main__":
    main()

