from GridDetectionFinal import ArucoGridDetector
import cv2
import time

detector = ArucoGridDetector(robot_id=28, rows=3, cols=4, cell_size=150.0, camera_index=0)

start = time.time()
while True:
    detector.set_use_wrap(1)
    success = detector.update_frame()
    if not success:
        break

    frame = detector.get_frame()
    cv2.imshow("Output Feed", frame)

    # Robot pos, other markers
    rpos = detector.get_robot_cell_label()
    others = detector.get_other_markers_cells()
    print("Position", rpos)
    print("others", others)
    mid = time.time()

    if mid - start > 5:
        detector.set_detect_grid_state(0)
        print("grid detection is off")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

