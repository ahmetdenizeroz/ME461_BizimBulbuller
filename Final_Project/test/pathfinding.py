# pathfinding.py
from queue import PriorityQueue

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(start, goal, rows, cols, obstacles=None):
    """Returns a list of cells in the path from start to goal, or None if no path."""
    if obstacles is None:
        obstacles = set()

    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    g_score = {(r, c): float("inf") for r in range(rows) for c in range(cols)}
    g_score[start] = 0
    f_score = {(r, c): float("inf") for r in range(rows) for c in range(cols)}
    f_score[start] = manhattan(start, goal)

    while not open_set.empty():
        _, current = open_set.get()
        if current == goal:
            return reconstruct_path(came_from, current)

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = current[0] + dx, current[1] + dy
            neighbor = (nr, nc)
            if 0 <= nr < rows and 0 <= nc < cols and neighbor not in obstacles:
                temp_g = g_score[current] + 1
                if temp_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = temp_g
                    f_score[neighbor] = temp_g + manhattan(neighbor, goal)
                    open_set.put((f_score[neighbor], neighbor))
    return None

def reconstruct_path(came_from, current):
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

