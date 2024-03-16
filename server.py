import socket
import threading
import random
import time

# Global variables
UDP_PORT = 5000
TCP_PORT = 4040  # Will be assigned dynamically
MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
GAME_DURATION = 10  # Duration of each round in seconds

# Question pool
questions = [
    "Aston Villa's current manager is Pep Guardiola",
    "Aston Villa's mascot is a lion named Hercules"
]

# Clients dictionary to store active connections
clients = {}
lock = threading.Lock()


def send_offer_message():
    """Broadcast offer message via UDP."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Use SO_REUSEADDR
        udp_socket.bind(('0.0.0.0', UDP_PORT))
        while True:
            offer_message = MAGIC_COOKIE + b'\x02' + b'Mystic'.ljust(32) + \
                            TCP_PORT.to_bytes(2, byteorder='big')
            udp_socket.sendto(offer_message, ('<broadcast>', UDP_PORT))
            time.sleep(1)



def handle_client_connection(client_socket, address):
    """Handle client connection."""
    with client_socket:
        team_name = client_socket.recv(1024).decode().strip()
        print(f"New connection from {address}, Team: {team_name}")
        with lock:
            clients[address] = client_socket

        time.sleep(GAME_DURATION)  # Wait for other players to join

        # Send welcome message and start the game
        welcome_message = f"Welcome to the Mystic server, where we are answering trivia questions about Aston Villa FC.\n" \
                          f"Player 1: {team_name}\n"
        with lock:
            for idx, addr in enumerate(clients):
                welcome_message += f"Player {idx + 2}: {clients[addr].recv(1024).decode().strip()}\n"
        welcome_message += "==\n" + random.choice(questions)
        broadcast_message(welcome_message)

        # Wait for answers and handle game logic


def broadcast_message(message):
    """Broadcast message to all connected clients."""
    with lock:
        for client_socket in clients.values():
            client_socket.sendall(message.encode())


def start_server():
    """Start the server."""
    global TCP_PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.bind(('0.0.0.0', 0))  # Bind to any available port
        TCP_PORT = tcp_socket.getsockname()[1]
        tcp_socket.listen()

        # Start UDP offer message broadcasting thread
        udp_thread = threading.Thread(target=send_offer_message, daemon=True)
        udp_thread.start()

        print(f"Server started, listening on IP address 0.0.0.0:{TCP_PORT}")

        # Accept incoming connections
        while True:
            client_socket, address = tcp_socket.accept()
            client_thread = threading.Thread(target=handle_client_connection, args=(client_socket, address))
            client_thread.start()


if __name__ == "__main__":
    start_server()
