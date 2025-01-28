# noros.py
import tkinter as tk
import cv2
import time
from tkinter import messagebox

# Reuse your pathfinding, image_proc, etc.
from pathfinding import a_star
from image_proc import ImageProcessor

class NorosGame:
    def __init__(self, parent, pico_manager):
        """
        parent: a Tk root or Toplevel
        pico_manager: an existing connection manager from THEMAIN
        """
        self.pico_manager = pico_manager

        # Create a new fullscreen Toplevel for NoROS stage
        self.window = tk.Toplevel(parent)
        self.window.title("NoROS Stage")
        self.window.attributes("-fullscreen", True)  # go fullscreen

        # Variables for the grid size
        self.rows = 3
        self.cols = 4
        self.cell_size = 80  # px for the GUI squares

        # We'll also define the physical size for perspective transform:
        self.physical_rows = 3
        self.physical_cols = 4
        self.physical_cell_size = 100.0  # mm or arbitrary

        # Create an ImageProcessor (camera #2, etc.)
        # We'll prompt or just fix an ID for demonstration
        self.robot_id = 7
        self.iproc = ImageProcessor(
            robot_id=self.robot_id,
            n=self.physical_rows,
            m=self.physical_cols,
            cell_size=self.physical_cell_size
        )
        if not self.iproc.is_opened():
            messagebox.showerror("Error", "Could not open camera #2")
            return

        # Build the pathfinding grid UI
        self.start = None
        self.goal = None
        self.obstacles = set()  # store (r, c) that are blocked or special

        self.canvas = tk.Canvas(self.window, width=self.cols*self.cell_size, height=self.rows*self.cell_size)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        # We'll store references to each cell in grid_refs
        self.grid_refs = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.draw_grid()

        self.canvas.bind("<Button-1>", self.on_grid_click)

        # Some label or frame on the right side
        self.control_frame = tk.Frame(self.window)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.status_label = tk.Label(self.control_frame, text="NoROS - Ready", font=("Arial", 14))
        self.status_label.pack(pady=10)

        # Some button to exit fullscreen
        tk.Button(self.control_frame, text="Exit Fullscreen", command=self.exit_fullscreen).pack(pady=5)

        # A frame or placeholders for toggles (grid lines, intersections, etc.)
        # For simplicity, let's rely on the same trackbar logic you used in OpenCV.
        # We'll just keep it simple here.

        # We'll track the robot cell
        self.robot_cell = None

        # We'll set up an update loop
        self.window.after(100, self.update_loop)

    def draw_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                x1, y1 = c*self.cell_size, r*self.cell_size
                x2, y2 = x1+self.cell_size, y1+self.cell_size
                rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")
                self.grid_refs[r][c] = rect_id

    def on_grid_click(self, event):
        c = event.x // self.cell_size
        r = event.y // self.cell_size

        # If user hasn't placed start
        if self.start is None:
            self.start = (r, c)
            self.set_cell_color(r, c, "green")
        # Then place goal
        elif self.goal is None:
            self.goal = (r, c)
            self.set_cell_color(r, c, "red")
            # Immediately plan path
            self.plan_path()
        else:
            # reset
            self.clear_grid()
            self.start = (r, c)
            self.set_cell_color(r, c, "green")
            self.goal = None

    def plan_path(self):
        """Compute path using A* (with obstacles, etc.). 
           Also incorporate special marker-based points as penalty or reward."""
        # Build a cost or penalty map if needed
        path = a_star(self.start, self.goal, self.rows, self.cols, obstacles=self.obstacles)
        if path:
            # highlight path
            for (rr, cc) in path:
                if (rr, cc) not in [self.start, self.goal]:
                    self.set_cell_color(rr, cc, "lightblue")
            # Also show in the final video feed if needed
            self.status_label.config(text="Path found!")
        else:
            self.status_label.config(text="No path found!")

    def update_loop(self):
        """
        Periodically:
          1) Read a frame
          2) Detect grid + ArUco
          3) Place markers in the GUI as obstacles or reward/penalty
          4) Show robot cell
          5) Show everything in an OpenCV window (the 'final video feed')
        """
        frame = self.iproc.read_frame()
        if frame is not None:
            # Possibly get trackbar states, e.g. cluster size, wrap toggles.
            # For demonstration, let's fix them:
            cluster_dist = 50
            update_thresh = 10

            # Detect the grid
            self.iproc.detect_grid(frame, cluster_dist=cluster_dist, update_thresh=update_thresh)
            # Detect markers
            detections = self.iproc.detect_aruco(frame)

            # Clear old obstacles
            self.obstacles.clear()
            # Check each marker
            for (marker_id, (cx, cy), angle_deg, corners) in detections:
                # If it's the robot
                if marker_id == self.robot_id:
                    robot_cell = self.iproc.find_robot_cell((cx, cy))
                    if robot_cell is not None:
                        self.robot_cell = robot_cell
                else:
                    # It's some other marker -> treat as an obstacle or special cell
                    cell = self.iproc.find_robot_cell((cx, cy))
                    if cell is not None:
                        # odd ID -> penalty (CYAN), even ID -> reward (DARK BLUE)
                        if marker_id % 2 == 1:
                            self.obstacles.add(cell)
                            # We'll color it CYAN in the grid
                            rr, cc = cell
                            self.set_cell_color(rr, cc, "cyan")
                        else:
                            self.obstacles.add(cell)
                            rr, cc = cell
                            self.set_cell_color(rr, cc, "blue")

                # Also draw goal in the final feed if we want
                # or we can place a small circle in the image

            # If we have a robot_cell, color it YELLOW (unless it's start or goal)
            self.refresh_grid_colors()

            # Show final feed in an OpenCV window
            cv2.imshow("NoROS - Final Video Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.exit_fullscreen()

        # re-schedule
        self.window.after(100, self.update_loop)

    def refresh_grid_colors(self):
        """Re-color the grid to reflect obstacles, start, goal, robot, etc."""
        for r in range(self.rows):
            for c in range(self.cols):
                color = "white"
                if (r, c) == self.start:
                    color = "green"
                elif (r, c) == self.goal:
                    color = "red"
                if (r, c) in self.obstacles:
                    # We already did a pass for obstacles (e.g., cyan/blue),
                    # but let's unify here if needed
                    # color = "cyan" or "blue" based on stored metadata
                    pass
                self.set_cell_color(r, c, color)

        # If path was computed, highlight it
        # (You might store it in self.path_cells, etc.)

        # Highlight robot
        if self.robot_cell is not None:
            rr, cc = self.robot_cell
            if (rr, cc) != self.start and (rr, cc) != self.goal:
                self.set_cell_color(rr, cc, "yellow")

    def clear_grid(self):
        """Reset the grid to white, no start/goal."""
        for r in range(self.rows):
            for c in range(self.cols):
                self.set_cell_color(r, c, "white")
        self.start = None
        self.goal = None

    def set_cell_color(self, r, c, color):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self.canvas.itemconfig(self.grid_refs[r][c], fill=color)

    def exit_fullscreen(self):
        self.window.attributes("-fullscreen", False)
        # If we want to close window entirely on 'q':
        cv2.destroyAllWindows()
        self.window.destroy()

