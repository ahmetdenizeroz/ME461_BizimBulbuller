import tkinter as tk
from queue import PriorityQueue
import socket
import time

# Pico's IP Address (Replace with actual IP)
PICO_IP = "192.168.66.106"
PORT = 8080

class PathfindingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("A* Pathfinding on 3x4 Grid")

        self.rows = 3
        self.cols = 4
        self.cell_size = 100
        self.start = None
        self.goal = None
        self.obstacles = set()
        self.path_cells = []
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        self.canvas = tk.Canvas(root, width=self.cols * self.cell_size, height=self.rows * self.cell_size)
        self.canvas.pack()

        self.draw_grid()
        self.canvas.bind("<Button-1>", self.on_click)

        # Status label
        self.status_label = tk.Label(root, text="Select start and goal", font=("Arial", 12))
        self.status_label.pack(pady=5)

        # Establish a connection to Pico
        self.client = None
        self.connect_to_pico()

    def connect_to_pico(self):
        """Connects to the Pico server and keeps the socket open."""
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((PICO_IP, PORT))
            print("Connected to Pico successfully!")
        except Exception as e:
            print(f"Error connecting to Pico: {e}")
            self.client = None  # Reset client if connection fails

    def heuristic(self, a, b):
        """Manhattan distance heuristic for A* pathfinding."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def draw_grid(self):
        """Draws a 3x4 grid."""
        for r in range(self.rows):
            for c in range(self.cols):
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                self.grid[r][c] = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")

    def on_click(self, event):
        """Handles user clicks for setting start, goal, and obstacles."""
        col = event.x // self.cell_size
        row = event.y // self.cell_size

        if (row, col) == self.start:
            self.start = None
            self.canvas.itemconfig(self.grid[row][col], fill="white")
        elif (row, col) == self.goal:
            self.goal = None
            self.canvas.itemconfig(self.grid[row][col], fill="white")
        elif self.start is None:
            self.start = (row, col)
            self.canvas.itemconfig(self.grid[row][col], fill="green")
        elif self.goal is None:
            self.goal = (row, col)
            self.canvas.itemconfig(self.grid[row][col], fill="red")
            self.auto_update_path()

    def auto_update_path(self):
        """Finds the path and starts step-by-step movement."""
        if self.start and self.goal:
            self.path_cells = self.find_path()
            if self.path_cells:
                self.draw_path()
                self.status_label.config(text="Following path...")
                self.move_step_by_step()
            else:
                self.status_label.config(text="No path found")

    def find_path(self):
        """Runs A* pathfinding and returns the path."""
        open_set = PriorityQueue()
        open_set.put((0, self.start))
        came_from = {}
        g_score = {node: float("inf") for row in range(self.rows) for node in [(row, col) for col in range(self.cols)]}
        g_score[self.start] = 0
        f_score = {node: float("inf") for row in range(self.rows) for node in [(row, col) for col in range(self.cols)]}
        f_score[self.start] = self.heuristic(self.start, self.goal)

        while not open_set.empty():
            _, current = open_set.get()

            if current == self.goal:
                return self.reconstruct_path(came_from, current)

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < self.rows and 0 <= neighbor[1] < self.cols and neighbor not in self.obstacles:
                    tentative_g_score = g_score[current] + 1

                    if tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, self.goal)
                        open_set.put((f_score[neighbor], neighbor))

        return None

    def reconstruct_path(self, came_from, current):
        """Reconstructs the shortest path."""
        path = []
        while current in came_from:
            current = came_from[current]
            if current != self.start and current != self.goal:
                path.append(current)
        return path[::-1]

    def draw_path(self):
        """Highlights the computed path in light blue."""
        for step in self.path_cells:
            self.canvas.itemconfig(self.grid[step[0]][step[1]], fill="lightblue")

    def move_step_by_step(self):
        """Moves step by step with a 0.5-second delay."""
        if not self.client:
            print("Error: No connection to Pico.")
            return

        for step in self.path_cells:
            self.update_grid(step[0], step[1])
            self.root.update_idletasks()  # Update GUI before sleeping
            time.sleep(0.5)  # Delay to visualize movement

            command = f"MOVE,{step[0]},{step[1]}"
            try:
                self.client.sendall(command.encode())

                # Wait for Pico confirmation
                response = self.client.recv(1024).decode().strip()
                if response.startswith("ARRIVED"):
                    print(f"Pico confirmed arrival at {step}")

            except Exception as e:
                print(f"Error in connection: {e}")
                break  # Exit loop if connection fails

        self.update_grid(self.goal[0], self.goal[1])

    def update_grid(self, row, col):
        """Updates the grid to show the robot's current position."""
        for r in range(self.rows):
            for c in range(self.cols):
                color = "white"
                if (r, c) == self.start:
                    color = "green"
                elif (r, c) == self.goal:
                    color = "red"
                elif (r, c) == (row, col):
                    color = "yellow"
                elif (r, c) in self.path_cells:
                    color = "lightblue"
                self.canvas.itemconfig(self.grid[r][c], fill=color)

if __name__ == "__main__":
    root = tk.Tk()
    app = PathfindingApp(root)
    root.mainloop()

