import cv2
import numpy as np

# Initialize default values for all parameters
gaussian_ksize = 5
adaptive_blocksize = 25
adaptive_c = 10
canny_threshold1 = 50
canny_threshold2 = 150
hough_threshold = 100
min_line_length = 150
max_line_gap = 50
red_lower_hue = 0
red_upper_hue = 10
black_lower_v = 50
black_upper_v = 100

def update_values(_):
    """Trackbar callback function (updates values in real-time)."""
    global gaussian_ksize, adaptive_blocksize, adaptive_c, canny_threshold1, canny_threshold2
    global hough_threshold, min_line_length, max_line_gap
    global red_lower_hue, red_upper_hue, black_lower_v, black_upper_v

    # Ensure odd values for Gaussian Blur kernel
    gaussian_ksize = cv2.getTrackbarPos("Gaussian Kernel", "Settings")
    if gaussian_ksize % 2 == 0:
        gaussian_ksize += 1  # Gaussian Blur kernel must be odd

    # Ensure odd blockSize and greater than 1
    adaptive_blocksize = cv2.getTrackbarPos("Adaptive BlockSize", "Settings") | 1  # Ensure odd
    if adaptive_blocksize < 3: 
        adaptive_blocksize = 3  # Ensure minimum block size is 3

    adaptive_c = cv2.getTrackbarPos("Adaptive C", "Settings")
    canny_threshold1 = cv2.getTrackbarPos("Canny Threshold 1", "Settings")
    canny_threshold2 = cv2.getTrackbarPos("Canny Threshold 2", "Settings")
    hough_threshold = cv2.getTrackbarPos("Hough Threshold", "Settings")
    min_line_length = cv2.getTrackbarPos("Min Line Length", "Settings")
    max_line_gap = cv2.getTrackbarPos("Max Line Gap", "Settings")
    red_lower_hue = cv2.getTrackbarPos("Red Lower Hue", "Settings")
    red_upper_hue = cv2.getTrackbarPos("Red Upper Hue", "Settings")
    black_lower_v = cv2.getTrackbarPos("Black Lower V", "Settings")
    black_upper_v = cv2.getTrackbarPos("Black Upper V", "Settings")

def detect_lines(frame):
    """ Detect black and red lines dynamically with histogram equalization and adjustable parameters """
    # Convert to grayscale and apply Histogram Equalization
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(gray)

    # Apply Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(equalized, (gaussian_ksize, gaussian_ksize), 0)

    # Convert to HSV for color segmentation
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define dynamic color ranges for red (using trackbars)
    lower_red1 = np.array([red_lower_hue, 120, 70])
    upper_red1 = np.array([red_upper_hue, 255, 255])
    lower_red2 = np.array([180 - red_upper_hue, 120, 70])
    upper_red2 = np.array([180 - red_lower_hue, 255, 255])

    # Define dynamic black detection range with adjustable V values
    lower_black = np.array([0, 0, black_lower_v])
    upper_black = np.array([180, 255, black_upper_v])

    # Create masks for red and black colors
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    mask_black = cv2.inRange(hsv, lower_black, upper_black)

    # Adaptive Thresholding on Black Mask to Improve Detection
    adaptive_black = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV, adaptive_blocksize, adaptive_c)

    # Combine black detection with adaptive thresholding for better results
    mask_black = cv2.bitwise_or(mask_black, adaptive_black)

    # Combine masks (Detect either red or black)
    combined_mask = cv2.bitwise_or(mask_red, mask_black)

    # Apply edge detection on the mask
    edges = cv2.Canny(combined_mask, canny_threshold1, canny_threshold2)

    # Detect lines using Hough Transform with refined parameters
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, hough_threshold, minLineLength=min_line_length, maxLineGap=max_line_gap)

    # Draw detected lines on the frame
    line_image = frame.copy()
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green lines

    return combined_mask, line_image

def capture_webcam():
    cap = cv2.VideoCapture(2)  # Open webcam

    # Create a window with trackbars
    cv2.namedWindow("Settings")
    cv2.createTrackbar("Gaussian Kernel", "Settings", gaussian_ksize, 21, update_values)
    cv2.createTrackbar("Adaptive BlockSize", "Settings", adaptive_blocksize, 51, update_values)
    cv2.createTrackbar("Adaptive C", "Settings", adaptive_c, 50, update_values)
    cv2.createTrackbar("Canny Threshold 1", "Settings", canny_threshold1, 255, update_values)
    cv2.createTrackbar("Canny Threshold 2", "Settings", canny_threshold2, 255, update_values)
    cv2.createTrackbar("Hough Threshold", "Settings", hough_threshold, 200, update_values)
    cv2.createTrackbar("Min Line Length", "Settings", min_line_length, 300, update_values)
    cv2.createTrackbar("Max Line Gap", "Settings", max_line_gap, 100, update_values)
    cv2.createTrackbar("Red Lower Hue", "Settings", red_lower_hue, 180, update_values)
    cv2.createTrackbar("Red Upper Hue", "Settings", red_upper_hue, 180, update_values)
    cv2.createTrackbar("Black Lower V", "Settings", black_lower_v, 255, update_values)
    cv2.createTrackbar("Black Upper V", "Settings", black_upper_v, 255, update_values)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        mask, line_image = detect_lines(frame)  # Detect black and red lines

        # Show original, thresholded mask, and detected lines
        cv2.imshow("Original Video", frame)
        cv2.imshow("Thresholded Video", mask)
        cv2.imshow("Detected Lines", line_image)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Run the function
capture_webcam()

