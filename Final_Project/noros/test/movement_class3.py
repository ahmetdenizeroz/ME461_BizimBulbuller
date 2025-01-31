import socket
import time
import math

class MovementClass:
    def __init__(self, pico_ip="192.168.106.106", pico_port=12346, detector=None):
        self.pico_ip = pico_ip
        self.pico_port = pico_port
        self.client_socket = None
        self.detector = detector  

        self.position_threshold = 0.5  
        self.orientation_threshold = 15.0  
        self.cells_per_command = 1  

        # Initialize expected_angle to None; it will be set based on the path
        self.expected_angle = None  

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.pico_ip, self.pico_port))
            # print("[MovementClass] Connected to Pico at", self.pico_ip)

            initial_msg = self._recv_line()
            if initial_msg:
                pass  # print(f"[MovementClass] Initial Pico message: {initial_msg}")
            else:
                pass  # print("[MovementClass] No initial message received from Pico.")

        except Exception as e:
            pass  # print("[MovementClass] Error connecting to Pico:", e)
            self.client_socket = None

    def disconnect(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            # print("[MovementClass] Disconnected from Pico.")

    def execute_path(self, path):
        if not self.client_socket:
            print("[MovementClass] Not connected to Pico.")
            return

        if not path:
            print("[MovementClass] Path is empty.")
            return

        segments = self._compress_path(path)

        # Initialize expected_angle based on the first step's angle from the path
        if path:
            self.expected_angle = path[0][2]  # Extracting the angle from the first path step
            print(f"[MovementClass] Initial expected angle set to {self.expected_angle} degrees.")

        for (cmd_type, value) in segments:
            if cmd_type.upper() == "TURN":
                # Update expected_angle based on the TURN command from the path
                self.expected_angle = (self.expected_angle + value) % 360
                print(f"[MovementClass] Updated expected angle to {self.expected_angle} degrees after TURN command.")

            success = self._send_command_wait_ack(cmd_type, value)
            if not success:
                print(f"[MovementClass] Command failed: {cmd_type} {value}")
                break

            self._check_and_correct_position()

    def _send_command_wait_ack(self, command, param):
        if command.upper() in ["FORWARD", "BACK", "TURN", "STOP", "DANCE"]:
            message = f"{command.upper()},{param}\n"
        else:
            print(f"[MovementClass] Invalid command type: {command}")
            return False

        try:
            self.client_socket.sendall(message.encode())
            print(f"[MovementClass] Sent: {message.strip()}")
        except Exception as e:
            print(f"[MovementClass] Error sending command '{command}': {e}")
            return False

        self.client_socket.settimeout(5.0)
        try:
            ack = self.client_socket.recv(1024).decode().strip()
            print(f"[MovementClass] Received ack: {ack}")
            expected_ack = f"DONE,{command.upper()},{param}"
            if ack == expected_ack:
                return True
            else:
                print(f"[MovementClass] Unexpected ack. Expected: '{expected_ack}', Got: '{ack}'")
                return False
        except socket.timeout:
            print("[MovementClass] Ack timeout.")
            return False
        except Exception as e:
            print(f"[MovementClass] Error receiving ack for command '{command}': {e}")
            return False
        finally:
            self.client_socket.settimeout(None)

    def _recv_line(self):
        try:
            response = self.client_socket.recv(1024).decode().strip()
            return response
        except Exception as e:
            print(f"[MovementClass] Error receiving line: {e}")
            return None

    def _check_and_correct_position(self):
        if not self.detector:
            print("[MovementClass] No detector available for position correction.")
            return

        label = self.detector.get_robot_cell_label()
        if label is None:
            print("[MovementClass] Unable to get robot cell label.")
            return

        (current_r, current_c) = self._converter(label)
        print(f"[MovementClass] Current cell: ({current_r}, {current_c})")

        position = self.detector.get_robot_position()
        if position is not None:
            _, _, angle_deg = position  
            print(f"[MovementClass] Current orientation from detector: {angle_deg} degrees")
            angle_diff = self._calculate_angle_difference(angle_deg, self.expected_angle)
            print(f"[MovementClass] Angle difference: {angle_diff} degrees")

            while abs(angle_diff) > self.orientation_threshold:
                correction_deg = min(abs(angle_diff), 5)
                correction_deg = correction_deg if angle_diff > 0 else -correction_deg
                print(f"[MovementClass] Applying correction: {correction_deg} degrees")

                success = self._send_command_wait_ack("TURN", correction_deg)
                if success:
                    # Update expected_angle based on the correction
                    self.expected_angle = (self.expected_angle + correction_deg) % 360
                    print(f"[MovementClass] Expected angle updated to {self.expected_angle} degrees after correction.")
                else:
                    print("[MovementClass] Failed to apply correction.")
                print(angle_dif, "1")
                _, _, angle_deg = self.detector.get_robot_position()
                angle_diff = self._calculate_angle_difference(angle_deg, self.expected_angle)
                print(angle_dif, "2")

    def _converter(self, cell_label):
        if cell_label % self.detector.cols == 0:
            return ((cell_label // self.detector.cols) - 1, self.detector.cols - 1)
        else:
            return (cell_label // self.detector.cols, (cell_label % self.detector.cols) - 1)

    def _compress_path(self, path):
        if len(path) < 2:
            print("[MovementClass] Path too short to compress.")
            return []

        commands = []
        current_state = path[0]

        for i in range(1, len(path)):
            next_state = path[i]
            (r1, c1, dir1) = current_state
            (r2, c2, dir2) = next_state

            # Calculate the difference in direction based on path's angle
            turn_diff = (dir2 - dir1) % 360
            if turn_diff > 180:
                turn_diff -= 360

            if abs(turn_diff) > 1:
                commands.append(("TURN", turn_diff))
                print(f"[MovementClass] Added TURN command with {turn_diff} degrees.")

            dr = r2 - r1
            dc = c2 - c1
            if dr == 0 and dc == 0:
                print("[MovementClass] No movement required for this step.")
                pass
            else:
                # Calculate the number of steps based on cells_per_command
                distance = math.hypot(dr, dc)
                steps = max(int(distance / self.cells_per_command), 1)
                commands.append(("FORWARD", steps))
                print(f"[MovementClass] Added FORWARD command with {steps} steps.")

            current_state = next_state

        return commands

    def _calculate_angle_difference(self, actual_angle, expected_angle):
        """
        Calculates the smallest difference between two angles.
        Result is in the range [-180, 180].
        """
        diff = (actual_angle - expected_angle + 180) % 360 - 180
        return diff

