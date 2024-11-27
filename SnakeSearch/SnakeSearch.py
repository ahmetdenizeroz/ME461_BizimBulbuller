import pygame
import random
import heapq
from collections import deque

# Constants
MARGIN = 2  # Margin between cells
ALGORITHMS = ["BFS", "DFS", "UCS", "Greedy", "A*"]  # Available algorithms

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
VISITED_COLOR = (173, 216, 230)  # Light Blue for visited nodes
PATH_COLOR = (255, 215, 0)       # Gold for the solution path
START_COLOR = (0, 0, 0)       # Green for the start node
TARGET_COLOR = (250, 100, 150)       # Red for the target node
TEXT_COLOR = (0, 0, 0)           # Black for text

# Initialize Pygame and get screen dimensions
pygame.init()
info = pygame.display.Info()
print(f"Your screen width is: {info.current_w} and screen height is: {info.current_h}")
obstacle_count = int(input("Please enter the required number of obstacles: "))
# Screen dimensions input
SCREEN_WIDTH = int(input("Please enter the required width: "))
SCREEN_HEIGHT = int(input("Please enter the required height: "))

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pathfinding Algorithms Visualization")
font = pygame.font.SysFont("Arial", 20)

# Calculate grid size
GRID_ROWS = 30
GRID_COLS = 30
CELL_WIDTH = (SCREEN_WIDTH - (GRID_COLS + 1) * MARGIN) // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - 100 - (GRID_ROWS + 1) * MARGIN) // GRID_ROWS
CELL_SIZE = min(CELL_WIDTH, CELL_HEIGHT)
GRID_COLS = (SCREEN_WIDTH - MARGIN) // (CELL_SIZE + MARGIN)
GRID_ROWS = (SCREEN_HEIGHT - 100 - MARGIN) // (CELL_SIZE + MARGIN)

class Food:
    def __init__(self, shape, color, position):
        self.shape = shape
        self.color = color
        self.position = position
        self.points = 0

def draw_ui(selected_algorithm):
    """
    Draws the algorithm selection UI at the bottom of the screen.
    """
    ui_start_y = SCREEN_HEIGHT - 90  # UI panel's vertical start position
    screen.fill(WHITE, (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))  # Clear UI area
    text = font.render("Select Algorithm:", True, TEXT_COLOR)
    screen.blit(text, (10, ui_start_y))  # Display prompt
    for i, algorithm in enumerate(ALGORITHMS):
        # Highlight the selected algorithm
        color = BLACK if algorithm == selected_algorithm else GRAY
        pygame.draw.circle(screen, color, (175 + i * 175, ui_start_y + 20), 10)
        label = font.render(algorithm, True, TEXT_COLOR)
        screen.blit(label, (190 + i * 175, ui_start_y + 10))
    pygame.display.flip()


def generate_grid():
    """
    Generates a random grid with obstacles.
    """
    food_objects = {}
    grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]  # Empty grid

    #obstacle_count = (GRID_ROWS * GRID_COLS) // 4  # 25% of cells are obstacles

    for _ in range(obstacle_count):
        x, y = random.randint(0, GRID_ROWS - 1), random.randint(0, GRID_COLS - 1)
        grid[x][y] = 1  # Mark cell as an obstacle
        shape = random.choice(["circle", "triangle", "square"])
        color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255)])
        food_objects[(x, y)] = Food(shape, color, (x, y))
    return grid, food_objects


def neighbors(node):
    """
    Returns valid neighbors (adjacent cells) of a node in the grid.
    """
    row, col = node
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
    result = []
    for dr, dc in directions:
        r, c = row + dr, col + dc
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS and grid[r][c] == 0:
            result.append((r, c))
    return result


