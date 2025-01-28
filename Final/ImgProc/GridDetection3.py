import cv2
import numpy as np

### USER INPUT PARAMETERS ###
GRID_ROWS = 3  # Number of rows in the grid (m)
GRID_COLS = 4  # Number of columns in the grid (n)
SQUARE_SIZE = 150  # Side length of one square in mm (x)
CAMERA_INDEX = 3  # Change this if using a different camera

# Open the webcam feed from the specified camera index
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

def match_intersections_to_grid(intersections, frame_shape):
    """
    Matches detected intersections to a structured m × n grid using the known grid size and spacing.
    Ensures evenly distributed points and reconstructs missing ones.
    """
    height, width = frame_shape[:2]
    
    # Expected grid spacing in pixels (estimated from the image size)
    x_spacing = width // (GRID_COLS + 1)
    y_spacing = height // (GRID_ROWS + 1)

    # Generate expected grid positions based on known grid size
    expected_grid = []
    for i in range(GRID_ROWS + 1):
        row = []
        for j in range(GRID_COLS + 1):
            expected_x = x_spacing * (j + 1)
            expected_y = y_spacing * (i + 1)
            row.append((expected_x, expected_y))
        expected_grid.append(row)

    # Snap detected intersections to the closest expected grid positions
    matched_grid = [[None] * (GRID_COLS + 1) for _ in range(GRID_ROWS + 1)]

    for x, y in intersections:
        closest_dist = float('inf')
        closest_point = None
        closest_i, closest_j = -1, -1

        for i in range(GRID_ROWS + 1):
            for j in range(GRID_COLS + 1):
                expected_x, expected_y = expected_grid[i][j]
                distance = np.linalg.norm([x - expected_x, y - expected_y])
                if distance < closest_dist:
                    closest_dist = distance
                    closest_point = (expected_x, expected_y)
                    closest_i, closest_j = i, j

        if closest_point and closest_i != -1 and closest_j != -1:
            matched_grid[closest_i][closest_j] = closest_point

    return matched_grid

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
        structured_grid = match_intersections_to_grid(intersections, frame.shape)

        # Draw detected grid intersections on the frame
        intersection_image = frame.copy()
        for row in structured_grid:
            for point in row:
                if point:
                    cv2.circle(intersection_image, point, 5, (255, 0, 0), -1)  # Blue markers for corners

        cv2.imshow("Webcam Feed - Camera 3", frame)
        cv2.imshow("Binary Feed - Adaptive Gaussian Thresholding", binary_feed)
        cv2.imshow("Canny Edge Detection", edges)
        cv2.imshow("Structured Grid Intersections", intersection_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

