# image_proc.py
import cv2
import numpy as np
import cv2.aruco as aruco

# ============= Grid / Homography Helpers =============

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
    """Apply homography to a single point (x, y)."""
    x, y = pt
    in_vec = np.array([[x], [y], [1]], dtype=np.float32)
    out_vec = H @ in_vec
    if out_vec[2, 0] != 0:
        ox = int(out_vec[0, 0] / out_vec[2, 0])
        oy = int(out_vec[1, 0] / out_vec[2, 0])
        return ox, oy
    return (0, 0)

# ============= ArUco Setup ============
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
detector_params = aruco.DetectorParameters()

class ImageProcessor:
    """
    A class that continuously reads from webcam #2, detects the grid + ArUco markers,
    tries to find the robot's row,col location in the grid if perspective is known.
    """
    def __init__(self, robot_id, n, m, cell_size):
        self.robot_id = robot_id
        self.n = n
        self.m = m
        self.cell_size = cell_size
        
        # Real-world corners
        self.real_corner_pts = np.float32([
            [0, 0],
            [m * cell_size, 0],
            [0, n * cell_size],
            [m * cell_size, n * cell_size]
        ])
        
        self.cap = cv2.VideoCapture(2)
        self.last_valid_grid = None
        self.last_valid_homography = None
    
    def is_opened(self):
        return self.cap.isOpened()

    def read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def close(self):
        self.cap.release()

    def detect_grid(self, frame, cluster_dist=50, update_thresh=10):
        """
        Detect lines -> intersections -> new grid. If differs from last grid
        significantly, update it. Then compute homography if possible.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 15, 10)
        edges = cv2.Canny(binary, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 60, minLineLength=30, maxLineGap=10)
        
        raw_intx = find_intersections(lines)
        if cluster_dist < 1:
            cluster_dist = 1
        clustered = cluster_points(raw_intx, cluster_dist)
        new_grid = sort_into_grid(clustered)

        # Compare to old grid
        if new_grid:
            if self.last_valid_grid is None:
                self.last_valid_grid = new_grid
            else:
                dist = self._average_grid_distance(self.last_valid_grid, new_grid)
                if dist > update_thresh:
                    self.last_valid_grid = new_grid
            
            # Attempt homography
            corners_4 = get_grid_corners(self.last_valid_grid)
            if corners_4 is not None:
                image_corner_pts = np.float32(corners_4)
                H = cv2.getPerspectiveTransform(image_corner_pts, self.real_corner_pts)
                self.last_valid_homography = H
    
    def detect_aruco(self, frame):
        """Detect ArUco markers in the given frame; return a list of (id, center, angle)."""
        corners, ids, _ = aruco.detectMarkers(frame, aruco_dict, parameters=detector_params)
        detections = []
        if ids is not None and len(ids) > 0:
            for i, cset in enumerate(corners):
                c = cset[0]  # shape (4,2)
                corner_pts = [(int(pt[0]), int(pt[1])) for pt in c]
                cx = int(np.mean([pt[0] for pt in corner_pts]))
                cy = int(np.mean([pt[1] for pt in corner_pts]))
                dx = corner_pts[1][0] - corner_pts[0][0]
                dy = corner_pts[1][1] - corner_pts[0][1]
                angle_deg = np.degrees(np.arctan2(dy, dx))
                marker_id = int(ids[i])
                
                detections.append((marker_id, (cx, cy), angle_deg, corner_pts))
        return detections

    def find_robot_cell(self, robot_center):
        """
        Using the last_valid_homography, warp the robot center into top-down coords
        and compute which cell (row,col) it's in. Return (row,col) or None if out of bounds.
        """
        if self.last_valid_homography is None:
            return None
        warped_pt = warp_point(robot_center, self.last_valid_homography)
        x, y = warped_pt
        # Each cell is cell_size wide in the warped image
        col = x // int(self.cell_size)
        row = y // int(self.cell_size)
        if 0 <= row < self.n and 0 <= col < self.m:
            return (row, col)
        return None

    def _average_grid_distance(self, gridA, gridB):
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

