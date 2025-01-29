# movement_class.py

import socket
import time

class MovementClass:
    """
    Takes a path of grid cells and sends 
    'FRONT', 'BACK', 'LEFT', 'RIGHT' commands to the Pico.
    """

    def __init__(self, pico_ip="192.168.4.1", pico_port=8080):
        self.pico_ip = pico_ip
        self.pico_port = pico_port
        self.client_socket = None

    def connect(self):
        """
        Opens a TCP connection to the Pico.
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.pico_ip, self.pico_port))
            print("Connected to Pico at", self.pico_ip)
        except Exception as e:
            print("Error connecting to Pico:", e)
            self.client_socket = None

    def disconnect(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            print("Disconnected from Pico.")

    def execute_path(self, path):
        """
        For each adjacent pair of cells in the path,
        determine the movement direction, then send to Pico.
        """
        if not self.client_socket:
            print("No valid connection to Pico. Call connect() first.")
            return

        # path like [(0,0), (0,1), (0,2), ...]
        for i in range(len(path) - 1):
            current = path[i]
            nxt = path[i + 1]
            command = self._step_to_command(current, nxt)
            if command:
                self._send_command(command)
                # Optional: wait for an acknowledgment or a short delay
                time.sleep(0.5)

    def _step_to_command(self, current, nxt):
        (r1, c1) = current
        (r2, c2) = nxt
        dr = r2 - r1
        dc = c2 - c1

        # Negative row difference => FRONT
        if dr == -1 and dc == 0:
            return "FRONT"
        # Positive row difference => BACK
        elif dr == 1 and dc == 0:
            return "BACK"
        # Positive col difference => RIGHT
        elif dr == 0 and dc == 1:
            return "RIGHT"
        # Negative col difference => LEFT
        elif dr == 0 and dc == -1:
            return "LEFT"
        else:
            return None

    def _send_command(self, command):
        """
        Sends the command to the Pico. Optionally reads a response.
        """
        try:
            message = command + "\n"
            self.client_socket.sendall(message.encode())
            print("Sent command:", command)

            # If Pico code sends an acknowledgment:
            response = self.client_socket.recv(1024).decode().strip()
            print("Response from Pico:", response)

        except Exception as e:
            print("Error sending data:", e)

