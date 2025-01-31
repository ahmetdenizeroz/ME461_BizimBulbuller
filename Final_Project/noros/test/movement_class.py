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
            # print("[MovementClass] Connected to Pico at", self.pico_ip)
        except Exception as e:
            # print("[MovementClass] Error connecting to Pico:", e)
            self.client_socket = None

    def disconnect(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            # print("[MovementClass] Disconnected from Pico.")

    def execute_path(self, path):
        """
        path: list of (row, col, direction) from your A* search.

        We'll compress consecutive moves with the same direction into one big "FORWARD n" or "BACK n".
        When direction changes, we do "TURN" command. Then proceed.

        After each step, we check camera-based feedback.
        """
        if not self.client_socket:
            # print("[MovementClass] No valid connection to Pico. Call connect() first.")
            return

        if not path:
            # print("[MovementClass] Empty path.")
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

        # print("[MovementClass] Movement complete for entire path.")

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
            # print(f"[MovementClass] Unknown command: {command}")
            return

        # Send
        try:
            self.client_socket.sendall(message.encode())
            # print(f"[MovementClass] Sent: {message.strip()}")
        except Exception as e:
            # print("[MovementClass] Error sending data:", e)
            return

        # Wait for ack
        ack = self._recv_line()
        if ack:
            # print(f"[MovementClass] Pico ack: {ack}")
            pass
        else:
            # print("[MovementClass] No ack received or error.")
            pass

    def _recv_line(self):
        """
        Read one line from the Pico. Return it as a string or None.
        """
        try:
            response = self.client_socket.recv(1024).decode().strip()
            return response
        except Exception as e:
            # print("[MovementClass] Error receiving data:", e)
            return None

    # ----------------------------------------------------------------
    #                   Feedback & Correction
    # ----------------------------------------------------------------
    def _check_and_correct_position(self):
        """
        Uses ArucoGridDetector to see if the robot is near the expected cell and orientation.
        If not, sends extra "fine-tune" commands.
        """
        if not self.detector:
            return

        label = self.detector.get_robot_cell_label()
        if label is None:
            return

        (current_r, current_c) = self._converter(label)

        if self.detector.get_robot_position() is not None:
            _, _, angle_deg = self.detector.get_robot_position()
            pass

    def _converter(self, cell_label):
        """
        Convert a cell label to (row, col). 
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
        Compresses a path list into movement commands.
        """
        if len(path) < 2:
            return []

        commands = []
        current_state = path[0]

        for i in range(1, len(path)):
            next_state = path[i]
            (r1, c1, dir1) = current_state
            (r2, c2, dir2) = next_state

            turn_diff = (dir2 - dir1) % 360
            if turn_diff > 180:
                turn_diff -= 360

            if abs(turn_diff) > 1:
                commands.append(("TURN", turn_diff))

            dr = r2 - r1
            dc = c2 - c1
            if dr == 0 and dc == 0:
                pass
            else:
                steps = abs(dr) + abs(dc)
                commands.append(("FORWARD", steps))

            current_state = next_state

        return commands

