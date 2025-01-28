import cv2
import numpy as np
import cv2.aruco as aruco

# =========================
# 1. Grid / Homography Helpers
# =========================

def compute_intersection(line1, line2):
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None
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

# ArUco Setup
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
detector_params = aruco.DetectorParameters()

class ArucoGridDetector:
    """
    A class to detect a grid from lines (toggleable),
    detect ArUco markers (always),
    and optionally warp/draw the final frame.
    """

    def __init__(self, robot_id, rows, cols, cell_size, camera_index=2):
        self.robot_id = robot_id
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size

        self.real_corner_pts = np.float32([
            [0, 0],
            [self.cols * self.cell_size, 0],
            [0, self.rows * self.cell_size],
            [self.cols * self.cell_size, self.rows * self.cell_size]
        ])

        # Toggles & parameters
        self.detect_grid = 1          # 1=on, 0=off (for grid detection)
        self.cluster_dist = 90
        self.update_thresh = 15
        self.show_intersections = 0
        self.show_lines = 0
        self.use_wrap = 0

        # Internal state
        self.cap = cv2.VideoCapture(camera_index)
        self.last_valid_grid = None
        self.last_valid_homography = None

        # The final annotated frame
        self.display_frame = None

        # Robot & markers
        self.robot_position = None
        self.other_markers = []
        self.robot_cell_label = None
        self.other_markers_cell_labels = []

    # ======= Setters =======
    def set_detect_grid_state(self, val):
        """
        Set whether we detect/refresh the grid each frame (1) or skip (0).
        Note that if we skip, we keep the old grid/homography if we had one.
        """
        self.detect_grid = val

    def set_cluster_dist(self, val):
        self.cluster_dist = val

    def set_update_thresh(self, val):
        self.update_thresh = val

    def set_show_intersections(self, val):
        self.show_intersections = val

    def set_show_lines(self, val):
        self.show_lines = val

    def set_use_wrap(self, val):
        self.use_wrap = val

    # ======= Processing =======
    def update_frame(self):
        """
        Grab a frame, optionally detect/refresh the grid, always detect ArUco,
        store the annotated frame in self.display_frame.
        Returns True if success, False if camera read failed.
        """
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame from camera.")
            return False

        # 1) If detect_grid==1, do grid detection; else skip
        if self.detect_grid == 1:
            self.update_grid(frame)

        # 2) Possibly warp the feed
        display_frame = frame.copy()
        used_homography = False
        if self.use_wrap == 1 and self.last_valid_homography is not None:
            out_w = int(self.cols * self.cell_size)
            out_h = int(self.rows * self.cell_size)
            if out_w < 1: out_w = 1
            if out_h < 1: out_h = 1
            display_frame = cv2.warpPerspective(frame, self.last_valid_homography, (out_w, out_h))
            used_homography = True

        # 3) Always detect ArUco
        self.detect_aruco(display_frame)

        # 4) If we have a valid grid, draw it
        if self.last_valid_grid is not None:
            self.draw_grid(display_frame, used_homography)

        # 5) Assign marker cells (only if grid is available)
        self.assign_marker_cells(used_homography)

        self.display_frame = display_frame
        return True

    def update_grid(self, frame):
        """Detect and refresh the grid from the frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 15, 10
        )
        edges = cv2.Canny(binary, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 60, minLineLength=30, maxLineGap=10)

        raw_intx = find_intersections(lines)
        cdist = max(1, self.cluster_dist)
        clustered = cluster_points(raw_intx, cdist)
        new_grid = sort_into_grid(clustered)

        if new_grid:
            if self.last_valid_grid is None:
                self.last_valid_grid = new_grid
            else:
                dist = average_grid_distance(self.last_valid_grid, new_grid)
                if dist > self.update_thresh:
                    self.last_valid_grid = new_grid

            corners_4 = get_grid_corners(self.last_valid_grid)
            if corners_4 is not None:
                image_corner_pts = np.float32(corners_4)
                H = cv2.getPerspectiveTransform(image_corner_pts, self.real_corner_pts)
                self.last_valid_homography = H

    def detect_aruco(self, display_frame):
        """Always run ArUco detection, storing robot + others."""
        corners, ids, _ = aruco.detectMarkers(display_frame, aruco_dict, parameters=detector_params)
        self.robot_position = None
        self.other_markers = []

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
                if marker_id == self.robot_id:
                    self.robot_position = (cx, cy)
                else:
                    self.other_markers.append((marker_id, (cx, cy), angle_deg))

                # Draw bounding box, center, orientation
                cv2.polylines(display_frame, [np.array(corner_pts)], True, (255, 255, 0), 2)
                cv2.circle(display_frame, (cx, cy), 5, (255, 255, 0), -1)
                if marker_id == self.robot_id:
                    id_text = "Bulbul"
                else:
                    id_text = f"ID: {marker_id}"
                x0, y0 = corner_pts[0]
                x1, y1 = corner_pts[1]
                cv2.putText(display_frame, id_text, (x0, y0 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 2)
                cv2.putText(display_frame, f"{angle_deg:.1f} deg", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 2)

                fx = (corner_pts[0][0] + corner_pts[1][0]) // 2
                fy = (corner_pts[0][1] + corner_pts[1][1]) // 2
                cv2.line(display_frame, (cx, cy), (fx, fy), (0, 255, 255), 2)

    def draw_grid(self, display_frame, used_homography):
        cell_centers, labels = find_cell_centers(self.last_valid_grid)
        # cell centers in red
        for (cx, cy), lbl in zip(cell_centers, labels):
            if used_homography and self.last_valid_homography is not None:
                cx, cy = warp_point((cx, cy), self.last_valid_homography)
            cv2.circle(display_frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(display_frame, str(lbl), (cx - 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if self.show_intersections == 1:
            num_rows = len(self.last_valid_grid)
            for i, row_pts in enumerate(self.last_valid_grid):
                for j, (x, y) in enumerate(row_pts):
                    if used_homography and self.last_valid_homography is not None:
                        x, y = warp_point((x, y), self.last_valid_homography)
                    # color logic
                    if ((i == 0 and j == 0) or
                        (i == 0 and j == len(row_pts)-1) or
                        (i == num_rows-1 and j == 0) or
                        (i == num_rows-1 and j == len(row_pts)-1)):
                        color = (0, 165, 255)  # orange
                        radius = 7
                    elif i == 0 or i == num_rows-1 or j == 0 or j == len(row_pts)-1:
                        color = (0, 255, 0)  # green
                        radius = 5
                    else:
                        color = (255, 0, 0)  # blue
                        radius = 4
                    cv2.circle(display_frame, (x, y), radius, color, -1)

        if self.show_lines == 1:
            num_rows = len(self.last_valid_grid)
            for i in range(num_rows):
                row_pts = self.last_valid_grid[i]
                for j in range(len(row_pts)-1):
                    p1 = row_pts[j]
                    p2 = row_pts[j+1]
                    if used_homography and self.last_valid_homography is not None:
                        p1 = warp_point(p1, self.last_valid_homography)
                        p2 = warp_point(p2, self.last_valid_homography)
                    cv2.line(display_frame, p1, p2, (255, 105, 180), 2)
            for i in range(num_rows-1):
                row_pts_this = self.last_valid_grid[i]
                row_pts_next = self.last_valid_grid[i+1]
                max_cols = min(len(row_pts_this), len(row_pts_next))
                for col in range(max_cols):
                    p1 = row_pts_this[col]
                    p2 = row_pts_next[col]
                    if used_homography and self.last_valid_homography is not None:
                        p1 = warp_point(p1, self.last_valid_homography)
                        p2 = warp_point(p2, self.last_valid_homography)
                    cv2.line(display_frame, p1, p2, (255, 105, 180), 2)

    def assign_marker_cells(self, used_homography):
        self.robot_cell_label = None
        self.other_markers_cell_labels = []
        if self.last_valid_grid is None:
            return
        cell_centers, labels = find_cell_centers(self.last_valid_grid)
        # warp centers if needed
        warped_centers = []
        if used_homography and self.last_valid_homography is not None:
            for pt in cell_centers:
                wx, wy = warp_point(pt, self.last_valid_homography)
                warped_centers.append((wx, wy))
        else:
            warped_centers = cell_centers

        # main robot
        if self.robot_position is not None:
            rx, ry = self.robot_position
            best_label = None
            best_dist = 999999
            for (cx, cy), lbl in zip(warped_centers, labels):
                dist = np.hypot(rx-cx, ry-cy)
                if dist < best_dist:
                    best_dist = dist
                    best_label = lbl
            self.robot_cell_label = best_label

        # other markers
        for (mid, (mx, my), angle_deg) in self.other_markers:
            best_label = None
            best_dist = 999999
            for (cx, cy), lbl in zip(warped_centers, labels):
                dist = np.hypot(mx-cx, my-cy)
                if dist < best_dist:
                    best_dist = dist
                    best_label = lbl
            self.other_markers_cell_labels.append((mid, best_label, angle_deg))

    # ======= Getters =======
    def get_frame(self):
        return self.display_frame

    def get_robot_position(self):
        return self.robot_position

    def get_robot_cell_label(self):
        return self.robot_cell_label

    def get_other_markers(self):
        return self.other_markers

    def get_other_markers_cells(self):
        return self.other_markers_cell_labels

    def release(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

