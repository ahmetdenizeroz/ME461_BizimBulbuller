# movement_class.py
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
            return

        if not path:
            return

        segments = self._compress_path(path)

        for (cmd_type, value) in segments:
            if cmd_type.upper() == "TURN":
                self.detector.set_expected_angle((self.detector.get_expected_angle() + value) % 360)
            success = self._send_command_wait_ack(cmd_type, value)
            if not success:
                break

            self._check_and_correct_position()

    def _send_command_wait_ack(self, command, param):
        if command.upper() in ["FORWARD", "BACK", "TURN", "STOP", "DANCE"]:
            message = f"{command.upper()},{param}\n"
        else:
            return False

        try:
            self.client_socket.sendall(message.encode())
            print(f"[MovementClass] Sent: {message.strip()}")
        except Exception as e:
            return False

        self.client_socket.settimeout(5.0)
        try:
            ack = self.client_socket.recv(1024).decode().strip()
            print(f"[MovementClass] Received ack: {ack}")
            expected_ack = f"DONE,{command.upper()},{param}"
            if ack == expected_ack:
                return True
            else:
                return False
        except socket.timeout:
            return False
        except Exception as e:
            return False
        finally:
            self.client_socket.settimeout(None)

    def _recv_line(self):
        try:
            response = self.client_socket.recv(1024).decode().strip()
            return response
        except Exception as e:
            return None

    def _check_and_correct_position(self):
        if not self.detector:
            return

        label = self.detector.get_robot_cell_label()
        if label is None:
            return

        (current_r, current_c) = self._converter(label)

        position = self.detector.get_robot_position()
        if position is not None:
            _, _, angle_deg = position  
            expected_angle = self.detector.get_expected_angle()
            print("1")
            angle_diff = (angle_deg - expected_angle + 180) % 360 - 270  
            print(angle_diff)
            if abs(angle_diff) > self.orientation_threshold:
                correction_deg = min(abs(angle_diff), 5)
                correction_deg = correction_deg if angle_diff > 0 else -correction_deg

                success = self._send_command_wait_ack("TURN", correction_deg)
                if success:
                    self.detector.set_expected_angle((expected_angle + correction_deg) % 360)

    def _converter(self, cell_label):
        if cell_label % self.detector.cols == 0:
            return ((cell_label // self.detector.cols) - 1, self.detector.cols - 1)
        else:
            return (cell_label // self.detector.cols, (cell_label % self.detector.cols) - 1)

    def _compress_path(self, path):
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

