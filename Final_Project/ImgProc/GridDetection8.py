import cv2
import numpy as np

# Open the webcam feed from camera index 3
cap = cv2.VideoCapture(3)

# Create a window for trackbars
cv2.namedWindow("Settings")
cv2.createTrackbar("Clustering Distance", "Settings", 40, 50, lambda x: None)  # Base clustering distance set to 40

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

def identify_outermost_and_corner_intersections(grid_intersections):
    """Identifies outermost intersections and the four main corner vertices."""
    if not grid_intersections:
        return [], [], []

    outermost = []
    inner = []
    corner_points = []

    for i in range(len(grid_intersections)):  # Iterate over rows
        for j in range(len(grid_intersections[i])):  # Iterate over columns
            point = grid_intersections[i][j]
            if i == 0 or i == len(grid_intersections) - 1 or j == 0 or j == len(grid_intersections[i]) - 1:
                outermost.append(point)  # Outermost points
            else:
                inner.append(point)  # Inner points

    # Identify the four corner points (top-left, top-right, bottom-left, bottom-right)
    if len(grid_intersections) > 1 and len(grid_intersections[0]) > 1:
        corner_points = [
            grid_intersections[0][0],  # Top-left
            grid_intersections[0][-1],  # Top-right
            grid_intersections[-1][0],  # Bottom-left
            grid_intersections[-1][-1]  # Bottom-right
        ]

    return outermost, inner, corner_points

if not cap.isOpened():
    print("Error: Could not open webcam.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        cluster_distance = cv2.getTrackbarPos("Clustering Distance", "Settings")
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            binary_feed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)
            edges = cv2.Canny(binary_feed, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 80, minLineLength=50, maxLineGap=10)

            intersections = find_grid_intersections(lines)
            clustered_intersections = cluster_intersections(intersections, cluster_distance=40)
            structured_grid = sort_intersections(clustered_intersections)

            if len(structured_grid) > 0:
                outermost_intersections, inner_intersections, corner_intersections = identify_outermost_and_corner_intersections(structured_grid)

                intersection_image = frame.copy()

                # Draw boundary lines connecting the green dots (outermost points)
                for row in structured_grid:
                    for i in range(len(row) - 1):
                        cv2.line(intersection_image, row[i], row[i + 1], (0, 255, 0), 2)  # Green lines for horizontal connections

                for col in range(len(structured_grid[0])):
                    for i in range(len(structured_grid) - 1):
                        cv2.line(intersection_image, structured_grid[i][col], structured_grid[i + 1][col], (0, 255, 0), 2)  # Green lines for vertical connections

                # Draw detected points
                for x, y in inner_intersections:
                    cv2.circle(intersection_image, (x, y), 3, (255, 0, 0), -1)  # Blue for inner intersections
                for x, y in outermost_intersections:
                    cv2.circle(intersection_image, (x, y), 3, (0, 255, 0), -1)  # Green for outermost intersections
                for x, y in corner_intersections:
                    cv2.circle(intersection_image, (x, y), 6, (0, 165, 255), -1)  # Orange for the 4 main corners

            except Exception as e:
                continue
            cv2.imshow("Detected Intersections & Full Grid Structure", intersection_image)

        cv2.imshow("Webcam Feed - Camera 3", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

