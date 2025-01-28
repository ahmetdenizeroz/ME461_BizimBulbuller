# pico_comm.py
import socket

class PicoComm:
    def __init__(self, ip="192.168.66.106", port=8080):
        self.ip = ip
        self.port = port
        self.client = None

    def connect(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.ip, self.port))
            print("Connected to Pico successfully!")
            return True
        except Exception as e:
            print(f"Error connecting to Pico: {e}")
            self.client = None
            return False

    def send_command(self, cmd):
        """Send a string command to the Pico."""
        if self.client:
            try:
                self.client.sendall(cmd.encode())
            except Exception as e:
                print(f"Error sending command: {e}")
        else:
            print("No Pico connection available.")

    def receive_response(self):
        """Receive data from Pico."""
        if self.client:
            try:
                data = self.client.recv(1024).decode().strip()
                return data
            except Exception as e:
                print(f"Error receiving response: {e}")
        return None

    def close(self):
        if self.client:
            self.client.close()
            self.client = None