def update_frame(grid,foods, start, target, visited=None, path=None):
    """
    Updates the grid display, highlighting the visited nodes, the solution path, and redraws grid lines.
    """
    screen.fill(WHITE)  # Clear the screen to redraw

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            # Determine cell color
            #color = GRAY if grid[row][col] == 1 else WHITE  # Obstacle or empty
            color = WHITE if grid[row][col] == 1 else WHITE  # Obstacle or empty
            if path and (row, col) in path:
                color = PATH_COLOR  # Highlight solution path
            elif visited and (row, col) in visited:
                color = VISITED_COLOR  # Highlight visited cells
            if (row, col) == start:
                color = START_COLOR  # Start node
            elif (row, col) == target:
                color = TARGET_COLOR  # Target node
            
            # Draw the cell rectangle
            rect = pygame.Rect(
                col * (CELL_SIZE + MARGIN) + MARGIN,
                row * (CELL_SIZE + MARGIN) + MARGIN,
                CELL_SIZE,
                CELL_SIZE,
            )
            pygame.draw.rect(screen, color, rect)

    # Draw grid lines to ensure visibility
    for row in range(GRID_ROWS + 1):
        pygame.draw.line(
            screen,
            BLACK,
            (MARGIN, row * (CELL_SIZE + MARGIN)),
            (GRID_COLS * (CELL_SIZE + MARGIN), row * (CELL_SIZE + MARGIN))
        )
    for col in range(GRID_COLS + 1):
        pygame.draw.line(
            screen,
            BLACK,
            (col * (CELL_SIZE + MARGIN), MARGIN),
            (col * (CELL_SIZE + MARGIN), GRID_ROWS * (CELL_SIZE + MARGIN))
        )

    for food in foods.values():
        col = food.position[1]
        row = food.position[0]
        if food.shape == "circle":
            pygame.draw.circle(
                screen, food.color,
                (col * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2,
                 row * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2),
                 CELL_SIZE // 2
            )

        elif food.shape == "square":
            pygame.draw.rect(
                screen, food.color,
                pygame.Rect(
                    col * (CELL_SIZE + MARGIN) + MARGIN,
                    row * (CELL_SIZE + MARGIN) + MARGIN,
                    CELL_SIZE,
                    CELL_SIZE,
                )
            )
        elif food.shape == "triangle":
            pygame.draw.polygon(
                screen, food.color,
                [(col * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2, row * (CELL_SIZE + MARGIN) + MARGIN),
                 (col * (CELL_SIZE + MARGIN) + MARGIN, row * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE),
                 (col * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE, row * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE)]
            )

    pygame.display.flip()  # Update the entire display



