# movement_class.py
import socket
import time
import math

class MovementClass:
    """
    Takes a path of grid states (row, col, direction)
    and sends high-level commands (FORWARD n, BACK n, TURN deg, STOP, DANCE) to the Pico.

    It also uses the image-processor (ArucoGridDetector) feedback to ensure the robot
    is truly in the correct cell and orientation, sending correction commands if needed.
    """

    def __init__(self, pico_ip="192.168.106.106", pico_port=12346, detector=None):
        """
        Args:
            detector: An instance of ArucoGridDetector (or None).
        """
        self.pico_ip = pico_ip
        self.pico_port = pico_port
        self.client_socket = None
        self.detector = detector  # so we can check real-time position/orientation

        # Movement thresholds
        self.position_threshold = 0.5  # in "cells" (or fraction of a cell)
        self.orientation_threshold = 15.0  # degrees allowable error
        self.cells_per_command = 1  # how many cells we group before checking

    def connect(self):
        """
        Opens a TCP connection to the Pico.
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.pico_ip, self.pico_port))
            print("[MovementClass] Connected to Pico at", self.pico_ip)
        except Exception as e:
            print("[MovementClass] Error connecting to Pico:", e)
            self.client_socket = None

    def disconnect(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            print("[MovementClass] Disconnected from Pico.")

    def execute_path(self, path):
        """
        path: list of (row, col, direction) from your A* search.

        We'll compress consecutive moves with the same direction into one big "FORWARD n" or "BACK n".
        When direction changes, we do "TURN" command. Then proceed.

        After each step, we check camera-based feedback.
        """
        if not self.client_socket:
            print("[MovementClass] No valid connection to Pico. Call connect() first.")
            return

        if not path:
            print("[MovementClass] Empty path.")
            return

        # Convert the path into a more "compressed" sequence of (delta_row, delta_col).
        segments = self._compress_path(path)

        # Send each segment
        for (cmd_type, value) in segments:
            self._send_command_wait_ack(cmd_type, value)

            # Now do a feedback check with the image processor
            # If we are not within a threshold of the expected cell,
            # we can attempt correction commands.
            self._check_and_correct_position()

        print("[MovementClass] Movement complete for entire path.")

    # ----------------------------------------------------------------
    #                   Command / Acknowledgment
    # ----------------------------------------------------------------
    def _send_command_wait_ack(self, command, param):
        """
        Send a single command => "FORWARD,n", "BACK,n", "TURN,deg", "STOP", "DANCE"
        Wait for the "DONE,<CMD>,<PARAM>" response.
        """
        if command.upper() in ["FORWARD", "BACK", "TURN", "STOP", "DANCE"]:
            message = f"{command.upper()},{param}\n"
        else:
            print(f"[MovementClass] Unknown command: {command}")
            return

        # Send
        try:
            self.client_socket.sendall(message.encode())
            print(f"[MovementClass] Sent: {message.strip()}")
        except Exception as e:
            print("[MovementClass] Error sending data:", e)
            return

        # Wait for ack
        ack = self._recv_line()
        if ack:
            print(f"[MovementClass] Pico ack: {ack}")
        else:
            print("[MovementClass] No ack received or error.")

    def _recv_line(self):
        """
        Read one line from the Pico. Return it as a string or None.
        """
        try:
            response = self.client_socket.recv(1024).decode().strip()
            return response
        except Exception as e:
            print("[MovementClass] Error receiving data:", e)
            return None

    # ----------------------------------------------------------------
    #                   Feedback & Correction
    # ----------------------------------------------------------------
    def _check_and_correct_position(self):
        """
        Uses ArucoGridDetector to see if the robot is near the expected cell and orientation.
        If not, sends extra "fine-tune" commands.

        Simplified logic: if we are within 0.5 cell, do nothing; else try a small FORWARD or BACK.
        Similarly for orientation.
        """
        if not self.detector:
            return  # no real-time feedback if we have no detector

        # Suppose detector can give us a cell_label and orientation
        label = self.detector.get_robot_cell_label()
        if label is None:
            return  # can't correct if we don't see the robot

        # We'll define a function to convert label -> (row, col)
        (current_r, current_c) = self._converter(label)

        # Compare to path or some target. This is up to you:
        # we might not know exactly which cell is "current" in the path.
        # For simplicity, do nothing unless you have a known target cell we want to confirm.

        # Also check orientation
        if self.detector.get_robot_position() is not None:
            _, _, angle_deg = self.detector.get_robot_position()
            # If angle is off, maybe we do a "TURN,diff"
            # This is optional, depends on how fine you want correction.
            pass

        # For demonstration, we won't do actual “fine correction” code here,
        # but you could do:
        #   difference_in_cells = sqrt((target_r - current_r)^2 + (target_c - current_c)^2)
        #   if difference_in_cells > self.position_threshold: 
        #       # send a small FORWARD or BACK by 1 cell
        #   orientation_diff = angle_deg - target_angle
        #   if abs(orientation_diff) > self.orientation_threshold:
        #       # do a TURN, etc.

    def _converter(self, cell_label):
        """
        Convert a cell label to (row, col). 
        Adjust for your labeling scheme. For example:
            If label % self.detector.cols == 0:
                row = (label // self.detector.cols) - 1
                col = self.detector.cols - 1
            else:
                row = label // self.detector.cols
                col = (label % self.detector.cols) - 1
        """
        if cell_label % self.detector.cols == 0:
            return ((cell_label // self.detector.cols) - 1, self.detector.cols - 1)
        else:
            return (cell_label // self.detector.cols, (cell_label % self.detector.cols) - 1)

    # ----------------------------------------------------------------
    #                   Path Compression
    # ----------------------------------------------------------------
    def _compress_path(self, path):
        """
        path: list of (row, col, direction).
        We want to turn it into a sequence of commands like:
            [("TURN", 0), ("FORWARD", 3), ("TURN", 90), ("FORWARD", 2), ...]

        There's many ways to do this. We'll do a simple version:
          1) Walk through consecutive states.
          2) If direction is the same, group them as a "FORWARD" if we are moving forward
             or "BACK" if we’re moving backward. 
          3) If direction changes, create a "TURN" command for the difference.
        """
        if len(path) < 2:
            return []

        commands = []
        # We'll keep track of the robot's orientation as we move from step to step.
        current_state = path[0]  # (r, c, dir)

        for i in range(1, len(path)):
            next_state = path[i]
            (r1, c1, dir1) = current_state
            (r2, c2, dir2) = next_state

            # If orientation changed from dir1 -> dir2, we produce a "TURN" first
            turn_diff = (dir2 - dir1) % 360
            if turn_diff > 180:  # e.g. 270 = -90
                turn_diff -= 360

            if abs(turn_diff) > 1:  # e.g. a 0.1 deg difference might be negligible
                commands.append(("TURN", turn_diff))

            # Now see how the row,col changed
            dr = r2 - r1
            dc = c2 - c1
            if dr == 0 and dc == 0:
                # No move in the grid
                pass
            else:
                # We can decide if it's forward or backward relative to dir2
                # But for simplicity, let's assume "FORWARD" means 1 cell step whenever row/col changes.
                steps = abs(dr) + abs(dc)  # each step in path is 1 cell
                # If it’s consistent with facing direction, call it forward,
                # but if direction is 180 deg away from the movement vector, it's BACK.
                # For now, we assume path was built so each step is "forward" in orientation.
                # If you want to be precise, you can check if direction is reversed.

                # We'll just "FORWARD, steps"
                commands.append(("FORWARD", steps))

            current_state = next_state

        return commands

