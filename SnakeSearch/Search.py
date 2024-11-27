import pygame
import random
import heapq

# Constants
MARGIN = 2


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
VISITED_COLOR = (173, 216, 230)  # Light Blue
PATH_COLOR = (255, 215, 0)       # Gold
START_COLOR = (0, 255, 0)        # Green
TARGET_COLOR = (255, 0, 0)       # Red

# Define Shape-Color combinations and their unique point values
SHAPE_COLOR_POINTS = {
    ("circle", (255, 0, 0)): -2,    # Red Circle
    ("circle", (0, 255, 0)): 1,    # Green Circle
    ("circle", (0, 0, 255)): -4,    # Blue Circle
    ("triangle", (255, 0, 0)): 3,  # Red Triangle
    ("triangle", (0, 255, 0)): -6,  # Green Triangle
    ("triangle", (0, 0, 255)): 5,  # Blue Triangle
    ("square", (255, 0, 0)): -8,    # Red Square
    ("square", (0, 255, 0)): 7,    # Green Square
    ("square", (0, 0, 255)): 9     # Blue Square
}

# Food Class
class Food:
    def __init__(self, shape, color, position):
        self.shape = shape
        self.color = color
        self.position = position
        self.points = SHAPE_COLOR_POINTS.get((shape, color), 0)

# Generate foods
def generate_food(grid, n_foods):
    food_objects = {}
    for food in range(n_foods):
        while True:
            row, col = random.randint(0, len(grid) - 1), random.randint(0, len(grid[0]) - 1)
            print(row, col)
            if grid[row][col] == 0:  # Place food only on empty cells
                grid[row][col] = 1
                shape = random.choice(["circle", "triangle", "square"])
                color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255)])
                food_objects[(row, col)] = Food(shape, color, (row, col))
                break
    return food_objects

# Heuristic function
def heuristic(node, target):
    return abs(node[0] - target[0]) + abs(node[1] - target[1])

# A* Pathfinding Algorithm
def a_star(grid, food_objects, start, target, max_steps):
    pq = [(0, start, 0, 0, [])]  # (negative_score, current, steps, collected_points, path)
    visited = set()

    while pq:
        negative_score, current, steps, collected_points, path = heapq.heappop(pq)

        if steps > max_steps:
            continue

        if current == target:
            return visited, path + [current], collected_points, steps

        if current in visited:
            continue

        visited.add(current)
        path = path + [current]

        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = current[0] + dr, current[1] + dc
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and (nr, nc) not in visited:
                neighbor_points = food_objects[(nr, nc)].points if (nr, nc) in food_objects else 0
                heapq.heappush(
                    pq, (
                        -(collected_points + neighbor_points),
                        (nr, nc),
                        steps + 1,
                        collected_points + neighbor_points,
                        path
                    )
                )

    return visited, [], None, None  # No solution

