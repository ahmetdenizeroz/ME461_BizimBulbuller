# server.py

import socket
import threading

# Server configuration
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 8080        # Port to listen on

# Direction Mapping for WASD keys
DIRECTION_MAP = {
    "w": "Forward",
    "a": "Left",
    "s": "Backward",
    "d": "Right",
    "x": "Stop"  # Added 'x' to stop the motors
}

# Global connection variable
conn = None
conn_lock = threading.Lock()

def handle_client_connection(client_socket, address):
    """
    Handles incoming client connections and receives data from the client.
    """
    global conn
    print(f"Connected by {address}")
    with conn_lock:
        conn = client_socket
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                print("Client disconnected.")
                break
            print(f"Received from Pico: {data.decode()}")
    except ConnectionResetError:
        print("Client disconnected abruptly.")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        with conn_lock:
            conn = None
        client_socket.close()

def send_commands():
    """
    Captures keyboard inputs from the terminal and sends corresponding commands to the Pico.
    """
    global conn
    print("Enter commands (w/a/s/d/x). Type 'q' to quit.")
    while True:
        try:
            cmd = input("Command (w/a/s/d/x): ").lower()
            if cmd == 'q':
                print("Shutting down command sender.")
                break
            if cmd in DIRECTION_MAP:
                direction = DIRECTION_MAP[cmd]
                with conn_lock:
                    if conn:
                        try:
                            message = f"MOVE:{direction}"
                            conn.sendall(message.encode())
                            print(f"Sent: ({cmd.upper()}, {direction})")
                        except Exception as e:
                            print(f"Failed to send: {e}")
                    else:
                        print("No client connected. Unable to send command.")
            else:
                print("Invalid command. Use 'w', 'a', 's', 'd', or 'x'.")
        except KeyboardInterrupt:
            print("\nExiting command sender.")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """
    Sets up the server, starts threads for handling client connections and sending commands.
    """
    global conn
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow address reuse to prevent "Address already in use" errors
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)  # Allow only one connection at a time
        print(f"Server listening on {HOST}:{PORT}")
    
        # Start the command sending thread
        cmd_thread = threading.Thread(target=send_commands, daemon=True)
        cmd_thread.start()
    
        while True:
            try:
                client_socket, address = server_socket.accept()
                client_handler = threading.Thread(
                    target=handle_client_connection,
                    args=(client_socket, address),
                    daemon=True
                )
                client_handler.start()
            except KeyboardInterrupt:
                print("\nServer shutting down.")
                break
            except Exception as e:
                print(f"Server error: {e}")
    
    finally:
        if conn:
            conn.close()
        server_socket.close()

if __name__ == "__main__":
    main()

