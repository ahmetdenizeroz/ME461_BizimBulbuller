import cv2
import numpy as np
import cv2.aruco as aruco
import time

# =========================
# 1. Grid / Homography Helpers
# =========================

def compute_intersection(line1, line2):
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None  # Parallel or coincident
    px = ((x1 * y2 - y1 * x2) * (x3 - x4)
          - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4)
          - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return int(px), int(py)

def find_intersections(lines):
    if lines is None:
        return []
    vertical, horizontal = [], []
    for line in lines:
        x1, y1, x2, y2 = line[0]
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
    if not intersections:
        return []
    sorted_pts = sorted(intersections, key=lambda p: (p[1], p[0]))
    grid_rows = []
    row_tolerance = 20
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
    centers = []
    labels = []
    label_count = 1
    for row_idx in range(len(grid) - 1):
        num_cols_curr = len(grid[row_idx])
        num_cols_next = len(grid[row_idx + 1])
        max_cols = min(num_cols_curr, num_cols_next) - 1
        for col_idx in range(max_cols):
            x1, y1 = grid[row_idx][col_idx]
            x2, y2 = grid[row_idx + 1][col_idx + 1]
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            centers.append((cx, cy))
            labels.append(label_count)
            label_count += 1
    return centers, labels

def average_grid_distance(gridA, gridB):
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

def get_grid_corners(grid):
    if len(grid) < 2:
        return None
    top_row = grid[0]
    bottom_row = grid[-1]
    if len(top_row) < 2 or len(bottom_row) < 2:
        return None
    tl = top_row[0]
    tr = top_row[-1]
    bl = bottom_row[0]
    br = bottom_row[-1]
    return [tl, tr, bl, br]

def warp_point(pt, H):
    x, y = pt
    in_vec = np.array([[x], [y], [1]], dtype=np.float32)
    out_vec = H @ in_vec
    if out_vec[2, 0] != 0:
        ox = int(out_vec[0, 0] / out_vec[2, 0])
        oy = int(out_vec[1, 0] / out_vec[2, 0])
        return (ox, oy)
    return (0, 0)

def point_in_polygon(pt, polygon):
    poly_np = np.array(polygon, dtype=np.int32).reshape((-1,1,2))
    inside = cv2.pointPolygonTest(poly_np, pt, False)
    return inside >= 0

# =========================
# 2. ArUco Setup
# =========================

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
detector_params = aruco.DetectorParameters()

# =========================
# 3. Image Processing Functions
# =========================

def get_triangle_corners(cx, cy, angle_deg, triangle_side):
    """
    Define an equilateral triangle of side = triangle_side,
    centered at (cx, cy) with orientation angle_deg.
    Corner #0 is the front corner.
    """
    R = triangle_side / np.sqrt(3.0)
    angle_rad = np.radians(angle_deg)
    corners = []
    for k in range(3):
        theta = angle_rad + (k * 2.0 * np.pi / 3.0)
        px = cx + R * np.cos(theta)
        py = cy + R * np.sin(theta)
        corners.append((px, py))
    return corners

def get_cell_polygons(grid, homography, use_wrap):
    """
    Return a list of tuples: [( [p0, p1, p2, p3], cell_label ), ... ]
    Each p_i = (x,y) corner of the cell in the final display space.
    """
    polys = []
    cell_label = 1
    for r in range(len(grid) - 1):
        row_top = grid[r]
        row_bot = grid[r + 1]
        num_cols = min(len(row_top), len(row_bot))
        for c in range(num_cols - 1):
            tl = row_top[c]
            tr = row_top[c + 1]
            bl = row_bot[c]
            br = row_bot[c + 1]
            if use_wrap and homography is not None:
                tl = warp_point(tl, homography)
                tr = warp_point(tr, homography)
                bl = warp_point(bl, homography)
                br = warp_point(br, homography)
            poly = [tl, tr, br, bl]
            polys.append((poly, cell_label))
            cell_label += 1
    return polys

