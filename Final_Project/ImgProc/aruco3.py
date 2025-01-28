import cv2
import numpy as np

def main():
    # 1. Load a predefined 6x6 ArUco dictionary
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

    # 2. Create the detector parameters
    detector_params = cv2.aruco.DetectorParameters()

    # 3. Open webcam (or replace "0" with a video file path)
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
        corners, ids, rejected = cv2.aruco.detectMarkers(
            frame, dictionary, parameters=detector_params
        )

        if ids is not None and len(ids) > 0:
            # Draw only the bounding boxes (without IDs)
            # Pass 'None' in place of 'ids' to avoid drawing the ID text
            cv2.aruco.drawDetectedMarkers(frame, corners, None, (255, 255, 0))

            for i, corner_set in enumerate(corners):
                # Convert corner points to integer (x,y)
                c = corner_set[0]
                corner_coords = [(int(pt[0]), int(pt[1])) for pt in c]

                # Marker ID (since 'ids' is shaped (N,1), get the actual int)
                marker_id = int(ids[i])

                # Compute angle as the vector from corner 0 to corner 1
                dx = corner_coords[1][0] - corner_coords[0][0]
                dy = corner_coords[1][1] - corner_coords[0][1]
                angle_deg = np.degrees(np.arctan2(dy, dx))

                # 5. Place text on different corners
                # Corner 0 = top-left, Corner 1 = top-right, Corner 2 = bottom-right, Corner 3 = bottom-left
                
                # -- (A) Marker ID near top-left corner
                cv2.putText(
                    frame, 
                    f"ID: {marker_id}",
                    (corner_coords[0][0], corner_coords[0][1] - 10),  
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (0, 255, 255), 2
                )

                # -- (B) Angle near top-right corner
                cv2.putText(
                    frame, 
                    f"Angle: {angle_deg:.1f} deg",
                    (corner_coords[1][0], corner_coords[1][1] - 10),  
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (0, 255, 255), 2
                )

                # -- (C) "Orientation" (same value) near bottom-right corner
                cv2.putText(
                    frame,
                    f"Orientation: {angle_deg:.1f} deg",
                    (corner_coords[2][0], corner_coords[2][1] + 20),  # shift below corner 2
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255), 2
                )

        # Show the result
        cv2.imshow("6x6 ArUco Detection", frame)
        
        # Exit on 'ESC'
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

