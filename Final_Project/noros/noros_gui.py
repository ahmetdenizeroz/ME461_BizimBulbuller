import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import math

# Import your library classes (modular design)
from GridDetectionFinal2 import ArucoGridDetector  # Robot Position Tracking
from search_modified import SearchClass               # Pathfinding (A* Search)
from movement_class import MovementClass           # Movement Control

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
                robot_id=42, rows=6, cols=8, cell_size=150, camera_index=3
        )

        # 2) Initialize search and movement classes
        self.searcher = SearchClass()
        self.mover = MovementClass(pico_ip="192.168.89.106", pico_port=8080)
        #self.mover.connect()

        # Set grid dimensions in SearchClass
        self.searcher.set_grid_dimensions(self.rows if hasattr(self, 'rows') else 3, 
                                         self.cols if hasattr(self, 'cols') else 4)

        # ------------------------ Main Layout Frames ------------------------
        # Left frame: camera feed
        #self.left_frame = ttk.Frame(self.root)
        #self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.left_frame = ttk.Frame(self.root, width=500, height=400)
        self.left_frame.pack_propagate(False)  # Prevent auto-sizing based on children
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)



        # Right frame: grid display
        self.right_frame = ttk.Frame(self.root)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control panel: sliders, toggles, buttons
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

        # Grid size
        self.rows = 6
        self.cols = 8
        self.cell_size = self.canvas_width // self.cols

        # Track user selections and path
        self.obstacles = []
        self.is_path_found = False
        self.start_cell = None
        self.goal_cell = None
        self.path = []

        # Set grid dimensions in SearchClass
        self.searcher.set_grid_dimensions(self.rows, self.cols)

        # Draw initial grid (with numbering)
        self.draw_grid()

        # Bind canvas click for selecting start/goal
        self.grid_canvas.bind("<Button-1>", self.select_cell)

        # ------------------------ Control Panel ------------------------
        self.create_control_panel()

        # Schedule periodic camera updates
        self.update_camera_feed()
        self.update_grid()

    # ----------------------------------------------------------------
    #                           GRID LOGIC
    # ----------------------------------------------------------------
    def draw_equilateral_triangle(self, canvas, cx, cy, size, angle):
        # Convert angle to radians
        angle_rad = math.radians(angle)

        # Compute front vertex
        front_x = cx + size * math.cos(angle_rad)
        front_y = cy + size * math.sin(angle_rad)

        # Compute the other two vertices by rotating +/-120 degrees
        angle1 = angle_rad + math.radians(120)
        angle2 = angle_rad - math.radians(120)

        left_x = cx + size * math.cos(angle1)
        left_y = cy + size * math.sin(angle1)

        right_x = cx + size * math.cos(angle2)
        right_y = cy + size * math.sin(angle2)

        # Draw the triangle
        canvas.create_polygon(front_x, front_y, left_x, left_y, right_x, right_y, 
                              outline="black", fill="orange", width=2)
    def draw_grid(self):
        """
        Draws a 3x4 grid on the canvas with numbers.
        Start cell is green, goal cell is red, path is light blue.
        """
        self.grid_canvas.delete("all")
        
        for obstacle in self.detector.get_other_markers_cells():
            if obstacle[:2] not in self.obstacles and obstacle[1] != None:
                self.obstacles.append(obstacle[:2])
        for obstacle in self.obstacles:   
            print(self.converter(obstacle[1]))

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
                '''
                elif len(self.obstacles) != 0: 
                    if ((row, col) == converter(obstacle[1]) for obstacle in self.obstacles):
                        color = "grey"
                '''
                elif (row, col, 0) in self.path or (row, col, 90) in self.path or (row, col, 180) in self.path or (row, col, 270) in self.path:
                    color = "#ADD8E6"  # light blue
                else:
                    color = "white"
                #Drawing Grids
                self.grid_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")

                if self.detector.get_robot_cell_label() != None and self.detector.get_robot_cell_label() % self.cols == 0:
                    if self.detector.get_robot_cell_label() != None and (row, col) == ((self.detector.get_robot_cell_label() // self.cols)-1, 7):
                        self.draw_equilateral_triangle(self.grid_canvas, (x1+x2)/2, (y1+y2)/2, self.detector.triangle_side/5, self.detector.get_robot_position()[2])

                else:
                    if self.detector.get_robot_cell_label() != None and (row, col) == (self.detector.get_robot_cell_label() // self.cols , (self.detector.get_robot_cell_label() % self.cols)-1):
                        self.draw_equilateral_triangle(self.grid_canvas, (x1+x2)/2, (y1+y2)/2, self.detector.triangle_side/5, self.detector.get_robot_position()[2])

                # Number the cell in the center
                cx = x1 + self.cell_size // 2
                cy = y1 + self.cell_size // 2
                self.grid_canvas.create_text(cx, cy, text=str(cell_index), fill="black", font=("Arial", 12, "bold"))
                cell_index += 1

    def converter(self, cell_number):
        if cell_number % self.cols == 0:
            return ((cell_number // self.cols)-1, 7)
        else:
            return (cell_number // self.cols , (cell_number % self.cols)-1)

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

        #if self.start_cell is None:
        #    self.start_cell = (row, col)
        
        #if  self.detector.get_robot_cell_label() is None:
        #    self.start_cell = None
        #else:
        #    print(self.detector.get_robot_cell_label())
        #    self.start_cell = (self.detector.get_robot_cell_label() // self.rows , self.detector.get_robot_cell_label() % self.rows)
        if self.goal_cell is None:
            self.goal_cell = (row, col)

        ## Once start & goal are selected, compute path
        #if self.start_cell and self.goal_cell:
        #    self.compute_path()

        # Redraw to show new selection
        self.draw_grid()

    def compute_path(self):
        """
        Uses the SearchClass to compute a path from start to goal.
        """
        if self.start_cell and self.goal_cell and not self.is_path_found:
            # Ensure grid dimensions are set
            self.searcher.set_grid_dimensions(self.rows, self.cols)
            for obstacle in self.obstacles:
                self.searcher.add_obstacle(obstacle[0], obstacle[1])

            # Find path using find_path
            self.path = self.searcher.find_path(self.start_cell, self.goal_cell)

            if not self.path:
                print("No path found between the selected cells.")
                self.is_path_found = False
            else:
                print("Path found:", self.path)
                self.is_path_found = True

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
            self.control_frame, from_=5, to=200, orient=tk.HORIZONTAL,
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
                #frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                #img_pil = Image.fromarray(frame_rgb)
                #img_tk = ImageTk.PhotoImage(img_pil)

                #self.feed_label.config(image=img_tk)
                #self.feed_label.image = img_tk  # keep reference
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(frame_rgb)

                # Resize the image to fit within 450x350
                img_pil = img_pil.resize((450, 350), Image.Resampling.LANCZOS)

                img_tk = ImageTk.PhotoImage(img_pil)
                self.feed_label.config(image=img_tk)
                self.feed_label.image = img_tk


        # Schedule next update
        self.root.after(50, self.update_camera_feed)

    def update_grid(self):
        """
        Continuously updates the grid
        """
        if  self.detector.get_robot_cell_label() is None:
            self.start_cell = None
        else:
            if self.detector.get_robot_cell_label() % self.cols == 0:
                self.start_cell = ((self.detector.get_robot_cell_label() // self.cols)-1, 7)
            else:
                self.start_cell = (self.detector.get_robot_cell_label() // self.cols, (self.detector.get_robot_cell_label() % self.cols)-1)
        
        # Once start & goal are selected, compute path
        if self.start_cell and self.goal_cell:
            self.compute_path()
        
        self.draw_grid()

        # Schedule next update
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
        self_is_path_found = False
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
