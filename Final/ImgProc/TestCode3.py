import cv2
import numpy as np

# Initialize default parameters for fine-tuning
params = {
    "gaussian_ksize": 5,
    "adaptive_blocksize": 25,
    "adaptive_c": 10,
    "canny_threshold1": 100,
    "canny_threshold2": 200,
    "hough_threshold": 120,
    "min_line_length": 100,
    "max_line_gap": 50,
    "morph_kernel_size": 5  # Morphological kernel size to remove noise
}

def update_values(_):
    """ Trackbar callback function to update values dynamically """
    for key in params.keys():
        params[key] = cv2.getTrackbarPos(key, "Settings")
        
        # Ensure necessary values remain odd and greater than 1
        if key == "gaussian_ksize" or key == "adaptive_blocksize" or key == "morph_kernel_size":
            params[key] = max(3, params[key] | 1)  # Ensure odd value

def detect_grid(frame):
    """ Process the image to detect grid lines with noise reduction """
    
    # Convert to grayscale and apply Histogram Equalization
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(gray)

    # Apply Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(equalized, (params["gaussian_ksize"], params["gaussian_ksize"]), 0)

    # Adaptive Thresholding to extract grid lines
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
        params["adaptive_blocksize"], params["adaptive_c"]
    )

    # Morphological operations to remove small noise and enhance lines
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (params["morph_kernel_size"], params["morph_kernel_size"]))
    morph_cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, morph_kernel)  # Closes small gaps
    morph_cleaned = cv2.morphologyEx(morph_cleaned, cv2.MORPH_OPEN, morph_kernel)  # Removes small noise

    # Canny edge detection for strong edge detection
    edges = cv2.Canny(morph_cleaned, params["canny_threshold1"], params["canny_threshold2"])

    # Hough Transform to detect grid lines
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, params["hough_threshold"],
                            minLineLength=params["min_line_length"], maxLineGap=params["max_line_gap"])

    # Draw detected lines
    line_image = frame.copy()
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Draw grid lines in green

    return morph_cleaned, line_image

def capture_webcam():
    """ Captures webcam feed and applies grid detection with adjustable parameters """
    cap = cv2.VideoCapture(2)

    # Create window with trackbars for parameter tuning
    cv2.namedWindow("Settings")
    for key, value in params.items():
        cv2.createTrackbar(key, "Settings", value, 255, update_values)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        mask, line_image = detect_grid(frame)

        # Display processed images
        cv2.imshow("Thresholded Grid", mask)
        cv2.imshow("Detected Lines", line_image)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Run the function
capture_webcam()

