# gui.py
import tkinter as tk
import time
from pathfinding import a_star

class PathfindingGUI:
    def __init__(self, root, rows=3, cols=4, cell_size=100):
        self.root = root
        self.root.title("A* Pathfinding on 3x4 Grid")
        
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        
        self.start = None
        self.goal = None
        self.obstacles = set()
        self.path_cells = []
        
        # Robot location in (row,col):
        self.robot_cell = None

        self.canvas = tk.Canvas(root, width=self.cols*self.cell_size, height=self.rows*self.cell_size)
        self.canvas.pack()

        self.grid_refs = [[None for _ in range(cols)] for _ in range(rows)]
        self.draw_grid()
        
        self.status_label = tk.Label(root, text="Select start and goal", font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        self.canvas.bind("<Button-1>", self.on_click)

    def draw_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                x1, y1 = c*self.cell_size, r*self.cell_size
                x2, y2 = x1+self.cell_size, y1+self.cell_size
                rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")
                self.grid_refs[r][c] = rect_id

    def on_click(self, event):
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        
        if (row, col) == self.start:
            self.start = None
            self.set_cell_color(row, col, "white")
        elif (row, col) == self.goal:
            self.goal = None
            self.set_cell_color(row, col, "white")
        elif self.start is None:
            self.start = (row, col)
            self.set_cell_color(row, col, "green")
        elif self.goal is None:
            self.goal = (row, col)
            self.set_cell_color(row, col, "red")
            self.auto_update_path()

    def auto_update_path(self):
        if self.start and self.goal:
            path = a_star(self.start, self.goal, self.rows, self.cols, self.obstacles)
            if path:
                self.path_cells = path
                self.draw_path()
                self.status_label.config(text="Path found.")
            else:
                self.status_label.config(text="No path found")

    def draw_path(self):
        # Clear intermediate cells first
        for r in range(self.rows):
            for c in range(self.cols):
                color = "white"
                if (r, c) == self.start:
                    color = "green"
                elif (r, c) == self.goal:
                    color = "red"
                self.set_cell_color(r, c, color)
        # highlight path
        for step in self.path_cells:
            if step != self.start and step != self.goal:
                self.set_cell_color(step[0], step[1], "lightblue")

    def set_cell_color(self, row, col, color):
        rect_id = self.grid_refs[row][col]
        self.canvas.itemconfig(rect_id, fill=color)

    def set_robot_cell(self, row, col):
        """Externally call this to update the robot's location."""
        self.robot_cell = (row, col)
        self.update_grid()

    def update_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                color = "white"
                if (r, c) == self.start:
                    color = "green"
                elif (r, c) == self.goal:
                    color = "red"
                elif (r, c) in self.path_cells:
                    color = "lightblue"
                if self.robot_cell == (r, c):
                    color = "yellow"  # Robot shown in yellow
                self.set_cell_color(r, c, color)

