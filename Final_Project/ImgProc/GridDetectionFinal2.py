import cv2
import numpy as np
import cv2.aruco as aruco

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

def point_in_polygon(pt, polygon):
    poly_np = np.array(polygon, dtype=np.int32).reshape((-1,1,2))
    inside = cv2.pointPolygonTest(poly_np, pt, False)
    return inside >= 0

# ArUco Setup
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
detector_params = aruco.DetectorParameters()

class ArucoGridDetector:
    """
    Equilateral-triangle logic for cell detection, with a toggle for grid recognition.
    The line from the marker's center to the front corner of the triangle replaces
    the old midpoint-based line.
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
        self.detect_grid = 1         # 1=grid detection on, 0=off
        self.cluster_dist = 50
        self.update_thresh = 15
        self.show_intersections = 0
        self.show_lines = 0
        self.use_wrap = 0
        self.triangle_side = 100  # side of the equilateral triangle

        # Internal state
        self.cap = cv2.VideoCapture(camera_index)
        self.last_valid_grid = None
        self.last_valid_homography = None
        self.display_frame = None

        # Robot/markers
        self.robot_position = None  # (x, y, angle_deg)
        self.other_markers = []     # list of (marker_id, (x,y), angle_deg)
        self.robot_cell_label = None
        self.other_markers_cell_labels = []

    # ======= Setters =======
    def set_detect_grid_state(self, val):
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

    def set_triangle_side(self, val):
        self.triangle_side = val

    # ======= Main Processing =======
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame from camera.")
            return False

        # Possibly update the grid if detect_grid == 1
        if self.detect_grid == 1:
            self.update_grid(frame)

        # Possibly warp
        display_frame = frame.copy()
        used_homography = False
        if self.use_wrap == 1 and self.last_valid_homography is not None:
            out_w = int(self.cols * self.cell_size)
            out_h = int(self.rows * self.cell_size)
            if out_w < 1: out_w = 1
            if out_h < 1: out_h = 1
            display_frame = cv2.warpPerspective(frame, self.last_valid_homography, (out_w, out_h))
            used_homography = True

        # ArUco detection
        self.detect_aruco(display_frame)

        # Triangle-based cell assignment (if grid is known)
        self.robot_cell_label = None
        self.other_markers_cell_labels = []
        if self.last_valid_grid is not None:
            self._assign_markers_to_cells(display_frame, used_homography)

        # Draw grid
        if self.last_valid_grid is not None:
            self.draw_grid(display_frame, used_homography)

        self.display_frame = display_frame
        return True

    def update_grid(self, frame):
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
                    self.robot_position = (cx, cy, angle_deg)
                else:
                    self.other_markers.append((marker_id, (cx, cy), angle_deg))

                # Draw bounding box & center
                cv2.polylines(display_frame, [np.array(corner_pts)], True, (255, 255, 0), 2)
                cv2.circle(display_frame, (cx, cy), 5, (255, 255, 0), -1)

                # Label
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

                # We no longer draw the old front line here. That will be replaced
                # by drawing from center to the front corner of the triangle later.

    # --------------------------------------------------------------------------
    # Equilateral Triangle => check if corners are inside a single cell polygon
    # and draw line from center -> front triangle corner
    # --------------------------------------------------------------------------
    def _assign_markers_to_cells(self, display_frame, used_homography):
        cell_polys = self._get_cell_polygons(used_homography)

        # Robot
        if self.robot_position is not None:
            rx, ry, rangle = self.robot_position
            tri_corners = self._get_triangle_corners(rx, ry, rangle)
            # Draw triangle
            pts_np = np.array(tri_corners, dtype=np.int32).reshape((-1,1,2))
            cv2.polylines(display_frame, [pts_np], True, (0,255,0), 2)

            # Draw line from center to the front corner = tri_corners[0]
            front_corner = tri_corners[0]
            cv2.line(display_frame,
                     (int(rx), int(ry)),
                     (int(front_corner[0]), int(front_corner[1])),
                     (0, 255, 255), 2)

            self.robot_cell_label = self._find_cell_for_triangle(tri_corners, cell_polys)

        # Other markers
        self.other_markers_cell_labels = []
        for (mid, (mx, my), angle_deg) in self.other_markers:
            tri_corners = self._get_triangle_corners(mx, my, angle_deg)
            pts_np = np.array(tri_corners, dtype=np.int32).reshape((-1,1,2))
            cv2.polylines(display_frame, [pts_np], True, (0,255,0), 2)

            # line from center to front corner
            front_corner = tri_corners[0]
            cv2.line(display_frame,
                     (int(mx), int(my)),
                     (int(front_corner[0]), int(front_corner[1])),
                     (0, 255, 255), 2)

            cell_label = self._find_cell_for_triangle(tri_corners, cell_polys)
            self.other_markers_cell_labels.append((mid, cell_label, angle_deg))

    def _get_cell_polygons(self, used_homography):
        polys = []
        cell_label = 1
        for r in range(len(self.last_valid_grid) - 1):
            row_top = self.last_valid_grid[r]
            row_bot = self.last_valid_grid[r + 1]
            num_cols = min(len(row_top), len(row_bot))
            for c in range(num_cols - 1):
                tl = row_top[c]
                tr = row_top[c + 1]
                bl = row_bot[c]
                br = row_bot[c + 1]
                if used_homography and self.last_valid_homography is not None:
                    tl = warp_point(tl, self.last_valid_homography)
                    tr = warp_point(tr, self.last_valid_homography)
                    bl = warp_point(bl, self.last_valid_homography)
                    br = warp_point(br, self.last_valid_homography)
                poly = [tl, tr, br, bl]
                polys.append((poly, cell_label))
                cell_label += 1
        return polys

    def _get_triangle_corners(self, cx, cy, angle_deg):
        """
        The distance from centroid to each corner is side / sqrt(3).
        We define corners at angle_deg + 0°, +120°, +240° from horizontal.
        Corner #0 => 'front' corner
        """
        R = self.triangle_side / np.sqrt(3.0)
        angle_rad = np.radians(angle_deg)
        corners = []
        for k in range(3):
            theta = angle_rad + (k * 2.0 * np.pi / 3.0)
            px = cx + R * np.cos(theta)
            py = cy + R * np.sin(theta)
            corners.append((px, py))
        return corners

    def _find_cell_for_triangle(self, tri_corners, cell_polys):
        for (poly, label) in cell_polys:
            inside_count = 0
            for corner in tri_corners:
                if point_in_polygon(corner, poly):
                    inside_count += 1
                else:
                    break
            if inside_count == 3:
                return label
        return None

    # ======= Draw Grid Overlays =======
    def draw_grid(self, display_frame, used_homography):
        cell_centers, labels = find_cell_centers(self.last_valid_grid)
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

                    if ((i == 0 and j == 0) or
                        (i == 0 and j == len(row_pts)-1) or
                        (i == num_rows-1 and j == 0) or
                        (i == num_rows-1 and j == len(row_pts)-1)):
                        color = (0, 165, 255)
                        radius = 7
                    elif i == 0 or i == num_rows-1 or j == 0 or j == len(row_pts)-1:
                        color = (0, 255, 0)
                        radius = 5
                    else:
                        color = (255, 0, 0)
                        radius = 4
                    cv2.circle(display_frame, (x, y), radius, color, -1)

        if self.show_lines == 1:
            num_rows = len(self.last_valid_grid)
            for i in range(num_rows):
                row_pts = self.last_valid_grid[i]
                for j in range(len(row_pts) - 1):
                    p1 = row_pts[j]
                    p2 = row_pts[j + 1]
                    if used_homography and self.last_valid_homography is not None:
                        p1 = warp_point(p1, self.last_valid_homography)
                        p2 = warp_point(p2, self.last_valid_homography)
                    cv2.line(display_frame, p1, p2, (255, 105, 180), 2)
            for i in range(num_rows - 1):
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

    # ======= Getters =======
    def get_frame(self):
        return self.display_frame

    def get_robot_position(self):
        """(x, y, angle_deg) in final coords if wrap=1 or original if wrap=0."""
        return self.robot_position

    def get_robot_cell_label(self):
        """Which cell the robot's triangle is in, or None."""
        return self.robot_cell_label

    def get_other_markers(self):
        """List of (marker_id, (x, y), angle_deg)."""
        return self.other_markers

    def get_other_markers_cells(self):
        """List of (marker_id, cell_label, angle_deg). cell_label=None if no cell encloses it."""
        return self.other_markers_cell_labels

    def release(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
