import cv2
import numpy as np
from collections import deque

# Get user input for grid size (rows and columns)
n = int(input("Enter number of rows (n): "))
m = int(input("Enter number of columns (m): "))

# Open the webcam feed from camera index 2
cap = cv2.VideoCapture(2)

# Create a window for trackbars and buttons
cv2.namedWindow("Settings")
cv2.createTrackbar("Clustering Distance", "Settings", 90, 200, lambda x: None)  # Base clustering distance
cv2.createTrackbar("Update Threshold", "Settings", 5, 50, lambda x: None)      # Threshold for updating positions
cv2.createTrackbar("Show Grid (0=Off, 1=On)", "Settings", 0, 1, lambda x: None)

# Grid stability settings
MAX_HISTORY = 5
intersection_history = deque(maxlen=MAX_HISTORY)  # Not used in the current version, but could be used for smoothing
last_valid_grid = None
last_valid_centers = None
missing_frames = 0
MISSING_THRESHOLD = 30

def compute_intersection(line1, line2):
    """Computes the intersection point between two lines."""
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None  # Parallel lines
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return int(px), int(py)

def find_grid_intersections(lines):
    """Finds intersection points from detected lines."""
    intersections = []
    if lines is None:
        return []

    vertical_lines = []
    horizontal_lines = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(x1 - x2) < abs(y1 - y2):
            vertical_lines.append((x1, y1, x2, y2))
        else:
            horizontal_lines.append((x1, y1, x2, y2))

    for v_line in vertical_lines:
        for h_line in horizontal_lines:
            intersec = compute_intersection(v_line, h_line)
            if intersec:
                intersections.append(intersec)

    return intersections

def cluster_intersections(intersections, cluster_distance):
    """Groups nearby intersection points into single representative points using clustering."""
    if not intersections:
        return []

    points = np.array(intersections)
    clustered = []

    while len(points) > 0:
        ref_point = points[0]
        distances = np.linalg.norm(points - ref_point, axis=1)
        close_points = points[distances < cluster_distance]

        cluster_center = np.mean(close_points, axis=0).astype(int)
        clustered.append(tuple(cluster_center))

        points = points[distances >= cluster_distance]

    return clustered

def sort_intersections(intersections):
    """Sorts intersections into row-major order based on y, then x."""
    if not intersections:
        return []

    # Sort by y, then by x
    intersections = sorted(intersections, key=lambda pt: (pt[1], pt[0]))

    grid_rows = []
    row_tolerance = 20  # max y-distance to consider points as part of the same row

    current_row = [intersections[0]]
    for i in range(1, len(intersections)):
        if abs(intersections[i][1] - current_row[-1][1]) < row_tolerance:
            current_row.append(intersections[i])
        else:
            grid_rows.append(sorted(current_row, key=lambda pt: pt[0]))  # sort each row by x
            current_row = [intersections[i]]
    grid_rows.append(sorted(current_row, key=lambda pt: pt[0]))

    return grid_rows

def find_cell_centers(grid_intersections):
    """Finds and numbers cell centers based on grid intersections."""
    cell_centers = []
    cell_numbers = []

    count = 1
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
        show_grid = cv2.getTrackbarPos("Show Grid (0=Off, 1=On)", "Settings")

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            binary_feed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10
            )
            edges = cv2.Canny(binary_feed, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 80, minLineLength=50, maxLineGap=10)

            intersections = find_grid_intersections(lines)
            clustered_intersections = cluster_intersections(intersections, cluster_distance)
            structured_grid = sort_intersections(clustered_intersections)

            if len(structured_grid) > 0:
                last_valid_grid = structured_grid
                missing_frames = 0
            else:
                missing_frames += 1

            # Use last valid grid if current detection fails
            if missing_frames < MISSING_THRESHOLD and last_valid_grid is not None:
                structured_grid = last_valid_grid

            if structured_grid is not None:
                intersection_image = frame.copy()
                cell_centers, cell_numbers = find_cell_centers(structured_grid)

                # Draw grid lines if toggle is ON
                if show_grid == 1:
                    # Draw horizontal connections
                    for row in structured_grid:
                        for i in range(len(row) - 1):
                            cv2.line(
                                intersection_image,
                                row[i],
                                row[i + 1],
                                (255, 105, 180),  # pink
                                2
                            )
                    # Draw vertical connections
                    for col in range(len(structured_grid[0])):
                        for i in range(len(structured_grid) - 1):
                            cv2.line(
                                intersection_image,
                                structured_grid[i][col],
                                structured_grid[i + 1][col],
                                (255, 105, 180),  # pink
                                2
                            )

                # Highlight each intersection point differently
                num_rows = len(structured_grid)
                for i, row_points in enumerate(structured_grid):
                    num_cols = len(row_points)
                    for j, (x, y) in enumerate(row_points):
                        # Determine if it's a corner, outer edge, or inner intersection
                        if (
                            (i == 0 and j == 0) or  # top-left corner
                            (i == 0 and j == num_cols - 1) or  # top-right corner
                            (i == num_rows - 1 and j == 0) or  # bottom-left corner
                            (i == num_rows - 1 and j == num_cols - 1)  # bottom-right corner
                        ):
                            color = (0, 165, 255)  # Orange (BGR)
                            radius = 8
                        elif (
                            i == 0 or
                            i == num_rows - 1 or
                            j == 0 or
                            j == num_cols - 1
                        ):
                            color = (0, 255, 0)  # Green
                            radius = 6
                        else:
                            color = (255, 0, 0)  # Blue
                            radius = 4

                        cv2.circle(intersection_image, (x, y), radius, color, -1)

                # Draw red cell centers with numbers
                for idx, (cx, cy) in enumerate(cell_centers):
                    cv2.circle(intersection_image, (cx, cy), 4, (0, 0, 255), -1)  # red
                    cv2.putText(
                        intersection_image,
                        str(cell_numbers[idx]),
                        (cx - 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        2
                    )

                cv2.imshow("Detected Intersections & Full Grid Structure", intersection_image)

        except Exception as e:
            print("Error:", e)

        cv2.imshow("Webcam Feed - Camera 3", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

