import socket
import threading
import sys

# Global variables
UDP_PORT = 13117
MAGIC_COOKIE = b'\xab\xcd\xdc\xba'


def receive_offer_messages():
    """Receive offer messages via UDP."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Use SO_REUSEADDR
        udp_socket.bind(('0.0.0.0', UDP_PORT))
        while True:
            data, _ = udp_socket.recvfrom(1024)
            if data.startswith(MAGIC_COOKIE) and data[4] == 0x02:
                server_name = data[5:37].decode().strip()
                server_port = int.from_bytes(data[37:39], byteorder='big')
                print(f"Received offer from server '{server_name}' at address 0.0.0.0:{server_port}, attempting to connect...")
                connect_to_server(server_port)


def connect_to_server(port):
    """Connect to the server via TCP."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        try:
            tcp_socket.connect(('0.0.0.0', port))
            team_name = "Alice"  # Hardcoded for now, should be user input
            tcp_socket.sendall(team_name.encode() + b'\n')
            print(f"Connected to server at 0.0.0.0:{port}")
            receive_messages(tcp_socket)
        except ConnectionRefusedError:
            print("Connection to server failed. Retrying...")


def receive_messages(tcp_socket):
    """Receive and display messages from the server."""
    while True:
        data = tcp_socket.recv(1024).decode().strip()
        if not data:
            break
        print(data)


def start_client():
    """Start the client."""
    udp_thread = threading.Thread(target=receive_offer_messages, daemon=True)
    udp_thread.start()


if __name__ == "__main__":
    start_client()
