import cv2
import numpy as np

# ------------------------------
# Helper Functions
# ------------------------------

def compute_intersection(line1, line2):
    """
    Given two lines each defined as (x1,y1,x2,y2),
    compute their intersection point. Return None if parallel.
    """
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None  # Parallel or coincident
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return int(px), int(py)

def find_intersections(lines):
    """
    Split lines into vertical/horizontal sets,
    then compute intersection points.
    """
    if lines is None:
        return []
    vertical, horizontal = [], []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # If the line is more vertical than horizontal, treat as vertical
        if abs(x1 - x2) < abs(y1 - y2):
            vertical.append((x1, y1, x2, y2))
        else:
            horizontal.append((x1, y1, x2, y2))

    intersections = []
    for v_line in vertical:
        for h_line in horizontal:
            pt = compute_intersection(v_line, h_line)
            if pt is not None:
                intersections.append(pt)
    return intersections

def cluster_points(points, cluster_dist):
    """
    Clusters a list of (x, y) points. If a point is within cluster_dist
    of a cluster, it merges into that cluster. Returns the cluster centers.
    """
    if not points:
        return []
    pts = np.array(points)
    clusters = []
    while len(pts) > 0:
        ref = pts[0]
        dists = np.linalg.norm(pts - ref, axis=1)
        close_mask = dists < cluster_dist
        close_points = pts[close_mask]
        cluster_center = np.mean(close_points, axis=0).astype(int)
        clusters.append(tuple(cluster_center))
        pts = pts[~close_mask]
    return clusters

def sort_into_grid(intersections):
    """
    Sort intersection points into rows (by y), then each row by x.
    Returns a list of rows, e.g. [ [(x00,y00),(x01,y01),...], [(...),(...)] ].
    """
    if not intersections:
        return []
    # Sort all points by Y first, then X
    sorted_pts = sorted(intersections, key=lambda p: (p[1], p[0]))

    grid_rows = []
    row_tolerance = 20  # how close in Y to be considered the same row
    current_row = [sorted_pts[0]]

    for i in range(1, len(sorted_pts)):
        if abs(sorted_pts[i][1] - current_row[-1][1]) < row_tolerance:
            current_row.append(sorted_pts[i])
        else:
            grid_rows.append(sorted(current_row, key=lambda p: p[0]))
            current_row = [sorted_pts[i]]
    grid_rows.append(sorted(current_row, key=lambda p: p[0]))

    return grid_rows

def find_cell_centers(grid):
    """
    For a grid of R rows and C columns of intersection points,
    we can form (R-1)*(C-1) cells. The center of each cell is the midpoint
    of the diagonal corners.
    """
    centers = []
    labels = []
    label_count = 1
    for row_idx in range(len(grid) - 1):
        num_cols_current = len(grid[row_idx])
        num_cols_next = len(grid[row_idx + 1])
        max_cols = min(num_cols_current, num_cols_next) - 1
        for col_idx in range(max_cols):
            x1, y1 = grid[row_idx][col_idx]
            x2, y2 = grid[row_idx + 1][col_idx + 1]
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            centers.append((center_x, center_y))
            labels.append(label_count)
            label_count += 1
    return centers, labels

def average_grid_distance(gridA, gridB):
    """
    Compute the average distance between two grids (row by row).
    If shapes differ, return a large number to indicate mismatch.
    """
    if len(gridA) != len(gridB):
        return 999999
    total_dist = 0.0
    total_points = 0
    for rowA, rowB in zip(gridA, gridB):
        if len(rowA) != len(rowB):
            return 999999
        for (xA, yA), (xB, yB) in zip(rowA, rowB):
            total_dist += np.linalg.norm([xA - xB, yA - yB])
            total_points += 1
    if total_points == 0:
        return 999999
    return total_dist / total_points

# ------------------------------
# Main Script
# ------------------------------

