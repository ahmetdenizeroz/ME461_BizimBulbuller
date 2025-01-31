import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import threading
import time

# Import your library classes (modular design)
from GridDetectionFinal2 import ArucoGridDetector  # Robot Position Tracking
from search_class import SearchClass               # Pathfinding (A* Search)
from movement_class import MovementClass           # Movement Control

class NorosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NOROS - Main GUI")
        self.root.geometry("1400x700")
        self.root.resizable(False, False)  

        # Apply TTK styling
        style = ttk.Style()
        style.theme_use("clam")  
        style.configure("TFrame", background="#EAF6F6")
        style.configure("TLabel", background="#EAF6F6", foreground="black", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10, "bold"))

        # ------------------ Initialize Components Concurrently ------------------
        self.init_event = threading.Event()  
        self.detector = None
        self.searcher = None
        self.mover = None

        self.init_threads = [
            threading.Thread(target=self.init_aruco_detector),
            threading.Thread(target=self.init_searcher),
            threading.Thread(target=self.init_mover),
        ]

        for thread in self.init_threads:
            thread.start()

        for thread in self.init_threads:
            thread.join()

        self.init_event.set()
        print("✅ All modules initialized concurrently!")

        # ------------------------ Layout ------------------------
        self.create_layout()
        self.create_control_panel()
        self.update_camera_feed()

    # ----------------------------------------------------------------
    #        Multi-threaded Initialization of Components
    # ----------------------------------------------------------------
    def init_aruco_detector(self):
        """Initializes the ArucoGridDetector."""
        print("Initializing ArucoGridDetector...")
        self.detector = ArucoGridDetector(robot_id=1, rows=3, cols=4, cell_size=100, camera_index=0)
        time.sleep(0.5)
        print("✅ ArucoGridDetector initialized!")

    def init_searcher(self):
        """Initializes the SearchClass."""
        print("Initializing SearchClass...")
        self.searcher = SearchClass()
        time.sleep(0.5)
        print("✅ SearchClass initialized!")

    def init_mover(self):
        """Initializes MovementClass and connects it."""
        print("Initializing MovementClass...")
        self.mover = MovementClass(pico_ip="192.168.31.62", pico_port=8080)
        self.mover.connect()
        time.sleep(0.5)
        print("✅ MovementClass initialized and connected!")

    # ----------------------------------------------------------------
    #        GUI Layout
    # ----------------------------------------------------------------
    def create_layout(self):
        """Sets up the GUI layout."""
        self.left_frame = ttk.Frame(self.root)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.right_frame = ttk.Frame(self.root)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.feed_label = ttk.Label(self.left_frame, text="Camera Feed Loading...")
        self.feed_label.pack(expand=True, fill=tk.BOTH)

        self.canvas_width = 500
        self.canvas_height = 400
        self.grid_canvas = tk.Canvas(self.right_frame, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.grid_canvas.pack(pady=10)

        self.rows = 3
        self.cols = 4
        self.cell_size = self.canvas_width // self.cols
        self.start_cell = None
        self.goal_cell = None
        self.path = []

        self.searcher.set_grid_dimensions(self.rows, self.cols)
        self.draw_grid()
        self.grid_canvas.bind("<Button-1>", self.select_cell)
    def draw_grid(self):
        """
        Draws a 3x4 grid on the canvas with numbers.
        Start cell is green, goal cell is red, path is light blue.
        """
        self.grid_canvas.delete("all")

        cell_index = 1  # For numbering cells from 1..12
        for row in range(self.rows):
            for col in range(self.cols):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                # Determine fill color
                if (row, col) == self.start_cell:
                    color = "green"
                elif (row, col) == self.goal_cell:
                    color = "red"
                elif (row, col) in self.path:
                    color = "#ADD8E6"  # light blue
                else:
                    color = "white"

                # Draw the cell
                self.grid_canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="black"
                )

                # Number the cell in the center
                cx = x1 + self.cell_size // 2
                cy = y1 + self.cell_size // 2
                self.grid_canvas.create_text(cx, cy, text=str(cell_index), fill="black", font=("Arial", 12, "bold"))
                cell_index += 1

    def select_cell(self, event):
        """
        Allows user to click the grid to choose start and goal cells.
        1st click -> start (green)
        2nd click -> goal (red)
        Then automatically compute path (light blue).
        """
        col = event.x // self.cell_size
        row = event.y // self.cell_size

        # Safety check: in range
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return  # click out of bounds

        if self.start_cell is None:
            self.start_cell = (row, col)
        elif self.goal_cell is None:
            self.goal_cell = (row, col)

        # Once start & goal are selected, compute path
        if self.start_cell and self.goal_cell:
            self.compute_path()

        # Redraw to show new selection
        self.draw_grid()

    def compute_path(self):
        """
        Uses the SearchClass to compute a path from start to goal.
        """
        if self.start_cell and self.goal_cell:
            # Ensure grid dimensions are set
            self.searcher.set_grid_dimensions(self.rows, self.cols)

            # Find path using find_path
            self.path = self.searcher.find_path(self.start_cell, self.goal_cell)

            if not self.path:
                print("No path found between the selected cells.")
            else:
                print("Path found:", self.path)

            # Show the path
            self.draw_grid()

    # ----------------------------------------------------------------
    #                       CONTROL PANEL
    # ----------------------------------------------------------------
    def create_control_panel(self):
        """
        Creates a control panel with detection settings (sliders/toggles)
        and path/robot controls (Start, Reset, Exit).
        """
        header = ttk.Label(self.control_frame, text="ArUco Detection Settings", font=("Arial", 14, "bold"))
        header.pack(pady=10)

        # 1) Cluster Size
        self.cluster_size_var = tk.IntVar(value=self.detector.cluster_dist)
        lbl_cluster = ttk.Label(self.control_frame, text="Cluster Size")
        lbl_cluster.pack()
        self.cluster_size_slider = ttk.Scale(
            self.control_frame, from_=10, to=100, orient=tk.HORIZONTAL,
            variable=self.cluster_size_var, command=self.update_cluster_size
        )
        self.cluster_size_slider.pack(pady=5)

        # 2) Threshold Distance
        self.threshold_var = tk.IntVar(value=self.detector.update_thresh)
        lbl_threshold = ttk.Label(self.control_frame, text="Threshold Distance")
        lbl_threshold.pack()
        self.threshold_slider = ttk.Scale(
            self.control_frame, from_=5, to=50, orient=tk.HORIZONTAL,
            variable=self.threshold_var, command=self.update_threshold
        )
        self.threshold_slider.pack(pady=5)

        # 3) Triangle Side
        self.triangle_size_var = tk.IntVar(value=self.detector.triangle_side)
        lbl_triangle = ttk.Label(self.control_frame, text="Triangle Side")
        lbl_triangle.pack()
        self.triangle_slider = ttk.Scale(
            self.control_frame, from_=50, to=200, orient=tk.HORIZONTAL,
            variable=self.triangle_size_var, command=self.update_triangle_side
        )
        self.triangle_slider.pack(pady=5)

        # 4) Toggles (Grid Detection, Intersections, Wrap, Grid Lines)
        self.detect_var = tk.IntVar(value=self.detector.detect_grid)
        self.detect_button = ttk.Checkbutton(
            self.control_frame, text="Grid Detection", variable=self.detect_var, command=self.toggle_detection
        )
        self.detect_button.pack(pady=2)

        self.intersection_var = tk.IntVar(value=self.detector.show_intersections)
        self.intersection_button = ttk.Checkbutton(
            self.control_frame, text="Show Intersections", variable=self.intersection_var, command=self.toggle_intersections
        )
        self.intersection_button.pack(pady=2)

        self.wrap_var = tk.IntVar(value=self.detector.use_wrap)
        self.wrap_button = ttk.Checkbutton(
            self.control_frame, text="Wrap Grid", variable=self.wrap_var, command=self.toggle_wrap
        )
        self.wrap_button.pack(pady=2)

        self.gridlines_var = tk.IntVar(value=self.detector.show_lines)
        self.gridlines_button = ttk.Checkbutton(
            self.control_frame, text="Show Grid Lines", variable=self.gridlines_var, command=self.toggle_gridlines
        )
        self.gridlines_button.pack(pady=2)

        # ---------------- Movement / Path Buttons ----------------
        ttk.Separator(self.control_frame, orient='horizontal').pack(fill='x', pady=10)

        # Start Button
        self.btn_start = ttk.Button(self.control_frame, text="Start", command=self.on_start)
        self.btn_start.pack(pady=5, fill=tk.X)

        # Reset Button
        self.btn_reset = ttk.Button(self.control_frame, text="Reset", command=self.on_reset)
        self.btn_reset.pack(pady=5, fill=tk.X)

        # Exit Button
        self.btn_exit = ttk.Button(self.control_frame, text="Exit", command=self.on_exit)
        self.btn_exit.pack(pady=5, fill=tk.X)

    # ----------------------------------------------------------------
    #                 CAMERA FEED & DETECTION UPDATES
    # ----------------------------------------------------------------
    def update_camera_feed(self):
        """
        Continuously fetches frames from ArucoGridDetector and updates the feed_label.
        """
        success = self.detector.update_frame()
        if success:
            frame = self.detector.get_frame()
            if frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(img_pil)

                self.feed_label.config(image=img_tk)
                self.feed_label.image = img_tk  # keep reference

        # Schedule next update
        self.root.after(100, self.update_camera_feed)

    # ----------------------------------------------------------------
    #            SLIDER/TEXT ENTRY HANDLERS (DETECTION SETTINGS)
    # ----------------------------------------------------------------
    def update_cluster_size(self, value):
        self.detector.set_cluster_dist(int(float(value)))

    def update_threshold(self, value):
        self.detector.set_update_thresh(int(float(value)))

    def update_triangle_side(self, value):
        self.detector.set_triangle_side(int(float(value)))

    # ----------------------------------------------------------------
    #             CHECKBOX TOGGLES (DETECTION SETTINGS)
    # ----------------------------------------------------------------
    def toggle_detection(self):
        self.detector.set_detect_grid_state(self.detect_var.get())

    def toggle_intersections(self):
        self.detector.set_show_intersections(self.intersection_var.get())

    def toggle_wrap(self):
        self.detector.set_use_wrap(self.wrap_var.get())

    def toggle_gridlines(self):
        self.detector.set_show_lines(self.gridlines_var.get())

    # ----------------------------------------------------------------
    #                  BUTTON COMMANDS
    # ----------------------------------------------------------------
    def on_start(self):
        """
        Pressing "Start" will move the robot along the computed path.
        If start/goal not selected, do nothing.
        """
        if not self.start_cell or not self.goal_cell:
            print("Please select Start and Goal cells on the grid first.")
            return

        if not self.path:
            print("No path found. Please select a valid Start/Goal.")
            return

        print("Starting movement along path:", self.path)

        # Execute the path
        self.mover.execute_path(self.path)

        print("Movement complete!")

    def on_reset(self):
        """
        Reset the selected path, start, goal, and refresh controls.
        """
        self.start_cell = None
        self.goal_cell = None
        self.path = []
        self.draw_grid()
        print("Reset complete.")

    def on_exit(self):
        """
        Clean up and exit.
        """
        self.detector.release()
        self.mover.disconnect()
        self.root.destroy()

    # Optional helper if you want to re-sync slider values:
    def update_controls(self):
        """
        Sync GUI controls with ArUcoGridDetector's current parameters.
        """
        self.cluster_size_slider.set(self.detector.cluster_dist)
        self.threshold_slider.set(self.detector.update_thresh)
        self.triangle_slider.set(self.detector.triangle_side)
        self.detect_var.set(self.detector.detect_grid)
        self.intersection_var.set(self.detector.show_intersections)
        self.wrap_var.set(self.detector.use_wrap)
        self.gridlines_var.set(self.detector.show_lines)


def main():
    root = tk.Tk()
    app = NorosGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
