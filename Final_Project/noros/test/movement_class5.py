# movement_class3.py
import socket
import time
import math
import threading

class MovementClass:
    def __init__(self, pico_ip="192.168.106.106", pico_port=12346, detector=None):
        self.pico_ip = pico_ip
        self.pico_port = pico_port
        self.client_socket = None
        self.detector = detector  

        self.position_threshold = 10 
        self.orientation_threshold = 5  # Degrees
        self.cells_per_command = 1  

        # Initialize expected_angle to None; it will be set based on the path
        self.expected_angle = None
        self.current_step_index = 0

        # Define steps_per_cell (encoder steps corresponding to one full cell move)
        self.steps_per_cell = 51

        self.socket_lock = threading.Lock()

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.pico_ip, self.pico_port))
            print("[MovementClass] Connected to Pico at", self.pico_ip)

            initial_msg = self._recv_line()
            if initial_msg:
                print(f"[MovementClass] Initial Pico message: {initial_msg}")
            else:
                print("[MovementClass] No initial message received from Pico.")

        except Exception as e:
            print("[MovementClass] Error connecting to Pico:", e)
            self.client_socket = None

    def disconnect(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            print("[MovementClass] Disconnected from Pico.")

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

        # Reset current step index
        self.current_step_index = 0

        for (cmd_type, value) in segments:
            if cmd_type.upper() == "TURN":
                # Update expected_angle based on the TURN command from the path
                self.expected_angle = (self.expected_angle + value) % 360
                print(f"[MovementClass] Updated expected angle to {self.expected_angle} degrees after TURN command.")

                success = self._send_command_wait_ack(cmd_type, value)
                if not success:
                    print(f"[MovementClass] Command failed: {cmd_type} {value}")
                    break

                # After each command, perform continuous angle corrections
                self._continuous_angle_correction()

            elif cmd_type.upper() == "FORWARD":
                for _ in range(value):
                    self.current_step_index += 1

                    if self.current_step_index < len(path):
                        expected_cell = path[self.current_step_index]
                        expected_position = self.detector.cell_centers.get(
                            (expected_cell[0], expected_cell[1]), (None, None)
                        )
                        if expected_position == (None, None):
                            print(f"[MovementClass] Expected cell center not found for cell {expected_cell}")
                            continue
                        expected_x, expected_y = expected_position
                    else:
                        print("[MovementClass] Reached end of path.")
                        expected_x, expected_y = None, None

                    # Send main FORWARD command for a single cell movement
                    success = self._send_command_wait_ack("FORWARD", 1)
                    if not success:
                        print("[MovementClass] Failed to send FORWARD,1 command.")
                        break

                    # Perform continuous angle corrections
                    self._continuous_angle_correction()

                    # Perform continuous position corrections using the new "CORRECTION" message
                    if expected_x is not None and expected_y is not None:
                        self._continuous_position_correction(expected_x, expected_y)

    def _send_command_wait_ack(self, command, param):
        valid_commands = ["FORWARD", "BACK", "TURN", "STOP", "DANCE", "CORRECTION"]
        if command.upper() not in valid_commands:
            print(f"[MovementClass] Invalid command type: {command}")
            return False

        message = f"{command.upper()},{param}\n"

        with self.socket_lock: 
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

    def _continuous_angle_correction(self):
        """
        Continuously checks and corrects the robot's orientation until the angle error
        is within the specified threshold.
        """
        while True:
            if not self.detector:
                print("[MovementClass] No detector available for position correction.")
                break

            position = self.detector.get_robot_position()
            if position is None:
                print("[MovementClass] Unable to get robot position for correction.")
                break

            _, _, angle_deg = position  
            angle_diff = self._calculate_angle_difference(angle_deg, self.expected_angle)
            print(f"[MovementClass] Current angle: {angle_deg}°, Expected angle: {self.expected_angle}°, Difference: {angle_diff}°")

            if abs(angle_diff) <= self.orientation_threshold:
                print("[MovementClass] Angle within threshold. No correction needed.")
                break  # Angle is within the acceptable threshold

            # Determine the correction angle (limit to 5 degrees per correction step)
            correction_deg = min(abs(angle_diff), 5)
            correction_deg = correction_deg if angle_diff < 0 else -correction_deg
            print(f"[MovementClass] Applying correction: {correction_deg} degrees")

            # Send the correction command
            success = self._send_command_wait_ack("TURN", correction_deg)
            if not success:
                print("[MovementClass] Failed to apply correction.")
                break  # Exit the loop if correction command fails

            # Update the expected angle based on the correction
            #self.expected_angle = (self.expected_angle + correction_deg) % 360
            #print(f"[MovementClass] Updated expected angle to {self.expected_angle} degrees after correction.")

            # Small delay to allow the robot to process the correction
            time.sleep(0.5)

    def _continuous_position_correction(self, expected_x, expected_y):
        """
        Continuously checks and corrects the robot's position along the axis corresponding
        to the expected angle until the position error is within the specified threshold.
        Instead of sending corrections in full-cell units, this sends a separate "CORRECTION"
        message with the number of encoder steps to correct.
        
        Args:
            expected_x (float): The expected x-coordinate of the robot's position.
            expected_y (float): The expected y-coordinate of the robot's position.
        """
        # conversion_factor converts a distance (in detector units) to encoder steps.
        # We assume detector.cell_size is the cell’s size (in the same units as expected_x/current_x).
        conversion_factor = 51 / 135
        while True:
            if not self.detector:
                print("[MovementClass] No detector available for position correction.")
                break

            position = self.detector.get_robot_position()
            if position is None:
                print("[MovementClass] Unable to get robot position for correction.")
                break

            current_x, current_y, _ = position

            # Determine the axis and direction to correct based on expected_angle:
            if self.expected_angle == 0:
                # For angle 0, we correct based on x+SHIFT: if current_x is less than expected_x, move forward.
                diff = expected_x - current_x
                if diff > self.position_threshold:
                    direction = "BACK"
                elif diff < -self.position_threshold:
                    direction = "FORWARD"
                else:
                    print("[MovementClass] X position within threshold.")
                    break

            elif self.expected_angle == 180:
                # For angle 180, correct with respect to x-SHIFT.
                diff = current_x - expected_x
                if diff > self.position_threshold:
                    direction = "FORWARD"
                elif diff < -self.position_threshold:
                    direction = "BACK"
                else:
                    print("[MovementClass] X position within threshold.")
                    break

            elif self.expected_angle == 90:
                # For angle 90, correct with respect to y-SHIFT.
                diff = expected_y - current_y
                if diff > self.position_threshold:
                    direction = "Forward"
                elif diff < -self.position_threshold:
                    direction = "BACK"
                else:
                    print("[MovementClass] Y position within threshold.")
                    break

            elif self.expected_angle == 270:
                # For angle 270, correct with respect to y+SHIFT.
                diff = current_y - expected_y
                if diff > self.position_threshold:
                    direction = "BACK"
                elif diff < -self.position_threshold:
                    direction = "FORWARD"
                else:
                    print("[MovementClass] Y position within threshold.")
                    break

            else:
                print(f"[MovementClass] Unexpected angle: {self.expected_angle} degrees.")
                break

            # Compute the number of encoder steps to move based on the distance error
            correction_steps = max(5, int(round(abs(diff) * conversion_factor)))
            # Send a new message type "CORRECTION" along with direction and number of steps.
            correction_param = f"{direction},{correction_steps}"
            print(f"[MovementClass] Applying position correction: CORRECTION,{correction_param} (diff = {diff})")
            success = self._send_command_wait_ack("CORRECTION", correction_param)
            if not success:
                print(f"[MovementClass] Failed to apply position correction: CORRECTION,{correction_param}")
                break

            # Small delay to allow the robot to move before re-checking
            time.sleep(0.5)

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

            '''
            else:
                # Calculate the number of steps based on cells_per_command
                distance = math.hypot(dr, dc)
                steps = max(int(distance / self.cells_per_command), 1)
                for _ in range(steps):
                    commands.append(("FORWARD", 1))
                print(f"[MovementClass] Added FORWARD command with {steps} steps.")
            '''

            current_state = next_state

        return commands

    def _calculate_angle_difference(self, actual_angle, expected_angle):
        """
        Calculates the smallest difference between two angles.
        Result is in the range [-180, 180].
        """
        diff = (actual_angle - expected_angle + 180) % 360 - 180
        return diff

    def send_status_message(self, message):
        """
        Sends a status message to the Pico and waits for the acknowledgment "Taken".
        """
        if not self.client_socket:
            print("[MovementClass] Not connected to Pico. Cannot send status message.")
            return False

        with self.socket_lock:
            try:
                # Send the status message
                self.client_socket.sendall(f"STATUS,{message}\n".encode())
                print(f"[MovementClass] Sent status message: {message}")

                # Set a timeout for the acknowledgment response
                self.client_socket.settimeout(5.0)

                # Wait for acknowledgment
                ack = self.client_socket.recv(1024).decode().strip()
                if ack == "Taken":
                    print(f"[MovementClass] Status message '{message}' acknowledged by Pico.")
                    return True
                else:
                    print(f"[MovementClass] Unexpected acknowledgment: {ack}")
                    return False

            except socket.timeout:
                print("[MovementClass] Status message acknowledgment timed out.")
                return False
            except Exception as e:
                print(f"[MovementClass] Error sending status message: {e}")
                return False
            finally:
                # Reset timeout to None for regular operations
                self.client_socket.settimeout(None)

