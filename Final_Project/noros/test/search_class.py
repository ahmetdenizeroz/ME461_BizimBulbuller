from queue import PriorityQueue

class SearchClass:
    """
    A simple A* grid search algorithm implementation that also takes into account:
      - Robot orientation (in multiples of 90 degrees)
      - Movement and rotation costs
      - Optional cell rewards/penalties
      - Weight factors for time vs. reward

    Usage (basic):
        1. Initialize the class.
        2. Set grid dimensions using `set_grid_dimensions(rows, cols)`.
        3. (Optional) Add obstacles using `add_obstacle(row, col)`.
        4. (Optional) Set speeds, rewards, etc.
        5. Call `find_path(start, goal, initial_direction=0)` to retrieve the path.

    Attributes:
        rows (int): Number of rows in the grid.
        cols (int): Number of columns in the grid.
        obstacles (set): Set of cells (row, col) that are blocked.
        linear_speed (float): Robot's linear speed (cells per unit time).
        rotation_speed (float): Time cost for a 90-degree rotation.
        w_time (float): Weight factor for time cost in the cost function.
        w_reward (float): Weight factor for reward in the cost function.
        cell_rewards (dict): A dictionary mapping (row, col) -> reward value.
    """

    def __init__(self):
        """
        Initializes the SearchClass with default grid dimensions, speeds, and no obstacles.
        """
        self.rows = 0
        self.cols = 0
        self.obstacles = set()  # set of (row, col) tuples representing blocked cells

        # New additions
        self.linear_speed = 1.0      # default: 1 cell per unit time
        self.rotation_speed = 1.0    # default: 1 unit time for a 90° turn

        # Weights for cost function
        self.w_time = 1.0
        self.w_reward = 1.0

        # Reward map: cell -> float (positive for reward, negative for penalty)
        self.cell_rewards = {}

    # ---------------------
    # Old Basic Methods
    # ---------------------

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

    # ---------------------
    # New/Extended Methods
    # ---------------------

    def set_speeds(self, linear_speed, rotation_speed):
        """
        Sets the linear and rotation speeds for the robot.

        Args:
            linear_speed (float): Robot's linear speed (cells per unit time).
            rotation_speed (float): Time cost for a 90-degree rotation.
        """
        self.linear_speed = linear_speed
        self.rotation_speed = rotation_speed

    def set_weights(self, w_time=1.0, w_reward=1.0):
        """
        Sets the weighting factors for the cost function.

        Args:
            w_time (float): Weight for time cost.
            w_reward (float): Weight for reward.
        """
        self.w_time = w_time
        self.w_reward = w_reward

    def set_cell_reward(self, row, col, value):
        """
        Assigns a reward (positive) or penalty (negative) for stepping on a specific cell.

        Args:
            row (int): Row index of the cell.
            col (int): Column index of the cell.
            value (float): Reward (positive) or penalty (negative) value.
        """
        if self._in_bounds((row, col)):
            self.cell_rewards[(row, col)] = value
        else:
            print(f"Attempted to set reward/penalty out of bounds at ({row}, {col})")

    def clear_rewards(self):
        """
        Clears all assigned rewards/penalties.
        """
        self.cell_rewards.clear()

    # ---------------------
    # Modified A* Search
    # ---------------------

    def find_path(self, start, goal, initial_direction=0):
        """
        Finds the path from a start cell to a goal cell using A*.
        Incorporates orientation, time cost, and optional cell rewards.

        Args:
            start (tuple): Starting cell as (row, col).
            goal (tuple): Goal cell as (row, col).
            initial_direction (int): Initial heading in degrees 
                                     (0, 90, 180, or 270). 
                                     Defaults to 0 (facing "right").

        Returns:
            list: List of (row, col, direction) tuples representing
                  the path from start to goal, including orientation.
                  Returns an empty list if no path is found.
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

        # A* using (row, col, direction) as the state
        open_set = PriorityQueue()
        start_state = (start[0], start[1], self._normalize_dir(initial_direction))
        
        # We'll store (f_score, (row, col, direction)) in the queue
        open_set.put((0, start_state))
        open_set_hash = {start_state}

        came_from = {}  # map: state -> predecessor state
        g_score = {}
        f_score = {}

        # Initialize g_score, f_score for all possible states 
        # (in practice, you might do lazy initialization for memory efficiency).
        for r in range(self.rows):
            for c in range(self.cols):
                for d in [0, 90, 180, 270]:
                    g_score[(r, c, d)] = float('inf')
                    f_score[(r, c, d)] = float('inf')

        g_score[start_state] = 0
        f_score[start_state] = self._heuristic(start, goal)

        while not open_set.empty():
            current_f, current_state = open_set.get()
            open_set_hash.discard(current_state)

            if (current_state[0], current_state[1]) == goal:
                # Reached goal cell (regardless of final orientation).
                return self._reconstruct_path(came_from, current_state)

            current_r, current_c, current_dir = current_state

            for next_state, step_cost in self._get_neighbors_and_costs(current_r, current_c, current_dir):
                # If next cell is an obstacle, skip
                nr, nc, ndir = next_state
                if (nr, nc) in self.obstacles:
                    continue

                # Tentative cost to neighbor
                tentative_g_score = g_score[current_state] + step_cost

                if tentative_g_score < g_score[next_state]:
                    came_from[next_state] = current_state
                    g_score[next_state] = tentative_g_score
                    # Standard A* f = g + h
                    f_score[next_state] = tentative_g_score + self._heuristic((nr, nc), goal)

                    if next_state not in open_set_hash:
                        open_set.put((f_score[next_state], next_state))
                        open_set_hash.add(next_state)

        print("No path found from start to goal.")
        return []

    # ---------------------
    # Internal Helpers
    # ---------------------

    def _heuristic(self, a, b):
        """
        Heuristic function for A* (Manhattan distance ignoring orientation).

        Args:
            a (tuple): Cell a as (row, col).
            b (tuple): Cell b as (row, col).

        Returns:
            int: Manhattan distance between cell a and cell b.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _get_neighbors_and_costs(self, r, c, direction):
        """
        Generates neighboring states and calculates the cost to move
        from (r, c, direction) to each neighbor.

        Each neighbor can be one of 4 directions (0, 90, 180, 270).
        We include the rotation cost (if direction changes) plus the
        move cost (1 cell / linear_speed), minus any reward for the next cell.

        Returns:
            list of (next_state, cost) pairs, where next_state = (nr, nc, ndir).
        """
        neighbors = []
        # Direction -> (dr, dc)
        direction_map = {
            0:   (0, +1),   # right
            90:  (+1, 0),   # down
            180: (0, -1),   # left
            270: (-1, 0)    # up
        }

        for ndir, (dr, dc) in direction_map.items():
            nr, nc = r + dr, c + dc
            if not self._in_bounds((nr, nc)):
                continue

            # Calculate time cost: rotation + move
            rot_cost = self._rotation_cost(direction, ndir)
            move_cost = 1.0 / self.linear_speed
            time_cost = rot_cost + move_cost

            # Reward (or penalty) for stepping onto (nr, nc)
            cell_reward = self.cell_rewards.get((nr, nc), 0.0)

            # Weighted cost function
            cost = (self.w_time * time_cost) - (self.w_reward * cell_reward)

            neighbors.append(((nr, nc, ndir), cost))

        return neighbors

    def _rotation_cost(self, current_dir, next_dir):
        """
        Computes the time cost to rotate from current_dir to next_dir.
        Both directions are in {0, 90, 180, 270} degrees.

        Returns:
            float: rotation cost in time units.
        """
        # minimal rotation difference in multiples of 90
        diff = abs(next_dir - current_dir) % 360
        # e.g., 270 is effectively a 90 turn in the other direction
        if diff > 180:
            diff = 360 - diff

        # Each 90° rotation costs rotation_speed
        return (diff / 90.0) * self.rotation_speed

    def _normalize_dir(self, d):
        """
        Ensures the direction is one of {0, 90, 180, 270}.
        """
        d = d % 360
        # Round to nearest multiple of 90 if user gave an odd angle
        # This is optional, but helps if user tries e.g. 45 degrees.
        offsets = [0, 90, 180, 270]
        closest = min(offsets, key=lambda x: abs(x - d))
        return closest

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
            came_from (dict): Dictionary mapping states to their predecessors.
            current (tuple): Current state as (row, col, direction).

        Returns:
            list: List of (row, col, direction) from start to goal.
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