# Draw the grid
def draw_grid(grid, food_objects, visited, path, start, target):
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            color = WHITE
            if (row, col) == start:
                color = START_COLOR
            elif (row, col) == target:
                color = TARGET_COLOR
            elif (row, col) in path:
                color = PATH_COLOR
            elif (row, col) in visited:
                color = VISITED_COLOR
            pygame.draw.rect(
                screen,
                color,
                pygame.Rect(
                    col * (cell_size + MARGIN) + MARGIN,
                    row * (cell_size + MARGIN) + MARGIN,
                    cell_size,
                    cell_size,
                ),
            )
            # Draw foods
            if (row, col) in food_objects:
                food = food_objects[(row, col)]
                if food.shape == "circle":
                    pygame.draw.circle(
                        screen, food.color,
                        (col * (cell_size + MARGIN) + MARGIN + cell_size // 2,
                         row * (cell_size + MARGIN) + MARGIN + cell_size // 2),
                        cell_size // 2
                    )
                elif food.shape == "square":
                    pygame.draw.rect(
                        screen, food.color,
                        pygame.Rect(
                            col * (cell_size + MARGIN) + MARGIN,
                            row * (cell_size + MARGIN) + MARGIN,
                            cell_size,
                            cell_size,
                        )
                    )
                elif food.shape == "triangle":
                    pygame.draw.polygon(
                        screen, food.color,
                        [(col * (cell_size + MARGIN) + MARGIN + cell_size // 2, row * (cell_size + MARGIN) + MARGIN),
                         (col * (cell_size + MARGIN) + MARGIN, row * (cell_size + MARGIN) + MARGIN + cell_size),
                         (col * (cell_size + MARGIN) + MARGIN + cell_size, row * (cell_size + MARGIN) + MARGIN + cell_size)]
                    )
                # Display food points on grid
                font = pygame.font.Font(None, 20)
                text = font.render(str(food.points), True, BLACK)
                screen.blit(text, (
                    col * (cell_size + MARGIN) + MARGIN + cell_size // 4,
                    row * (cell_size + MARGIN) + MARGIN + cell_size // 4)
                )
    pygame.display.flip()

def show_no_solution_message(SCREEN_WIDTH, SCREEN_HEIGHT, grid_size, n_foods, font):
    """
    Displays a 'No Solution' message and restarts the game with a new grid.
    """
    global grid

    screen.fill(WHITE)
    message = font.render("NO SOLUTION FOUND!", True, (255, 0, 0))  # Red text
    sub_message = font.render("Press R to restart the game.", True, (0, 0, 0))
    sub_message_two = font.render("Press ESC to close the game", True, (0, 0, 0))
    screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
    screen.blit(sub_message, (SCREEN_WIDTH // 2 - sub_message.get_width() // 2, SCREEN_HEIGHT // 2 + 10))
    screen.blit(sub_message_two, (SCREEN_WIDTH // 2 - sub_message.get_width() // 2, SCREEN_HEIGHT // 2 + 70))
    pygame.display.flip()

    # Restart the game
    grid = [[0 for _ in range(grid_size[0])] for _ in range(grid_size[1])] # Regenerate grid
    pygame.time.wait(2000)

# Main Function
def main():
    global screen, cell_size

    needs_update = True

    pygame.init()  # Initialize pygame
    pygame.font.init()  # Initialize font module

    font = pygame.font.SysFont("Arial", 20)

    # User Input
    info = pygame.display.Info()
    cell_size = int(input("Enter Cell size (N for NxN): "))
    ScreenWidthCell = int(input(f"Considering the given Cell size, you can have maximum of {int(info.current_w // (cell_size + MARGIN))} cells in width."
                            f"Please enter the number of cells in width: "))
    ScreenHeightCell = int(input(f"Considering the given Cell size, you can have maximum of {int(info.current_h // (cell_size+ MARGIN))} cells height."
                            f"Please enter the number of cells in height: "))
    n_foods = int(input("Enter number of foods: "))
    max_steps = int(input("Enter maximum steps: "))

    grid_size = [ScreenWidthCell, ScreenHeightCell]

    screen = pygame.display.set_mode((ScreenWidthCell * (cell_size+MARGIN) + MARGIN, ScreenHeightCell * (cell_size+MARGIN) + MARGIN))

    pygame.display.set_caption("Pathfinding Game with Obstacles")

    # Initialize grid and foods
    grid = [[0 for _ in range(grid_size[0])] for _ in range(grid_size[1])]
    food_objects = generate_food(grid, n_foods)
    start, target = None, None
    visited, path, score, steps_taken = set(), [], None, None

    running = True
    while running:
        if needs_update:
            screen.fill(BLACK)
            draw_grid(grid, food_objects, visited, path if path else [], start, target)
            needs_update = False  # Reset the update flag

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Reset the grid
                    visited, path, score, steps_taken, start, target = set(), [], None, None, None, None
                    needs_update = True  # Trigger UI update
                elif event.key == pygame.K_ESCAPE:  # Exit the program
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                col, row = x // (cell_size + MARGIN), y // (cell_size + MARGIN)
                needs_update = True
                if not start:
                    start = (row, col)
                elif not target:
                    target = (row, col)
                if start and target:
                    visited, path, score, steps_taken = a_star(grid, food_objects, start, target, max_steps)
                    if score is None:
                        #print("No solution found within max steps!")
                        show_no_solution_message(ScreenWidthCell * (cell_size+MARGIN) + MARGIN,
                                                 ScreenHeightCell * (cell_size+MARGIN) + MARGIN, grid_size, n_foods, font)
                        food_objects = generate_food(grid, n_foods)
                        start, target = None, None
                        visited, path, score, steps_taken = set(), [], None, None
                    else:
                        print(f"Path found with score: {score} and steps taken: {steps_taken}")

    pygame.quit()

if __name__ == "__main__":
    main()

