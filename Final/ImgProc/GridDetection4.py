import cv2
import numpy as np

### USER INPUT PARAMETERS ###
GRID_ROWS = 3  # Number of rows in the grid (m)
GRID_COLS = 4  # Number of columns in the grid (n)
CAMERA_INDEX = 3  # Change this if using a different camera

# Open the webcam feed
cap = cv2.VideoCapture(CAMERA_INDEX)

def compute_intersection(line1, line2):
    """Computes the intersection point between two lines."""
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if denom == 0:
        return None  # Parallel lines, no intersection

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom

    return int(px), int(py)

def find_grid_intersections(lines):
    """Finds intersection points from detected lines."""
    intersections = []
    if lines is None:
        return intersections

    vertical_lines, horizontal_lines = [], []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(x1 - x2) < abs(y1 - y2):  # Vertical line
            vertical_lines.append((x1, y1, x2, y2))
        else:  # Horizontal line
            horizontal_lines.append((x1, y1, x2, y2))

    for v_line in vertical_lines:
        for h_line in horizontal_lines:
            intersection = compute_intersection(v_line, h_line)
            if intersection:
                intersections.append(intersection)

    return intersections

def sort_intersections(intersections):
    """
    Sorts intersections into (m+1) x (n+1) structured grid.
    Ensures each row and column is ordered correctly.
    """
    if not intersections:
        return []

    intersections = sorted(intersections, key=lambda pt: (pt[1], pt[0]))  # Sort by y, then x

    # Sort into rows
    grid_rows = []
    row_tolerance = 20  # Max distance in y-axis to consider as same row

    current_row = [intersections[0]]
    for i in range(1, len(intersections)):
        if abs(intersections[i][1] - current_row[-1][1]) < row_tolerance:
            current_row.append(intersections[i])
        else:
            grid_rows.append(sorted(current_row, key=lambda pt: pt[0]))  # Sort by x within row
            current_row = [intersections[i]]

    grid_rows.append(sorted(current_row, key=lambda pt: pt[0]))

    return grid_rows

def draw_grid(frame, grid_intersections):
    """Draws the m × n grid and labels the cells based on structured intersections."""
    for i in range(GRID_ROWS):  # Iterate over rows
        for j in range(GRID_COLS):  # Iterate over columns
            if i + 1 < len(grid_intersections) and j + 1 < len(grid_intersections[i]):
                top_left = grid_intersections[i][j]
                top_right = grid_intersections[i][j+1]
                bottom_left = grid_intersections[i+1][j]
                bottom_right = grid_intersections[i+1][j+1]

                # Draw horizontal and vertical grid lines
                cv2.line(frame, top_left, top_right, (0, 255, 0), 2)
                cv2.line(frame, bottom_left, bottom_right, (0, 255, 0), 2)
                cv2.line(frame, top_left, bottom_left, (0, 255, 0), 2)
                cv2.line(frame, top_right, bottom_right, (0, 255, 0), 2)

                # Label grid cells
                cell_center = ((top_left[0] + bottom_right[0]) // 2, (top_left[1] + bottom_right[1]) // 2)
                cell_number = i * GRID_COLS + j + 1  # Number cells from top-left
                cv2.putText(frame, str(cell_number), cell_center, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

if not cap.isOpened():
    print("Error: Could not open webcam.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        binary_feed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)
        edges = cv2.Canny(binary_feed, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 80, minLineLength=50, maxLineGap=10)

        intersections = find_grid_intersections(lines)
        structured_grid = sort_intersections(intersections)

        final_feed = frame.copy()

        if len(structured_grid) == GRID_ROWS + 1 and all(len(row) == GRID_COLS + 1 for row in structured_grid):
            draw_grid(final_feed, structured_grid)
        else:
            cv2.putText(final_feed, "Grid not detected properly!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Show only the original and final processed feed
        cv2.imshow("Webcam Feed - Camera 3", frame)
        cv2.imshow("Final Grid Detection & Numbering", final_feed)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

