import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import math
import threading
import queue

# Import your library classes (modular design)
from Image_processor import ArucoGridDetector  # Robot Position Tracking
from search_class import SearchClass          # Pathfinding (A* Search)
from movement_class4 import MovementClass      # Movement Control

class NorosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NOROS - Main GUI")
        self.root.geometry("1400x700")
        self.root.resizable(False, False)  # Prevent resizing for cleaner UI

        # Apply TTK styling for aesthetics
        style = ttk.Style()
        style.theme_use("clam")  # 'clam', 'alt', 'default', or 'classic'
        style.configure("TFrame", background="#EAF6F6")
        style.configure("TLabel", background="#EAF6F6", foreground="black", font=("Arial", 10))
        style.configure("TCheckbutton", background="#EAF6F6", foreground="black", font=("Arial", 10))
        style.configure("TScale", background="#EAF6F6")
        style.configure("TButton", font=("Arial", 10, "bold"), relief="raised")

        # 1) Initialize ArUco-based detection class
        self.detector = ArucoGridDetector(
            robot_id=42, rows=6, cols=8, cell_size=150, camera_index=2
        )

        # 2) Initialize search and movement classes
        self.searcher = SearchClass()
        self.mover = MovementClass(pico_ip="192.168.232.16", pico_port=12346, detector=self.detector)
        self.mover.connect()  # Connect manually if needed

        # We set default grid dimensions in the search:
        self.rows = 6
        self.cols = 8
        self.searcher.set_grid_dimensions(self.rows, self.cols)

        # ------------------------ Main Layout Frames ------------------------
        self.left_frame = ttk.Frame(self.root, width=500, height=400)
        self.left_frame.pack_propagate(False)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.right_frame = ttk.Frame(self.root)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # ------------------------ Camera Feed ------------------------
        self.feed_label = ttk.Label(self.left_frame, text="Camera Feed Loading...")
        self.feed_label.pack(expand=True, fill=tk.BOTH)

        # ------------------------ Grid Canvas ------------------------
        self.canvas_width = 500
        self.canvas_height = 400
        self.grid_canvas = tk.Canvas(
            self.right_frame, width=self.canvas_width, height=self.canvas_height, bg="white"
        )
        self.grid_canvas.pack(pady=10)

        self.cell_size = self.canvas_width // self.cols

        # Track user selections and path
        self.obstacles = []
        self.is_path_found = False
        self.start_cell = None
        self.goal_cell = None
        self.path = []

        # Draw the initial grid
        self.draw_grid()

        # Bind canvas click for selecting goal
        self.grid_canvas.bind("<Button-1>", self.select_goal_cell)

        # Create the control panel
        self.create_control_panel()

        # Status Label
        self.status_label = ttk.Label(self.control_frame, text="Status: Idle", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=10, fill=tk.X)

        # Movement Thread Control
        self.movement_thread = None
        self.movement_queue = queue.Queue()

        # Periodic camera and grid updates
        self.update_camera_feed()
        self.update_grid()

    # ----------------------------------------------------------------
    #                           GRID LOGIC
    # ----------------------------------------------------------------
    def draw_equilateral_triangle(self, canvas, cx, cy, size, angle):
        """Helper to draw the robot's orientation as a triangle."""
        angle_rad = math.radians(angle)
        # front corner
        fx = cx + size * math.cos(angle_rad)
        fy = cy + size * math.sin(angle_rad)
        # other corners = +/-120 deg
        angle1 = angle_rad + math.radians(120)
        angle2 = angle_rad - math.radians(120)
        lx = cx + size * math.cos(angle1)
        ly = cy + size * math.sin(angle1)
        rx = cx + size * math.cos(angle2)
        ry = cy + size * math.sin(angle2)

        canvas.create_polygon(
            fx, fy, lx, ly, rx, ry,
            outline="black", fill="orange", width=2
        )

    def draw_grid(self):
        """
        Draw grid with the following color coding:
        - Start cell: green
        - Goal cell: red
        - Obstacles: grey
        - Path: light blue
        - Robot: orange triangle on top
        """
        self.grid_canvas.delete("all")

        cell_index = 1
        for row in range(self.rows):
            for col in range(self.cols):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                # Decide fill color
                if (row, col) == self.start_cell:
                    color = "green"
                elif (row, col) == self.goal_cell:
                    color = "red"
                elif (row, col) in self.obstacles:
                    color = "grey"
                elif any((row, col) == (step[0], step[1]) for step in self.path):
                    color = "#ADD8E6"  # light blue
                else:
                    color = "white"

                self.grid_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")

                # If robot is at (row, col) in real time, draw the triangle
                if self.detector.get_robot_cell_label() is not None:
                    # Convert label -> (r, c)
                    label = self.detector.get_robot_cell_label()
                    robot_coords = self.converter(label)
                    if robot_coords and (row, col) == robot_coords:
                        # Draw the orientation triangle
                        # center of cell
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        angle_deg = 0
                        robot_pos = self.detector.get_robot_position()
                        if robot_pos is not None:
                            angle_deg = robot_pos[2]
                        self.draw_equilateral_triangle(
                            self.grid_canvas,
                            cx,
                            cy,
                            self.detector.triangle_side / 5,
                            angle_deg
                        )

                # Number the cell in the center
                cx = x1 + self.cell_size // 2
                cy = y1 + self.cell_size // 2
                self.grid_canvas.create_text(cx, cy, text=str(cell_index), fill="black", font=("Arial", 12, "bold"))
                cell_index += 1

    def converter(self, cell_number):
        """Convert cell label to (row, col).  E.g. label=1 => (0,0), etc."""
        if cell_number is None:
            return None
        # Because we have self.cols columns, label i => row=(i-1)//cols, col=(i-1) % cols
        # but user’s code had a slightly different pattern. Let’s keep it:
        if cell_number % self.cols == 0:
            return ((cell_number // self.cols) - 1, self.cols - 1)
        else:
            return (cell_number // self.cols, (cell_number % self.cols) - 1)

    def select_goal_cell(self, event):
        """
        Allows user to click on the grid to choose a goal cell (red).
        The robot cell is auto-detected from Aruco. Then we compute path.
        """
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return  # out of bounds

        self.goal_cell = (row, col)
        print(f"User selected goal cell = {self.goal_cell}")

        self.draw_grid()

    def compute_path(self):
        """
        Use the SearchClass to compute a path from the robot's start cell to the user-chosen goal cell.
        The robot's orientation is also used as the initial direction.
        """
        if self.start_cell is None or self.goal_cell is None:
            return

        # Clear old path
        self.path = []

        # Tell the searcher about obstacles
        self.searcher.clear_obstacles()
        for (r, c) in self.obstacles:
            self.searcher.add_obstacle(r, c)

        # Suppose the robot orientation is from the detector (mod 360)
        robot_angle = 0
        if self.detector.get_robot_position() is not None:
            robot_angle = self.detector.get_robot_position()[2]

        # Find path
        result_path = self.searcher.find_path(
            self.start_cell, self.goal_cell,
            initial_direction=robot_angle
        )
        if result_path:
            self.path = result_path
            print("Path found:", self.path)
            self.is_path_found = True
        else:
            print("No path found between the selected cells.")
            self.is_path_found = False

    # ----------------------------------------------------------------
    #                       CONTROL PANEL
    # ----------------------------------------------------------------
    def create_control_panel(self):
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
            self.control_frame, from_=5, to=200, orient=tk.HORIZONTAL,
            variable=self.triangle_size_var, command=self.update_triangle_side
        )
        self.triangle_slider.pack(pady=5)

        # 4) Toggles
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

        # Movement / Path Buttons
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
        Continuously fetch frames from ArucoGridDetector and updates the feed_label.
        """
        success = self.detector.update_frame()
        if success:
            frame = self.detector.get_frame()
            if frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(frame_rgb)
                # Resize to fit the label
                img_pil = img_pil.resize((450, 350), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img_pil)
                self.feed_label.config(image=img_tk)
                self.feed_label.image = img_tk

        self.root.after(50, self.update_camera_feed)

    def update_grid(self):
        """
        Continuously updates the grid status:
        - Robot cell => start_cell
        - Other markers => obstacles
        - If both start & goal are known => compute path
        """
        # 1) Update start_cell from the robot's cell label
        label = self.detector.get_robot_cell_label()
        if label is not None:
            self.start_cell = self.converter(label)
        else:
            self.start_cell = None

        # 2) Update obstacles from other markers
        self.obstacles.clear()
        for (marker_id, cell_label, angle_deg) in self.detector.get_other_markers_cells():
            if cell_label is not None:
                obs = self.converter(cell_label)
                if obs and obs != self.start_cell and obs != self.goal_cell:
                    self.obstacles.append(obs)

        # 3) If we have both start & goal, compute path
        if self.start_cell is not None and self.goal_cell is not None and not self.is_path_found:
            self.compute_path()

        # 4) Redraw grid
        self.draw_grid()

        self.root.after(50, self.update_grid)

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
        Pressing "Start" moves the robot along the computed path.
        """
        if not self.start_cell or not self.goal_cell:
            print("Please select Goal cell and ensure Robot is detected.")
            self.update_status("Please select Goal cell and ensure Robot is detected.")
            return

        if not self.path:
            print("No path found. Cannot move.")
            self.update_status("No path found. Cannot move.")
            return

        if self.movement_thread and self.movement_thread.is_alive():
            print("Movement is already in progress.")
            self.update_status("Movement is already in progress.")
            return

        # Start movement in a separate thread
        self.movement_thread = threading.Thread(target=self.run_movement, daemon=True)
        self.movement_thread.start()

    def run_movement(self):
        """
        Runs the movement execution and updates the GUI status accordingly.
        """
        try:
            self.update_status("Movement in progress...")
            print("Starting movement along path:", self.path)
            self.mover.execute_path(self.path)
            print("Movement complete (all commands sent).")
            self.update_status("Movement complete.")
        except Exception as e:
            print(f"Error during movement: {e}")
            self.update_status(f"Error during movement: {e}")

    def on_reset(self):
        """
        Reset the path, start, goal, obstacles, etc.
        """
        if self.movement_thread and self.movement_thread.is_alive():
            print("Cannot reset while movement is in progress.")
            self.update_status("Cannot reset while movement is in progress.")
            return

        self.is_path_found = False
        self.start_cell = None
        self.goal_cell = None
        self.path = []
        self.obstacles.clear()
        self.draw_grid()
        self.update_status("Reset complete.")
        print("Reset complete.")

    def on_exit(self):
        """
        Clean up and exit.
        """
        if self.movement_thread and self.movement_thread.is_alive():
            print("Waiting for movement to finish before exiting...")
            self.update_status("Waiting for movement to finish before exiting...")
            self.movement_thread.join()

        self.detector.release()
        self.mover.disconnect()
        self.root.destroy()

    def update_status(self, message):
        """
        Thread-safe method to update the status label.
        """
        # Use thread-safe queue to update GUI elements
        self.movement_queue.put(message)
        self.root.after(100, self.process_queue)

    def process_queue(self):
        """
        Process the movement queue and update the GUI accordingly.
        """
        try:
            while not self.movement_queue.empty():
                message = self.movement_queue.get_nowait()
                self.status_label.config(text=f"Status: {message}")
        except queue.Empty:
            pass

    # ----------------------------------------------------------------
    #                      MAIN APPLICATION LOOP
    # ----------------------------------------------------------------
def main():
    root = tk.Tk()
    app = NorosGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

