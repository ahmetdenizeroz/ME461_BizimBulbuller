import pygame
import random
import heapq
from collections import deque

# Constants
MARGIN = 2
ALGORITHMS = ["A*"]

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
VISITED_COLOR = (173, 216, 230)  # Light Blue
PATH_COLOR = (255, 215, 0)       # Gold
START_COLOR = (0, 255, 0)        # Green
TARGET_COLOR = (255, 0, 0)       # Red
TEXT_COLOR = (0, 0, 0)

# Initialize the game
pygame.init()
info = pygame.display.Info()

print(f"Your screen width is: {info.current_w} and screen height is: {info.current_h}")

SCREEN_WIDTH = int(input("Please enter the required width: "))
SCREEN_HEIGHT = int(input("Please enter the required height "))
nObjects = int(input("Please enter the number of objects required: "))
maxnSteps = int(input("Please enter the maximum number steps: "))

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Pathfinding Algorithms Visualization")

font = pygame.font.SysFont("Arial", 20)

obstacleDict = {}

# Calculate grid size
GRID_ROWS = 30
GRID_COLS = 30
CELL_WIDTH = (SCREEN_WIDTH - (GRID_COLS + 1) * MARGIN) // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - 100 - (GRID_ROWS + 1) * MARGIN) // GRID_ROWS
CELL_SIZE = min(CELL_WIDTH, CELL_HEIGHT)
GRID_COLS = (SCREEN_WIDTH - MARGIN) // (CELL_SIZE + MARGIN)
GRID_ROWS = (SCREEN_HEIGHT - 100 - MARGIN) // (CELL_SIZE + MARGIN)

# Food Class
class Food():
    def __init__(food, shape, color, position, point):
        #Food Parameters
        food.shape = shape
        food.color = color
        food.position = position
        food.point = point

class Food1(Food):
    def __init__(F1, position):
        super().__init__("Circle", (255, 0 ,0), position, 9)

class Food2(Food):
    def __init__(F2, position):
        super().__init__("Circle", (0, 255, 0), position, -2)
        
class Food3(Food):
    def __init__(F3, position):
        super().__init__("Circle", (0, 0, 255), position, 5)

class Food4(Food):
    def __init__(F4, position):
        super().__init__("Triangle" , (255, 0, 0), position, 7)

class Food5(Food):
    def __init__(F5, position):
        super().__init__("Triangle", (0, 255, 0), position, -6)

class Food6(Food):
    def __init__(F6, position):
        super().__init__("Triangle", (0, 0, 255), position, 3)

class Food7(Food):
    def __init__(F7, position):
        super().__init__("Square", (255, 0, 0), position, 1)

class Food8(Food):
    def __init__(F8, position):
        super().__init__("Square", (0, 255, 0), position, -4)

class Food9(Food):
    def __init__(F9, position):
        super().__init__("Square", (0, 0, 255), position, -8)