def main():
    import sys
    print("Press 'q' to quit.")
    
    # Open webcam #2
    cap = cv2.VideoCapture(2)
    if not cap.isOpened():
        print("Could not open webcam #2.")
        sys.exit(1)
    
    # Create "Settings" window with trackbars
    cv2.namedWindow("Settings", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Settings", 400, 250)
    
    # 1) Grid Detection toggle (0=Stop, 1=Start)
    cv2.createTrackbar("Grid Detection", "Settings", 1, 1, lambda x: None)
    # 2) Clustering distance slider
    cv2.createTrackbar("Cluster Dist", "Settings", 50, 200, lambda x: None)
    # 3) Update threshold slider
    cv2.createTrackbar("Update Thresh", "Settings", 10, 100, lambda x: None)
    # 4) Show intersections toggle
    cv2.createTrackbar("Show Intersections", "Settings", 0, 1, lambda x: None)
    # 5) Show lines toggle
    cv2.createTrackbar("Show Lines", "Settings", 0, 1, lambda x: None)
    
    last_valid_grid = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from camera.")
            break
        
        # Show the "Input Feed" in a window
        cv2.imshow("Input Feed", frame)
        
        # Read trackbar positions
        detect_grid = cv2.getTrackbarPos("Grid Detection", "Settings")
        cluster_dist = cv2.getTrackbarPos("Cluster Dist", "Settings")
        update_thresh = cv2.getTrackbarPos("Update Thresh", "Settings")
        show_intersections = cv2.getTrackbarPos("Show Intersections", "Settings")
        show_lines = cv2.getTrackbarPos("Show Lines", "Settings")

        # If detection is ON, run the detection logic
        if detect_grid == 1:
            # Basic image processing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Use adaptive threshold to get a binary image
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 15, 10
            )
            edges = cv2.Canny(binary, 50, 150)
            
            # Hough lines
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 60, minLineLength=30, maxLineGap=10)
            
            # Find intersections & cluster
            raw_intersections = find_intersections(lines)
            if cluster_dist < 1:
                cluster_dist = 1  # avoid zero or negative
            clustered = cluster_points(raw_intersections, cluster_dist)
            
            # Sort into grid
            new_grid = sort_into_grid(clustered)
            
            # Decide whether to update the old grid based on the "Update Thresh"
            if new_grid:
                if last_valid_grid is None:
                    # If we don't have an old grid, accept the new one
                    last_valid_grid = new_grid
                else:
                    dist = average_grid_distance(last_valid_grid, new_grid)
                    # If the new grid changes by more than update_thresh, accept it
                    if dist > update_thresh:
                        last_valid_grid = new_grid
                    # else keep the old grid

        # If detection is OFF (detect_grid==0), we do not update last_valid_grid
        # We just keep displaying the existing grid on screen.

        # -------------------------------------
        # Draw results based on last_valid_grid
        # -------------------------------------
        output_frame = frame.copy()
        
        if last_valid_grid:
            # 1) Find cell centers
            cell_centers, labels = find_cell_centers(last_valid_grid)
            
            # 2) Draw cell centers (always visible)
            for (cx, cy), lbl in zip(cell_centers, labels):
                cv2.circle(output_frame, (cx, cy), 4, (0, 0, 255), -1)  # red point
                cv2.putText(output_frame, str(lbl), (cx - 10, cy + 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (255, 255, 255), 2)
            
            # 3) If "Show Intersections" is ON, draw intersection points
            if show_intersections == 1:
                num_rows = len(last_valid_grid)
                for i, row_pts in enumerate(last_valid_grid):
                    num_cols = len(row_pts)
                    for j, (x, y) in enumerate(row_pts):
                        # Check if corner (outermost corner)
                        if ((i == 0 and j == 0) or
                            (i == 0 and j == num_cols - 1) or
                            (i == num_rows - 1 and j == 0) or
                            (i == num_rows - 1 and j == num_cols - 1)):
                            color = (0, 165, 255)  # orange (BGR)
                            radius = 7
                        # Else if outer row or col
                        elif i == 0 or i == num_rows - 1 or j == 0 or j == num_cols - 1:
                            color = (0, 255, 0)  # green
                            radius = 5
                        else:
                            color = (255, 0, 0)  # blue
                            radius = 4
                        cv2.circle(output_frame, (x, y), radius, color, -1)
            
            # 4) If "Show Lines" is ON, draw all grid lines in pink
            if show_lines == 1:
                # A. All horizontal lines
                num_rows = len(last_valid_grid)
                for i in range(num_rows):
                    row_pts = last_valid_grid[i]
                    for j in range(len(row_pts) - 1):
                        p1 = row_pts[j]
                        p2 = row_pts[j + 1]
                        cv2.line(output_frame, p1, p2, (255, 105, 180), 2)  # pink

                # B. All vertical lines
                for i in range(num_rows - 1):
                    row_pts_this = last_valid_grid[i]
                    row_pts_next = last_valid_grid[i + 1]
                    max_cols = min(len(row_pts_this), len(row_pts_next))
                    for col in range(max_cols):
                        p1 = row_pts_this[col]
                        p2 = row_pts_next[col]
                        cv2.line(output_frame, p1, p2, (255, 105, 180), 2)

        # Show the "Output Feed"
        cv2.imshow("Output Feed", output_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