def get_selected_algorithm(pos):
    """
    Determines which algorithm was selected based on mouse click position.
    """
    ui_start_y = SCREEN_HEIGHT - 90
    for i, algorithm in enumerate(ALGORITHMS):
        center_x, center_y = 175 + i * 175, ui_start_y + 20
        if (pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2 <= 100:  # Inside circle
            return algorithm
    return None


def show_no_solution_message():
    """
    Displays a 'No Solution' message and restarts the game with a new grid.
    """
    screen.fill(WHITE)
    message = font.render("NO SOLUTION FOUND!", True, (255, 0, 0))  # Red text
    sub_message = font.render("Press R to restart the game.", True, TEXT_COLOR)
    sub_message_two = font.render("Press ESC to close the game", True, TEXT_COLOR)
    screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
    screen.blit(sub_message, (SCREEN_WIDTH // 2 - sub_message.get_width() // 2, SCREEN_HEIGHT // 2 + 10))
    screen.blit(sub_message_two, (SCREEN_WIDTH // 2 - sub_message.get_width() // 2, SCREEN_HEIGHT // 2 + 70))
    pygame.display.flip()

    # Restart the game
    global grid
    grid = generate_grid()[0]  # Regenerate grid
    pygame.time.wait(2000)  # Pause briefly before resuming


### Pathfinding Algorithms ###

def bfs(grid, start, target):
    """Breadth-First Search."""
    queue = deque([start])
    visited = set([start])
    parent = {}

    while queue:
        current = queue.popleft()
        if current == target:
            return visited, reconstruct_path(parent, start, target), True
        for neighbor in neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
    return visited, [], False  # No solution found


def dfs(grid, start, target):
    """Depth-First Search."""
    stack = [start]
    visited = set([start])
    parent = {}

    while stack:
        current = stack.pop()
        if current == target:
            return visited, reconstruct_path(parent, start, target), True
        for neighbor in neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)
    return visited, [], False  # No solution found


def ucs(grid, start, target):
    """Uniform Cost Search."""
    pq = [(0, start)]  # Priority queue with cost and node
    visited = set()
    parent = {}
    cost = {start: 0}

    while pq:
        current_cost, current = heapq.heappop(pq)
        if current in visited:
            continue
        visited.add(current)
        if current == target:
            return visited, reconstruct_path(parent, start, target), True
        for neighbor in neighbors(current):
            new_cost = current_cost + 1  # All edges have uniform cost
            if neighbor not in cost or new_cost < cost[neighbor]:
                cost[neighbor] = new_cost
                parent[neighbor] = current
                heapq.heappush(pq, (new_cost, neighbor))
    return visited, [], False  # No solution found


def greedy(grid, start, target):
    """Greedy Best-First Search."""
    pq = [(heuristic(start, target), start)]
    visited = set()
    parent = {}

    while pq:
        _, current = heapq.heappop(pq)
        if current in visited:
            continue
        visited.add(current)
        if current == target:
            return visited, reconstruct_path(parent, start, target), True
        for neighbor in neighbors(current):
            if neighbor not in visited:
                parent[neighbor] = current
                heapq.heappush(pq, (heuristic(neighbor, target), neighbor))
    return visited, [], False  # No solution found


def a_star(grid, start, target):
    """A* Search."""
    pq = [(heuristic(start, target), 0, start)]  # (f, g, node)
    visited = set()
    parent = {}
    cost = {start: 0}

    while pq:
        _, current_cost, current = heapq.heappop(pq)
        if current in visited:
            continue
        visited.add(current)
        if current == target:
            return visited, reconstruct_path(parent, start, target), True
        for neighbor in neighbors(current):
            new_cost = current_cost + 1
            if neighbor not in cost or new_cost < cost[neighbor]:
                cost[neighbor] = new_cost
                parent[neighbor] = current
                heapq.heappush(pq, (new_cost + heuristic(neighbor, target), new_cost, neighbor))
    return visited, [], False  # No solution found


def heuristic(node, target):
    """Manhattan Distance Heuristic."""
    return abs(node[0] - target[0]) + abs(node[1] - target[1])


def reconstruct_path(parent, start, target):
    """Reconstructs the path from start to target using the parent dictionary."""
    path = []
    current = target
    while current != start:
        path.append(current)
        current = parent.get(current)
        if current is None:
            return []  # No path exists
    path.append(start)
    return path[::-1]  # Reverse the path


# Main Function
def main():
    global grid
    grid, foods = generate_grid()# Initial grid generation
    start, target = None, None  # Start and target positions
    selected_algorithm = None  # No algorithm selected initially
    visited, path = None, None  # Tracking visited nodes and the solution path
    running = True
    needs_update = True  # Initial update to draw the grid and UI

    while running:
        if needs_update:
            update_frame(grid,foods, start, target, visited, path)  # Update grid visualization
            draw_ui(selected_algorithm)  # Update algorithm selection UI
            needs_update = False  # Reset the update flag

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Reset the grid
                    grid, foods = generate_grid()
                    start, target, visited, path = None, None, None, None
                    needs_update = True  # Trigger UI update
                elif event.key == pygame.K_ESCAPE:  # Exit the program
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if y < SCREEN_HEIGHT - 100:  # Grid area
                    row, col = y // (CELL_SIZE + MARGIN), x // (CELL_SIZE + MARGIN)
                    if grid[row][col] == 1:
                        continue  # Ignore obstacle cells
                    if not start:
                        start = (row, col)
                    elif not target:
                        target = (row, col)
                    else:
                        grid[row][col] = 1 - grid[row][col]  # Toggle obstacle
                    needs_update = True  # Trigger UI update
                else:  # UI area
                    selected_algorithm = get_selected_algorithm((x, y))
                    needs_update = True  # Trigger UI update

            elif event.type == pygame.MOUSEBUTTONUP:
                if selected_algorithm and start and target:
                    if selected_algorithm == "BFS":
                        visited, path, success = bfs(grid, start, target)
                    elif selected_algorithm == "DFS":
                        visited, path, success = dfs(grid, start, target)
                    elif selected_algorithm == "UCS":
                        visited, path, success = ucs(grid, start, target)
                    elif selected_algorithm == "Greedy":
                        visited, path, success = greedy(grid, start, target)
                    elif selected_algorithm == "A*":
                        visited, path, success = a_star(grid, start, target)

                    if not success:
                        show_no_solution_message()
                        start, target, visited, path = None, None, None, None
                    needs_update = True  # Trigger UI update for result

    pygame.quit()



if __name__ == "__main__":
    main()


