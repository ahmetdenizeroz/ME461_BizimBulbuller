import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import math
import threading
import queue
import sys

# Import your library classes (modular design)
from Image_processor import ArucoGridDetector  # Robot Position Tracking
from search_class import SearchClass          # Pathfinding (A* Search)
from movement_class5 import MovementClass      # Movement Control

class TextRedirector:
    """Redirects print output to the Text widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        """Insert the message into the Text widget and auto-scroll."""
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Auto-scroll to the latest message

    def flush(self):
        pass

class NorosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NOROS - Main GUI")
        self.root.geometry("1920x1080") #1400x700
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
        self.left_frame = ttk.Frame(self.root, width=500, height=700)
        self.left_frame.pack_propagate(False)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.right_frame = ttk.Frame(self.root)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # ------------------------ Left Frame Layout (Camera + Log) ------------------------

        # Frame to contain camera feed
        self.feed_label = ttk.Label(self.left_frame, text="Camera Feed Loading...")
        self.feed_label.pack(expand=False, fill=tk.BOTH, padx=5, pady=(5, 2))  # Margin on top

        # Frame for the log text box (fills remaining space under the camera)
        log_frame = ttk.Frame(self.left_frame)
        log_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=(2, 5))  # Margin at the bottom

        self.log_text = tk.Text(log_frame, wrap="word", font=("Arial", 12, "bold"))
        self.log_text.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # Redirect print to the GUI (using the one log_text widget)
        sys.stdout = TextRedirector(self.log_text)

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
        self.next_cell = None
        self.path = []
        self.old_robot_detection_stat = None
        self.is_path_executing = False   # True when path execution starts, False when it stops
        self.is_in_destination_cell = False  # True when robot is in the goal cell

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
        self.update_led_status()

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
                elif (row, col) == self.next_cell:
                    color = "orange"
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

        robot_angle = 0
        if self.detector.get_robot_position() is not None:
            robot_angle = self.detector.get_robot_position()[2]

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

        self.cluster_size_var = tk.IntVar(value=self.detector.cluster_dist)
        lbl_cluster = ttk.Label(self.control_frame, text="Cluster Size")
        lbl_cluster.pack()
        self.cluster_size_slider = ttk.Scale(
            self.control_frame, from_=10, to=100, orient=tk.HORIZONTAL,
            variable=self.cluster_size_var, command=self.update_cluster_size
        )
        self.cluster_size_slider.pack(pady=5)

        self.threshold_var = tk.IntVar(value=self.detector.update_thresh)
        lbl_threshold = ttk.Label(self.control_frame, text="Threshold Distance")
        lbl_threshold.pack()
        self.threshold_slider = ttk.Scale(
            self.control_frame, from_=5, to=50, orient=tk.HORIZONTAL,
            variable=self.threshold_var, command=self.update_threshold
        )
        self.threshold_slider.pack(pady=5)

        self.triangle_size_var = tk.IntVar(value=self.detector.triangle_side)
        lbl_triangle = ttk.Label(self.control_frame, text="Triangle Side")
        lbl_triangle.pack()
        self.triangle_slider = ttk.Scale(
            self.control_frame, from_=5, to=200, orient=tk.HORIZONTAL,
            variable=self.triangle_size_var, command=self.update_triangle_side
        )
        self.triangle_slider.pack(pady=5)

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

        ttk.Separator(self.control_frame, orient='horizontal').pack(fill='x', pady=10)

        self.btn_start = ttk.Button(self.control_frame, text="Start", command=self.on_start)
        self.btn_start.pack(pady=5, fill=tk.X)

        self.btn_reset = ttk.Button(self.control_frame, text="Reset", command=self.on_reset)
        self.btn_reset.pack(pady=5, fill=tk.X)

        self.btn_exit = ttk.Button(self.control_frame, text="Exit", command=self.on_exit)
        self.btn_exit.pack(pady=5, fill=tk.X)

    # ----------------------------------------------------------------
    #                 CAMERA FEED & DETECTION UPDATES
    # ----------------------------------------------------------------
    def update_camera_feed(self):
        success = self.detector.update_frame()
        if success:
            frame = self.detector.get_frame()
            if frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(frame_rgb)
                img_pil = img_pil.resize((450, 350), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img_pil)
                self.feed_label.config(image=img_tk)
                self.feed_label.image = img_tk

        self.root.after(50, self.update_camera_feed)

    def update_grid(self):
        label = self.detector.get_robot_cell_label()
        if label is not None:
            self.start_cell = self.converter(label)
        else:
            self.start_cell = None

        self.obstacles.clear()
        for (marker_id, cell_label, angle_deg) in self.detector.get_other_markers_cells():
            if cell_label is not None:
                obs = self.converter(cell_label)
                if obs and obs != self.start_cell and obs != self.goal_cell:
                    self.obstacles.append(obs)

        if self.start_cell is not None and self.goal_cell is not None and not self.is_path_found:
            self.compute_path()

        self.is_in_destination_cell = (self.start_cell == self.goal_cell)

        if len(self.path) != 0:
            for i in range(len(self.path)):
                row, col, _ = self.path[i]
                if (row, col) == self.converter(self.detector.get_robot_cell_label()) and (i+1) != len(self.path):
                    rown, coln, _ = self.path[i+1]
                    self.next_cell = (rown, coln)
                    break

        self.draw_grid()
        self.root.after(50, self.update_grid)

    def update_led_status(self):
        current_robot_status = self.detector.get_robot_cell_label() is not None
        current_path_executing = self.is_path_executing
        current_in_destination = self.is_in_destination_cell

        status_messages = []
        if current_robot_status != self.old_robot_detection_stat and not current_path_executing:
            status_messages.append("STATUS,Robot Detected" if current_robot_status else "STATUS,Robot Not Detected")
            self.old_robot_detection_stat = current_robot_status

        if current_path_executing != getattr(self, "old_path_executing_status", None):
            status_messages.append("STATUS,Path Executing" if current_path_executing else "STATUS,No Path Execution")
            self.old_path_executing_status = current_path_executing

        if current_in_destination != getattr(self, "old_in_destination_status", None):
            status_messages.append("STATUS,In Destination Cell" if current_in_destination else "STATUS,Not in Destination Cell")
            self.old_in_destination_status = current_in_destination

        for message in status_messages:
            threading.Thread(target=self.mover.send_status_message, args=(message,), daemon=True).start()

        self.root.after(50, self.update_led_status)

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
    #                  PRINT REDIRECT HANDLER
    # ----------------------------------------------------------------
    def update_status(self, message):
        self.movement_queue.put(message)
        self.root.after(100, self.process_queue)

    def process_queue(self):
        try:
            while not self.movement_queue.empty():
                message = self.movement_queue.get_nowait()
                self.status_label.config(text=f"Status: {message}")
        except queue.Empty:
            pass

    # ----------------------------------------------------------------
    #                  BUTTON COMMANDS
    # ----------------------------------------------------------------
    def on_start(self):
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

        self.is_path_executing = True
        self.movement_thread = threading.Thread(target=self.run_movement, daemon=True)
        self.movement_thread.start()

    def run_movement(self):
        try:
            self.update_status("Movement in progress...")
            print("Starting movement along path:", self.path)
            self.mover.execute_path(self.path)
            print("Movement complete (all commands sent).")
            self.update_status("Movement complete.")
        except Exception as e:
            print(f"Error during movement: {e}")
            self.update_status(f"Error during movement: {e}")
        self.is_path_executing = False

    def on_reset(self):
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
        self.next_cell = None
        self.update_status("Reset complete.")
        print("Reset complete.")

    def on_exit(self):
        if self.movement_thread and self.movement_thread.is_alive():
            print("Waiting for movement to finish before exiting...")
            self.update_status("Waiting for movement to finish before exiting...")
            self.movement_thread.join()

        self.detector.release()
        self.mover.disconnect()
        self.root.destroy()

    def update_status(self, message):
        self.movement_queue.put(message)
        self.root.after(100, self.process_queue)

    def process_queue(self):
        try:
            while not self.movement_queue.empty():
                message = self.movement_queue.get_nowait()
                self.status_label.config(text=f"Status: {message}")
        except queue.Empty:
            pass

def main():
    root = tk.Tk()
    app = NorosGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

