import cv2
import numpy as np

def main():
    # --- 1. Use getPredefinedDictionary for older versions of opencv-contrib ---
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

    # --- 2. Create the detector parameters ---
    detector_params = cv2.aruco.DetectorParameters()

    # --- 3. Open your webcam or a video file ---
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open video source.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("No frame captured from video.")
            break
        
        # --- 4. Detect markers in the frame ---
        corners, ids, rejected = cv2.aruco.detectMarkers(
            frame, 
            dictionary, 
            parameters=detector_params
        )

        if ids is not None and len(ids) > 0:
            # Draw detected markers in cyan
            cv2.aruco.drawDetectedMarkers(frame, corners, ids, (255, 255, 0))

            # Compute and display orientation for each detected marker
            for i, corner_set in enumerate(corners):
                c = corner_set[0]
                
                # Vector from corner[0] to corner[1]
                dx = c[1][0] - c[0][0]
                dy = c[1][1] - c[0][1]
                
                # Angle in degrees
                angle = np.degrees(np.arctan2(dy, dx))
                
                # Marker center
                center_x = int(np.mean(c[:, 0]))
                center_y = int(np.mean(c[:, 1]))
                
                # Display angle
                cv2.putText(
                    frame, 
                    f"Angle: {angle:.1f} deg",
                    (center_x, center_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (0, 255, 255), 
                    2
                )

        # Show the frame
        cv2.imshow("6x6 ArUco Detection", frame)
        
        # Exit on 'ESC'
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

