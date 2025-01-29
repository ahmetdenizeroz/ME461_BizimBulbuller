# search_class.py
from queue import PriorityQueue

class SearchClass:
    """
    A simple A* grid search algorithm implementation.
    
    Usage:
        1. Initialize the class.
        2. Set grid dimensions using `set_grid_dimensions(rows, cols)`.
        3. (Optional) Add obstacles using `add_obstacle(row, col)`.
        4. Call `find_path(start, goal)` to retrieve the path.
        
    Attributes:
        rows (int): Number of rows in the grid.
        cols (int): Number of columns in the grid.
        obstacles (set): Set of cells that are blocked and cannot be traversed.
    """
    
    def __init__(self):
        """
        Initializes the SearchClass with default grid dimensions and no obstacles.
        """
        self.rows = 0
        self.cols = 0
        self.obstacles = set()  # Set of (row, col) tuples representing blocked cells

    def set_grid_dimensions(self, rows, cols):
        """
        Sets the dimensions of the grid.
        
        Args:
            rows (int): Number of rows in the grid.
            cols (int): Number of columns in the grid.
        """
        self.rows = rows
        self.cols = cols

    def add_obstacle(self, row, col):
        """
        Adds an obstacle to the grid at the specified cell.
        
        Args:
            row (int): Row index of the obstacle.
            col (int): Column index of the obstacle.
        """
        if self._in_bounds((row, col)):
            self.obstacles.add((row, col))
        else:
            print(f"Attempted to add obstacle out of bounds at ({row}, {col})")

    def remove_obstacle(self, row, col):
        """
        Removes an obstacle from the grid at the specified cell.
        
        Args:
            row (int): Row index of the obstacle.
            col (int): Column index of the obstacle.
        """
        self.obstacles.discard((row, col))

    def clear_obstacles(self):
        """
        Clears all obstacles from the grid.
        """
        self.obstacles.clear()

    def find_path(self, start, goal):
        """
        Finds the shortest path from start to goal using the A* algorithm.
        
        Args:
            start (tuple): Starting cell as (row, col).
            goal (tuple): Goal cell as (row, col).
        
        Returns:
            list: List of cells representing the path from start to goal.
                  Each cell is a tuple (row, col). Returns an empty list if no path is found.
        """
        if not self._in_bounds(start) or not self._in_bounds(goal):
            print("Start or goal is out of grid bounds.")
            return []
        
        if start in self.obstacles:
            print("Start position is blocked by an obstacle.")
            return []
        
        if goal in self.obstacles:
            print("Goal position is blocked by an obstacle.")
            return []

        open_set = PriorityQueue()
        open_set.put((0, start))  # (f_score, cell)
        came_from = {}  # For path reconstruction
        
        # Initialize g_score and f_score for all cells
        g_score = { (r, c): float('inf') for r in range(self.rows) for c in range(self.cols) }
        f_score = { (r, c): float('inf') for r in range(self.rows) for c in range(self.cols) }
        
        g_score[start] = 0
        f_score[start] = self._heuristic(start, goal)
        
        open_set_hash = {start}  # To keep track of items in the PriorityQueue

        while not open_set.empty():
            current_f, current = open_set.get()
            open_set_hash.discard(current)

            if current == goal:
                return self._reconstruct_path(came_from, current)
            
            for neighbor in self._neighbors(current):
                if neighbor in self.obstacles:
                    continue  # Skip blocked cells
                
                tentative_g_score = g_score[current] + 1  # Assuming uniform cost
                
                if tentative_g_score < g_score[neighbor]:
                    # This path to neighbor is better than any previous one
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal)
                    
                    if neighbor not in open_set_hash:
                        open_set.put((f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        # No path found
        print("No path found from start to goal.")
        return []

    def _heuristic(self, a, b):
        """
        Heuristic function for A* (Manhattan distance).
        
        Args:
            a (tuple): Cell a as (row, col).
            b (tuple): Cell b as (row, col).
        
        Returns:
            int: Manhattan distance between cell a and cell b.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _neighbors(self, cell):
        """
        Generates valid neighboring cells (up, down, left, right) for a given cell.
        
        Args:
            cell (tuple): Current cell as (row, col).
        
        Yields:
            tuple: Neighboring cell as (row, col).
        """
        (r, c) = cell
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        for dr, dc in directions:
            neighbor = (r + dr, c + dc)
            if self._in_bounds(neighbor):
                yield neighbor

    def _in_bounds(self, cell):
        """
        Checks if a cell is within the grid bounds.
        
        Args:
            cell (tuple): Cell as (row, col).
        
        Returns:
            bool: True if the cell is within bounds, False otherwise.
        """
        (r, c) = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def _reconstruct_path(self, came_from, current):
        """
        Reconstructs the path from start to goal.
        
        Args:
            came_from (dict): Dictionary mapping cells to their predecessors.
            current (tuple): Current cell as (row, col).
        
        Returns:
            list: List of cells representing the path from start to goal.
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()  # Optional: start to goal
        return path

