# main.py
import tkinter as tk
from gui import PathfindingGUI
from image_proc import ImageProcessor
import threading
import time

def main():
    # 1) Ask for user inputs
    robot_id = int(input("Enter the ArUco ID for Bülbül: "))
    n = int(input("Number of rows in grid (n): "))
    m = int(input("Number of columns in grid (m): "))
    cell_size = float(input("Physical size of one cell (e.g. mm): "))

    # 2) Create the image processor
    ip = ImageProcessor(robot_id=robot_id, n=n, m=m, cell_size=cell_size)
    if not ip.is_opened():
        print("Camera not opened!")
        return

    # 3) Create the Tkinter GUI
    root = tk.Tk()
    app = PathfindingGUI(root, rows=n, cols=m, cell_size=100)

    # We'll define a method that runs periodically to:
    #   - Read a camera frame
    #   - Detect grid (optional)
    #   - Detect ArUco
    #   - If the correct ID is found, warp center -> find robot cell
    def update_loop():
        frame = ip.read_frame()
        if frame is not None:
            # We can do grid detection
            ip.detect_grid(frame, cluster_dist=50, update_thresh=10)
            
            # For demonstration, we skip drawing to a window here
            # Instead, we do ArUco detection
            detections = ip.detect_aruco(frame)
            for (marker_id, (cx, cy), angle, corners) in detections:
                if marker_id == robot_id:
                    # find robot's cell
                    rcell = ip.find_robot_cell((cx, cy))
                    if rcell is not None:
                        # Update GUI with robot location
                        app.set_robot_cell(rcell[0], rcell[1])
        
        # Schedule next call
        root.after(100, update_loop)

    # Start the loop
    root.after(100, update_loop)
    root.mainloop()

    # Cleanup
    ip.close()

if __name__ == "__main__":
    main()