def assign_marker_to_cell(tri_corners, cell_polys):
    """
    Check each cell polygon. If tri_corners are all inside the cell polygon,
    return that cell label. If none, return None.
    """
    for (poly, label) in cell_polys:
        if all(point_in_polygon(corner, poly) for corner in tri_corners):
            return label
    return None

def draw_annotations(frame, grid, homography, use_wrap, cell_centers, labels,
                     show_intersections, show_lines, markers, marker_cells, triangle_side):
    """
    Draw grid, cell centers, intersections, lines, markers, and triangles on the frame.
    """
    # Draw cell centers
    for (cx, cy), lbl in zip(cell_centers, labels):
        if use_wrap and homography is not None:
            cx, cy = warp_point((cx, cy), homography)
        cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
        cv2.putText(frame, str(lbl), (cx - 10, cy + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Draw intersections
    if show_intersections:
        num_rows = len(grid)
        for i, row_pts in enumerate(grid):
            num_cols = len(row_pts)
            for j, (x, y) in enumerate(row_pts):
                if use_wrap and homography is not None:
                    x, y = warp_point((x, y), homography)
                # Determine color and radius
                if ((i == 0 and j == 0) or
                    (i == 0 and j == num_cols - 1) or
                    (i == num_rows - 1 and j == 0) or
                    (i == num_rows - 1 and j == num_cols - 1)):
                    color = (0, 165, 255)  # orange
                    radius = 7
                elif i == 0 or i == num_rows - 1 or j == 0 or j == num_cols - 1:
                    color = (0, 255, 0)    # green
                    radius = 5
                else:
                    color = (255, 0, 0)    # blue
                    radius = 4
                cv2.circle(frame, (x, y), radius, color, -1)
    
    # Draw grid lines
    if show_lines:
        cell_polys = get_cell_polygons(grid, homography, use_wrap)
        for (poly, label) in cell_polys:
            cv2.polylines(frame, [np.array(poly)], True, (255, 105, 180), 2)
    
    # Draw markers and their triangles
    for marker, cell_label in zip(markers, marker_cells):
        marker_id, (cx, cy), angle_deg = marker
        tri_corners = get_triangle_corners(cx, cy, angle_deg, triangle_side)
        # Draw triangle
        cv2.polylines(frame, [np.array(tri_corners, dtype=np.int32)], True, (0, 255, 0), 2)
        # Draw line from center to front corner
        front_corner = tri_corners[0]
        cv2.line(frame, (int(cx), int(cy)),
                 (int(front_corner[0]), int(front_corner[1])),
                 (0, 255, 255), 2)
        # Draw bounding box and labels already handled in detection
    
    return frame

# =========================
# 4. Main Processing Loop
# =========================

def main():
    # Parameters (adjust as needed)
    robot_id = 27
    rows = 3
    cols = 4
    cell_size = 100  # e.g., in millimeters
    camera_index = 2  # Change if your camera is not at index 0
    detect_grid = True
    use_wrap = False
    show_intersections = False
    show_lines = False
    triangle_side = 80  # Adjust the triangle side length as needed
    cluster_dist = 50
    update_thresh = 15

    # Initialize video capture
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Initialize variables
    last_valid_grid = None
    last_valid_homography = None

    fps_start_time = time.time()
    fps_frame_count = 0
    fps = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera.")
                break

            # Optionally detect/update grid
            if detect_grid:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                binary = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 15, 10
                )
                edges = cv2.Canny(binary, 50, 150)
                lines = cv2.HoughLinesP(edges, 1, np.pi/180, 60, minLineLength=30, maxLineGap=10)

                raw_intx = find_intersections(lines)
                clustered = cluster_points(raw_intx, cluster_dist)
                new_grid = sort_into_grid(clustered)

                if new_grid:
                    if last_valid_grid is None:
                        last_valid_grid = new_grid
                    else:
                        dist = average_grid_distance(last_valid_grid, new_grid)
                        if dist > update_thresh:
                            last_valid_grid = new_grid

                    corners_4 = get_grid_corners(last_valid_grid)
                    if corners_4 is not None:
                        image_corner_pts = np.float32(corners_4)
                        real_corner_pts = np.float32([
                            [0, 0],
                            [cols * cell_size, 0],
                            [0, rows * cell_size],
                            [cols * cell_size, rows * cell_size]
                        ])
                        H = cv2.getPerspectiveTransform(image_corner_pts, real_corner_pts)
                        last_valid_homography = H
            else:
                # If grid detection is turned off, retain the last valid grid and homography
                pass

            # Possibly warp the frame
            display_frame = frame.copy()
            used_homography = False
            if use_wrap and last_valid_homography is not None:
                out_w = int(cols * cell_size)
                out_h = int(rows * cell_size)
                if out_w < 1: out_w = 1
                if out_h < 1: out_h = 1
                display_frame = cv2.warpPerspective(frame, last_valid_homography, (out_w, out_h))
                used_homography = True

            # ArUco detection
            corners, ids, _ = aruco.detectMarkers(display_frame, aruco_dict, parameters=detector_params)
            markers = []
            if ids is not None and len(ids) > 0:
                for i, cset in enumerate(corners):
                    c = cset[0]
                    corner_pts = [(int(pt[0]), int(pt[1])) for pt in c]
                    cx = int(np.mean([pt[0] for pt in corner_pts]))
                    cy = int(np.mean([pt[1] for pt in corner_pts]))
                    dx = corner_pts[1][0] - corner_pts[0][0]
                    dy = corner_pts[1][1] - corner_pts[0][1]
                    angle_deg = np.degrees(np.arctan2(dy, dx))

                    marker_id = int(ids[i])
                    markers.append((marker_id, (cx, cy), angle_deg))

                    # Draw bounding box & center
                    cv2.polylines(display_frame, [np.array(corner_pts)], True, (255, 255, 0), 2)
                    cv2.circle(display_frame, (cx, cy), 5, (255, 255, 0), -1)

                    # Label
                    id_text = "Bulbul" if marker_id == robot_id else f"ID: {marker_id}"
                    x0, y0 = corner_pts[0]
                    x1, y1 = corner_pts[1]
                    cv2.putText(display_frame, id_text, (x0, y0 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 2)
                    cv2.putText(display_frame, f"{angle_deg:.1f} deg", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 2)
                    # Old front line removed; will add new front line based on triangle

            # Assign markers to cells using equilateral triangle logic
            marker_cells = []
            if last_valid_grid is not None and len(markers) > 0:
                cell_polys = get_cell_polygons(last_valid_grid, last_valid_homography, use_wrap)
                for marker in markers:
                    marker_id, (cx, cy), angle_deg = marker
                    tri_corners = get_triangle_corners(cx, cy, angle_deg, triangle_side)
                    # Draw triangle
                    cv2.polylines(display_frame, [np.array(tri_corners, dtype=np.int32)], True, (0, 255, 0), 2)
                    # Draw line from center to front corner
                    front_corner = tri_corners[0]
                    cv2.line(display_frame, (int(cx), int(cy)),
                             (int(front_corner[0]), int(front_corner[1])),
                             (0, 255, 255), 2)
                    # Assign to cell
                    cell_label = assign_marker_to_cell(tri_corners, cell_polys)
                    marker_cells.append(cell_label)

            # Draw grid overlays
            if last_valid_grid is not None:
                cell_centers, labels = find_cell_centers(last_valid_grid)
                display_frame = draw_annotations(display_frame, last_valid_grid, last_valid_homography,
                                                use_wrap, cell_centers, labels,
                                                show_intersections, show_lines,
                                                markers, marker_cells, triangle_side)

            # FPS Calculation
            fps_frame_count += 1
            current_time = time.time()
            elapsed = current_time - fps_start_time
            if elapsed >= 1.0:
                fps = fps_frame_count / elapsed
                fps_frame_count = 0
                fps_start_time = current_time

            # Overlay FPS on the frame
            cv2.putText(display_frame, f"FPS: {fps:.2f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Display the processed frame
            cv2.imshow("Processed Feed", display_frame)

            # Exit on pressing 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")

    finally:
        # Release resources
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

