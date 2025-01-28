import cv2
import numpy as np

def main():
    # 1. Load a predefined 6x6 dictionary
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
        corners, ids, _ = cv2.aruco.detectMarkers(frame, dictionary, parameters=detector_params)

        if ids is not None and len(ids) > 0:
            # Draw only bounding boxes in cyan (pass None for ids to skip default ID text)
            cv2.aruco.drawDetectedMarkers(frame, corners, None, (255, 255, 0))

            for i, corner_set in enumerate(corners):
                # Convert corner points to integer (x,y)
                c = corner_set[0]
                corner_coords = [(int(pt[0]), int(pt[1])) for pt in c]

                # Marker ID
                marker_id = int(ids[i])

                # Compute angle based on the vector from corner 0 to corner 1
                dx = corner_coords[1][0] - corner_coords[0][0]
                dy = corner_coords[1][1] - corner_coords[0][1]
                angle_deg = np.degrees(np.arctan2(dy, dx))

                # (A) Put ID near corner 0 (top-left)
                cv2.putText(
                    frame,
                    f"ID: {marker_id}",
                    (corner_coords[0][0], corner_coords[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

                # (B) Put Angle near corner 1 (top-right)
                cv2.putText(
                    frame,
                    f"Angle: {angle_deg:.1f} deg",
                    (corner_coords[1][0], corner_coords[1][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

                # (C) Draw a cyan dot at the center of the marker
                center_x = int(np.mean([pt[0] for pt in corner_coords]))
                center_y = int(np.mean([pt[1] for pt in corner_coords]))
                cv2.circle(frame, (center_x, center_y), 5, (255, 255, 0), -1)

                # (D) Draw a line from center to the "front" (midpoint of top edge from corner 0→1)
                front_mid_x = (corner_coords[0][0] + corner_coords[1][0]) // 2
                front_mid_y = (corner_coords[0][1] + corner_coords[1][1]) // 2
                cv2.line(frame, (center_x, center_y), (front_mid_x, front_mid_y), (255, 255, 0), 2)

        # Show the result
        cv2.imshow("6x6 ArUco Detection", frame)
        
        # Exit on 'ESC'
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

