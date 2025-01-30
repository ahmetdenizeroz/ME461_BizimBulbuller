# pico_side.py
import network
import socket
import time

SSID = "YourWiFi"
PASSWORD = "YourPassword"

# For demonstration, define each "cell" = X distance in motor steps, for instance.
STEPS_PER_CELL = 200  # you must tune this for your robot

def move_forward(n_cells):
    """
    Example function that uses encoders to move forward n_cells.
    In practice, you'd implement a loop reading encoders until enough steps are counted.
    """
    steps_target = n_cells * STEPS_PER_CELL
    print(f"[Pico] Moving forward {n_cells} cells = {steps_target} steps")
    # ... your motor code here ...
    time.sleep(2)  # placeholder

def move_backward(n_cells):
    steps_target = n_cells * STEPS_PER_CELL
    print(f"[Pico] Moving backward {n_cells} cells = {steps_target} steps")
    time.sleep(2)  # placeholder

def turn_degrees(deg):
    """
    Turn deg degrees. deg can be positive or negative.
    For 90 deg, turn right or left, etc.
    """
    print(f"[Pico] Turning {deg} degrees")
    time.sleep(1)  # placeholder

def stop_now():
    """
    Immediately stop all movement.
    """
    print("[Pico] Stopping now.")

def dance():
    """
    Perform some fun movement.
    """
    print("[Pico] Dancing!")
    time.sleep(3)

# ----- Wi-Fi Setup -----
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
print("Connecting to Wi-Fi...")
while not wlan.isconnected():
    time.sleep(1)
print("Connected! IP:", wlan.ifconfig()[0])

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("", 8080))
server_socket.listen(1)
print("[Pico] Waiting for PC connection...")

while True:
    conn, addr = server_socket.accept()
    print(f"[Pico] Connected to PC: {addr}")

    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            # e.g. "FORWARD,3"
            tokens = data.split(",")
            command = tokens[0].upper()

            if command == "FORWARD":
                n = int(tokens[1])
                move_forward(n)
                ack = f"DONE,FORWARD,{n}\n"
                conn.send(ack.encode())

            elif command == "BACK":
                n = int(tokens[1])
                move_backward(n)
                ack = f"DONE,BACK,{n}\n"
                conn.send(ack.encode())

            elif command == "TURN":
                deg = int(tokens[1])
                turn_degrees(deg)
                ack = f"DONE,TURN,{deg}\n"
                conn.send(ack.encode())

            elif command == "STOP":
                stop_now()
                ack = f"DONE,STOP,0\n"
                conn.send(ack.encode())

            elif command == "DANCE":
                dance()
                ack = f"DONE,DANCE,0\n"
                conn.send(ack.encode())

            else:
                # Unknown command
                print("[Pico] Unknown command:", data)
                # You could send an error message if you like.

    except Exception as e:
        print(f"[Pico] Socket error: {e}")

    conn.close()
    print("[Pico] PC disconnected.")

