import cv2
import numpy as np
from collections import deque

# Get user input for grid size (rows and columns)
n = int(input("Enter number of rows (n): "))
m = int(input("Enter number of columns (m): "))

# Open the webcam feed from camera index 3
cap = cv2.VideoCapture(2)

# Create a window for trackbars and buttons
cv2.namedWindow("Settings")
cv2.createTrackbar("Clustering Distance", "Settings", 90, 200, lambda x: None)  # Base clustering distance set to 90, adjustable up to 200
cv2.createTrackbar("Update Threshold", "Settings", 5, 50, lambda x: None)  # Threshold for updating positions
cv2.createTrackbar("Show Grid (0=Off, 1=On)", "Settings", 0, 1, lambda x: None)  # Toggle grid visibility

# Grid stability settings
MAX_HISTORY = 5  # Number of frames to average for smoothing
intersection_history = deque(maxlen=MAX_HISTORY)  # Stores last few intersection detections

# Persistent Grid Memory Variables
last_valid_grid = None
last_valid_centers = None
missing_frames = 0  # Count frames where grid detection fails
MISSING_THRESHOLD = 30  # Number of missing frames before triggering re-detection

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
        return []

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

def cluster_intersections(intersections, cluster_distance):
    """Groups nearby intersection points into single representative points using clustering."""
    if not intersections:
        return []

    intersections = np.array(intersections)
    clustered = []

    while len(intersections) > 0:
        ref_point = intersections[0]
        distances = np.linalg.norm(intersections - ref_point, axis=1)
        close_points = intersections[distances < cluster_distance]

        cluster_center = np.mean(close_points, axis=0).astype(int)
        clustered.append(tuple(cluster_center))

        intersections = intersections[distances >= cluster_distance]

    return clustered

def sort_intersections(intersections):
    """Sorts intersections into (m+1) x (n+1) structured grid."""
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

def find_cell_centers(grid_intersections):
    """Finds and numbers cell centers based on grid intersections."""
    cell_centers = []
    cell_numbers = []

    count = 1  # Start numbering from 1
    for i in range(len(grid_intersections) - 1):
        for j in range(len(grid_intersections[i]) - 1):
            x1, y1 = grid_intersections[i][j]
            x2, y2 = grid_intersections[i + 1][j + 1]
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            cell_centers.append((center_x, center_y))
            cell_numbers.append(count)
            count += 1

    return cell_centers, cell_numbers

if not cap.isOpened():
    print("Error: Could not open webcam.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        cluster_distance = cv2.getTrackbarPos("Clustering Distance", "Settings")
        update_threshold = cv2.getTrackbarPos("Update Threshold", "Settings")
        show_grid = cv2.getTrackbarPos("Show Grid (0=Off, 1=On)", "Settings")  # Get grid visibility toggle

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            binary_feed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)
            edges = cv2.Canny(binary_feed, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 80, minLineLength=50, maxLineGap=10)

            intersections = find_grid_intersections(lines)
            clustered_intersections = cluster_intersections(intersections, cluster_distance)
            structured_grid = sort_intersections(clustered_intersections)

            if len(structured_grid) > 0:
                last_valid_grid = structured_grid
                missing_frames = 0  # Reset missing frame counter
            else:
                missing_frames += 1

            if missing_frames < MISSING_THRESHOLD and last_valid_grid is not None:
                structured_grid = last_valid_grid

            if structured_grid is not None:
                intersection_image = frame.copy()

                cell_centers, cell_numbers = find_cell_centers(structured_grid)

                # Draw grid only if toggle is ON
                if show_grid == 1:
                    # Draw grid lines
                    for row in structured_grid:
                        for i in range(len(row) - 1):
                            cv2.line(intersection_image, row[i], row[i + 1], (255, 105, 180), 2)  # Pink horizontal connections

                    for col in range(len(structured_grid[0])):
                        for i in range(len(structured_grid) - 1):
                            cv2.line(intersection_image, structured_grid[i][col], structured_grid[i + 1][col], (255, 105, 180), 2)  # Pink vertical connections

                    # Draw detected points and numbers
                for idx, (x, y) in enumerate(cell_centers):
                    cv2.circle(intersection_image, (x, y), 4, (0, 0, 255), -1)  # Red for cell centers
                    cv2.putText(intersection_image, str(cell_numbers[idx]), (x - 10, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                cv2.imshow("Detected Intersections & Full Grid Structure", intersection_image)

        except Exception as e:
            print("Error:", e)

        cv2.imshow("Webcam Feed - Camera 3", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

