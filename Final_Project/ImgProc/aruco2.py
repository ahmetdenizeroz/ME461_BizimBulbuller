import cv2
import numpy as np

def main():
    # 1. Load a predefined 6x6 dictionary
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

    # 2. Create the detector parameters
    # Note: In older OpenCV, this might be cv2.aruco.DetectorParameters_create().
    detector_params = cv2.aruco.DetectorParameters()

    # 3. Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open video source.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("No frame captured from video.")
            break
        
        # 4. Detect markers
        corners, ids, rejected = cv2.aruco.detectMarkers(frame, dictionary, parameters=detector_params)

        if ids is not None and len(ids) > 0:
            # Draw detected markers in cyan
            cv2.aruco.drawDetectedMarkers(frame, corners, ids, (255, 255, 0))

            # For each marker, compute & display orientation and ID near specific corners
            for i, corner_set in enumerate(corners):
                # corner_set has shape (1, 4, 2), so corner_set[0] is the 4 corner points.
                c = corner_set[0]
                
                # Convert corners to integer (x, y) for easy use with cv2.putText
                corner_coords = [(int(pt[0]), int(pt[1])) for pt in c]

                # corner[0] = top-left, corner[1] = top-right, corner[2] = bottom-right, corner[3] = bottom-left (by default)
                # The IDs array is also shaped (N, 1), so we take ids[i][0] or just int(ids[i])
                marker_id = int(ids[i])

                # Compute angle based on vector from corner[0] → corner[1]
                dx = corner_coords[1][0] - corner_coords[0][0]
                dy = corner_coords[1][1] - corner_coords[0][1]
                angle = np.degrees(np.arctan2(dy, dx))

                # Put the ID near top-left corner (corner 0)
                cv2.putText(
                    frame,
                    f"ID: {marker_id}",
                    (corner_coords[0][0], corner_coords[0][1] - 10),  # slight shift above the corner
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),  # Yellow color
                    2
                )

                # Put the angle near top-right corner (corner 1)
                cv2.putText(
                    frame,
                    f"Angle: {angle:.1f} deg",
                    (corner_coords[1][0], corner_coords[1][1] - 10),  # slight shift above the corner
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),  # Yellow color
                    2
                )

        # 5. Show the frame
        cv2.imshow("6x6 ArUco Detection", frame)
        
        # Exit on 'ESC'
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    # 6. Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