# Helper Functions
def draw_ui(selected_algorithm):

    """Draws the algorithm selection UI."""

    ui_start_y = SCREEN_HEIGHT - 90
    screen.fill(WHITE, (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
    text = font.render("Select Algorithm:", True, TEXT_COLOR)
    screen.blit(text, (10, ui_start_y))

    for i, algorithm in enumerate(ALGORITHMS):
        color = BLACK if algorithm == selected_algorithm else GRAY
        pygame.draw.circle(screen, color, (150 + i * 150, ui_start_y + 20), 10)
        label = font.render(algorithm, True, TEXT_COLOR)
        screen.blit(label, (165 + i * 150, ui_start_y + 10))
    pygame.display.flip()

def generate_grid():

    """Generates a random grid with obstacles."""

    grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    obstacle_count = nObjects

    for obstacle in range(obstacle_count):
        x, y = random.randint(0, GRID_ROWS - 1), random.randint(0, GRID_COLS - 1)
        obstacleDict[obstacle+1] = eval(f"Food{random.randint(1, 9)}(({x}, {y}))")
        print(obstacleDict)
        grid[x][y] = 1
    return grid

def neighbors(node):

    """Returns valid neighbors of a node in the grid."""

    row, col = node
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
    result = []
    for dr, dc in directions:
        r, c = row + dr, col + dc
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS and grid[r][c] == 0:
            result.append((r, c))
    return result

def update_frame(grid, start, target, visited=None, path=None):

    """Updates only the changed portions of the grid."""

    updated_rects = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            #color = GRAY if grid[row][col] == 1 else WHITE
            color = WHITE
            if path and (row, col) in path:
                color = PATH_COLOR
            elif visited and (row, col) in visited:
                color = VISITED_COLOR
            if (row, col) == start:
                color = START_COLOR
            elif (row, col) == target:
                color = TARGET_COLOR
            rect = pygame.Rect(
                col * (CELL_SIZE + MARGIN) + MARGIN,
                row * (CELL_SIZE + MARGIN) + MARGIN,
                CELL_SIZE,
                CELL_SIZE,
            )
            pygame.draw.rect(screen, color, rect)
            updated_rects.append(rect)

    for food in obstacleDict.values():
        shape = food.shape
        color = food.color
        position = food.position

        # Draw the outer shape
        if shape == "Circle":
            pygame.draw.circle(screen, color, (position[0] + CELL_SIZE // 2, position[1] + CELL_SIZE // 2), CELL_SIZE // 2)
            print("mf")
        elif shape == "Triangle":
            pygame.draw.polygon(screen, color, [(position[0] + CELL_SIZE // 2, position[1]), (position[0], position[1] + CELL_SIZE), (position[0] + CELL_SIZE, position[1] + CELL_SIZE)])
        elif shape == "Square":
            break
                #pygame.draw.rect(self.screen, color, (position[0] + self.cell))

    pygame.display.update(updated_rects)

def get_selected_algorithm(pos):

    """Determines which algorithm was selected based on the click position."""

    ui_start_y = SCREEN_HEIGHT - 90
    for i, algorithm in enumerate(ALGORITHMS):
        center_x, center_y = 150 + i * 150, ui_start_y + 20
        if (pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2 <= 100:
            return algorithm
    return None

# Pathfinding Algorithms

def a_star(grid, start, target):
    pq = [(heuristic(start, target), 0, start)]
    visited = set()
    parent = {}
    cost = {start: 0}
    dosuccess = False
    while pq:
        _, current_cost, current = heapq.heappop(pq)
        if current in visited:
            continue
        visited.add(current)
        if current == target:
            dosuccess = True
            break
        for neighbor in neighbors(current):
            new_cost = current_cost + 1
            if neighbor not in cost or new_cost < cost[neighbor]:
                cost[neighbor] = new_cost
                parent[neighbor] = current
                priority = new_cost + heuristic(neighbor, target)
                heapq.heappush(pq, (priority, new_cost, neighbor))
    path = reconstruct_path(parent, start, target)
    return visited, path, dosuccess

def heuristic(node, target):
    return abs(node[0] - target[0]) + abs(node[1] - target[1])

def reconstruct_path(parent, start, target):
    path = []
    current = target
    while current != start:
        path.append(current)
        current = parent.get(current)
        if current is None:
            return []
    path.append(start)
    return path[::-1]

# Main Function
def main():
    global grid
    grid = generate_grid()
    start, target = None, None
    selected_algorithm = None
    visited, path = None, None
    running = True
    while running:
        update_frame(grid, start, target, visited, path)
        draw_ui(selected_algorithm)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    grid = generate_grid()
                    start, target, visited, path = None, None, None, None
                elif event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if y < SCREEN_HEIGHT - 100:
                    row, col = y // (CELL_SIZE + MARGIN), x // (CELL_SIZE + MARGIN)
                    if grid[row][col] == 1:
                        continue
                    if not start:
                        start = (row, col)
                    elif not target:
                        target = (row, col)
                    else:
                        grid[row][col] = 1 - grid[row][col]
                else:
                    selected_algorithm = get_selected_algorithm((x, y))

            elif event.type == pygame.MOUSEBUTTONUP:
                if selected_algorithm and start and target:
                    if selected_algorithm == "A*":
                        visited, path, dosuccess = a_star(grid, start, target)
                        if not dosuccess:
                            print("No solution found")

    pygame.quit()

if __name__ == "__main__":
    main()
