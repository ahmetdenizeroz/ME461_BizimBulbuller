import network
import socket
import time

SSID = "Seççavv"
PASSWORD = "yirh3223"

ROWS, COLS = 3, 4
current_position = [0, 0]

# Connect to Wi-Fi
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
print("Waiting for PC connection...")

while True:
    conn, addr = server_socket.accept()
    print(f"Connected to PC: {addr}")

    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            command, row, col = data.split(",")  
            row, col = int(row), int(col)

            if command == "MOVE":
                current_position = [row, col]  # Update position
                print(f"Moved to: {current_position}")
                conn.send(f"ARRIVED,{row},{col}\n".encode())

    except Exception as e:
        print(f"Error: {e}")

    conn.close()
    print("PC disconnected.")



