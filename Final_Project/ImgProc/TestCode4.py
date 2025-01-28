import cv2
import numpy as np

# Open the webcam feed from camera index 2
cap = cv2.VideoCapture(3)

# Create a window for trackbars
cv2.namedWindow("Settings")

# Initialize sliders
cv2.createTrackbar("Histogram Flatness", "Settings", 0, 100, lambda x: None)  # Equalization control
cv2.createTrackbar("Histogram Shift", "Settings", 0, 100, lambda x: None)  # Shift control
cv2.createTrackbar("Adaptive Threshold", "Settings", 5, 50, lambda x: None)  # Adaptive threshold block size
cv2.createTrackbar("Canny Low", "Settings", 50, 255, lambda x: None)  # Lower bound for Canny Edge Detection
cv2.createTrackbar("Canny High", "Settings", 150, 255, lambda x: None)  # Upper bound for Canny Edge Detection
cv2.createTrackbar("Hough Threshold", "Settings", 80, 200, lambda x: None)  # Hough Transform threshold
cv2.createTrackbar("Line Min Length", "Settings", 50, 200, lambda x: None)  # Minimum line length for detection
cv2.createTrackbar("Line Max Gap", "Settings", 10, 50, lambda x: None)  # Maximum gap between lines

def compute_intersection(line1, line2):
    """
    Computes the intersection point between two lines.
    Each line is given as (x1, y1, x2, y2).
    """
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2

    # Compute the determinant
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    if denom == 0:
        return None  # Lines are parallel, no intersection

    # Solve for intersection point
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom

    return int(px), int(py)

def find_grid_intersections(lines):
    """
    Finds intersection points from detected lines.
    Filters intersections to match expected grid patterns.
    """
    intersections = []
    
    if lines is None:
        return intersections

    # Separate vertical and horizontal lines
    vertical_lines = []
    horizontal_lines = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(x1 - x2) < abs(y1 - y2):  # Vertical line
            vertical_lines.append((x1, y1, x2, y2))
        else:  # Horizontal line
            horizontal_lines.append((x1, y1, x2, y2))

    # Compute intersections
    for v_line in vertical_lines:
        for h_line in horizontal_lines:
            intersection = compute_intersection(v_line, h_line)
            if intersection:
                intersections.append(intersection)

    return intersections

if not cap.isOpened():
    print("Error: Could not open webcam.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Get slider values
        flatness = cv2.getTrackbarPos("Histogram Flatness", "Settings")
        shift = cv2.getTrackbarPos("Histogram Shift", "Settings") - 50  # Range: -50 to +50
        adaptive_block_size = cv2.getTrackbarPos("Adaptive Threshold", "Settings") | 1  # Ensure it's an odd number
        canny_low = cv2.getTrackbarPos("Canny Low", "Settings")
        canny_high = cv2.getTrackbarPos("Canny High", "Settings")
        hough_threshold = cv2.getTrackbarPos("Hough Threshold", "Settings")
        min_line_length = cv2.getTrackbarPos("Line Min Length", "Settings")
        max_line_gap = cv2.getTrackbarPos("Line Max Gap", "Settings")

        # Apply histogram equalization with adjustable flatness
        if flatness > 0:
            alpha = flatness / 100.0  # Convert to range 0.0 - 1.0
            hist_eq = cv2.equalizeHist(gray)  # Full equalization
            adjusted_gray = cv2.addWeighted(gray, 1 - alpha, hist_eq, alpha, 0)  # Blend original & equalized
        else:
            adjusted_gray = gray  # No equalization when slider is at 0

        # Apply brightness shift (shifting the histogram)
        shifted_gray = np.clip(adjusted_gray + shift, 0, 255).astype(np.uint8)

        # Apply Adaptive Gaussian Thresholding
        binary_feed = cv2.adaptiveThreshold(
            shifted_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, adaptive_block_size, 10
        )

        # Apply Canny Edge Detection
        edges = cv2.Canny(binary_feed, canny_low, canny_high)

        # Detect lines using Hough Line Transform
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, hough_threshold, minLineLength=min_line_length, maxLineGap=max_line_gap)

        # Find intersections
        intersections = find_grid_intersections(lines)

        # Draw detected intersections on a copy of the frame
        intersection_image = frame.copy()
        for x, y in intersections:
            cv2.circle(intersection_image, (x, y), 5, (0, 0, 255), -1)  # Red for detected intersections

        # Show the original feed
        cv2.imshow("Webcam Feed - Camera 2", frame)

        # Show the grayscale feed with applied histogram modifications
        cv2.imshow("Modified Grayscale Feed", shifted_gray)

        # Show the adaptive thresholded binary feed
        cv2.imshow("Binary Feed - Adaptive Gaussian Thresholding", binary_feed)

        # Show the Canny edge detected feed
        cv2.imshow("Canny Edge Detection", edges)

        # Show the detected intersections
        cv2.imshow("Detected Intersections", intersection_image)

        # Press 'q' to exit the webcam window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release the camera and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()

