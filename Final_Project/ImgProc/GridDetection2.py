import cv2
import numpy as np

# Open the webcam feed from camera index 3
cap = cv2.VideoCapture(3)

# Create a window for trackbars
cv2.namedWindow("Settings")

# Initialize sliders
cv2.createTrackbar("Histogram Flatness", "Settings", 0, 100, lambda x: None)
cv2.createTrackbar("Histogram Shift", "Settings", 0, 100, lambda x: None)
cv2.createTrackbar("Adaptive Threshold", "Settings", 5, 50, lambda x: None)
cv2.createTrackbar("Canny Low", "Settings", 50, 255, lambda x: None)
cv2.createTrackbar("Canny High", "Settings", 150, 255, lambda x: None)
cv2.createTrackbar("Hough Threshold", "Settings", 80, 200, lambda x: None)
cv2.createTrackbar("Line Min Length", "Settings", 50, 200, lambda x: None)
cv2.createTrackbar("Line Max Gap", "Settings", 10, 50, lambda x: None)
cv2.createTrackbar("Clustering Distance", "Settings", 15, 50, lambda x: None)  # Distance to group nearby intersections

# Store reference grid intersections for stability
reference_intersections = None

def compute_intersection(line1, line2):
    """ Computes the intersection point between two lines. """
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if denom == 0:
        return None  # Parallel lines, no intersection

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom

    return int(px), int(py)

def find_grid_intersections(lines):
    """ Finds intersection points from detected lines. """
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
    """
    Groups nearby intersection points into single representative points using clustering.
    """
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

def stabilize_intersections(intersections, ref_intersections):
    """
    Matches detected intersections with previous stable references to prevent flickering.
    """
    if ref_intersections is None:
        return intersections  # First frame, no previous data

    stabilized = []
    for x, y in intersections:
        closest_ref = min(ref_intersections, key=lambda pt: np.linalg.norm(np.array(pt) - np.array((x, y))))
        stabilized.append(closest_ref)

    return stabilized

if not cap.isOpened():
    print("Error: Could not open webcam.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        flatness = cv2.getTrackbarPos("Histogram Flatness", "Settings")
        shift = cv2.getTrackbarPos("Histogram Shift", "Settings") - 50
        adaptive_block_size = cv2.getTrackbarPos("Adaptive Threshold", "Settings") | 1
        canny_low = cv2.getTrackbarPos("Canny Low", "Settings")
        canny_high = cv2.getTrackbarPos("Canny High", "Settings")
        hough_threshold = cv2.getTrackbarPos("Hough Threshold", "Settings")
        min_line_length = cv2.getTrackbarPos("Line Min Length", "Settings")
        max_line_gap = cv2.getTrackbarPos("Line Max Gap", "Settings")
        cluster_distance = cv2.getTrackbarPos("Clustering Distance", "Settings")

        if flatness > 0:
            alpha = flatness / 100.0
            hist_eq = cv2.equalizeHist(gray)
            adjusted_gray = cv2.addWeighted(gray, 1 - alpha, hist_eq, alpha, 0)
        else:
            adjusted_gray = gray

        shifted_gray = np.clip(adjusted_gray + shift, 0, 255).astype(np.uint8)

        binary_feed = cv2.adaptiveThreshold(
            shifted_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, adaptive_block_size, 10
        )

        edges = cv2.Canny(binary_feed, canny_low, canny_high)

        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, hough_threshold, minLineLength=min_line_length, maxLineGap=max_line_gap)

        intersections = find_grid_intersections(lines)
        clustered_intersections = cluster_intersections(intersections, cluster_distance)
        stable_intersections = stabilize_intersections(clustered_intersections, reference_intersections)

        reference_intersections = stable_intersections

        intersection_image = frame.copy()
        for x, y in stable_intersections:
            cv2.circle(intersection_image, (x, y), 3, (255, 0, 0), -1)  # Blue markers for corners

        cv2.imshow("Webcam Feed - Camera 3", frame)
        cv2.imshow("Modified Grayscale Feed", shifted_gray)
        cv2.imshow("Binary Feed - Adaptive Gaussian Thresholding", binary_feed)
        cv2.imshow("Canny Edge Detection", edges)
        cv2.imshow("Detected Intersections (Stable, Blue)", intersection_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

