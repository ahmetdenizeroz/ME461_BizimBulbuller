import socket
import threading

HOST = '0.0.0.0'
PORT = 8080

def handle_client(conn):
    print("Client connected")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
                
            msg = data.decode().strip()
            print(f"Received: {msg}")
            
            # Immediate response
            if msg in ["PICO_HELLO", "PICO_PULSE"]:
                response = b"SERVER_ACK\n"
                print(f"Sending: {response.decode().strip()}")
                conn.sendall(response)
                
    except ConnectionResetError:
        print("Client disconnected")
    finally:
        conn.close()
    print("Connection closed")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()
            print(f"New connection from {addr[0]}")
            threading.Thread(target=handle_client, args=(conn,)).start()

if __name__ == "__main__":
    start_server()
