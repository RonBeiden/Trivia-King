# Import necessary modules
import socket
import time
import sys
from threading import Thread, Lock
import threading
import struct
from inputimeout import inputimeout, TimeoutOccurred


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SERVER_UDP_PORT = 13117
        self.MAGIC_COOKIE = 0xABCDDCBA
        self.OFFER_MESSAGE_TYPE = 0x2
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'reset': '\033[0m'
        }

    def get_offer_from_server(self):
        print(f"Client started, listening for UDP messages.... on {self.SERVER_UDP_PORT}")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.bind(("", self.SERVER_UDP_PORT))
            try:
                while True:
                    print("Waiting for message...")
                    data, addr = udp_socket.recvfrom(1024)
                    print("Received")
                    magic_cookie, message_type, server_name, tcp_port = struct.unpack(
                        "!Ib32sH", data
                    )
                    server_name = server_name.decode().strip("\x00")
                    #server_name = ''.join(char for char in server_name if char != ' ')
                    if magic_cookie == self.MAGIC_COOKIE and message_type == self.OFFER_MESSAGE_TYPE:
                        server_ip = addr[0]
                        print(
                            f'Received offer from server "{server_name}" at address {server_ip}, attempting to connect...'
                        )
                        print(f'server_ip: {server_ip} , tcp_port: {tcp_port}')
                        return server_ip, tcp_port
            except OSError:
                pass

    def send_player_name(self, player_name):
        self.client_socket.sendall(player_name.encode("utf-8") + b'\n')

    def receive_game_start_message(self):
        try:
            game_start_message = self.client_socket.recv(1024).decode("utf-8")
            print(game_start_message)
        except Exception:
            pass

    def print_color(self, color, message):
        # Check if the specified color exists, otherwise default to white
        color_code = self.colors.get(color, self.colors['white'])
        # Send the colored message to the player
        print(color_code + message + self.colors['reset'], end="")

    def receive_message_from_server(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if message:
                    if message.startswith("You lose"):
                        self.print_color("red", message)
                    elif message.startswith("Game over!\nCongratulations to the winner"):
                        self.print_color("green", message)
                    elif message.startswith("Game Statistics:"):
                        self.print_color("yellow", message)
                    elif message.startswith("Welcome to the game!"):
                        self.print_color("magenta", message)
                    else:
                        print(message, end="")
                return message
            except (ConnectionResetError, socket.timeout) as error:
                if isinstance(error, ConnectionResetError):
                    print("Connection reset by peer.")
                    self.disconnect()
                elif isinstance(error, socket.timeout):
                    continue

    def send_key_press_to_server(self, key):
        self.client_socket.sendall(key.encode("utf-8"))

    def send_answer_to_server(self, answer):
        self.client_socket.send(answer.encode("utf-8"))

    def disconnect(self):  # disconnect and rerun
        self.client_socket.close()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket.close()
        print('Server disconnected, listening for offer requests....')
        self.start_client()

    def input(self, enter_input):
        answer = None
        try:
            answer = inputimeout(prompt=enter_input, timeout=10)
        except TimeoutOccurred:
            pass
        return answer

    def start_client(self):
        server_ip, tcp_port = self.get_offer_from_server()
        print("Connecting using TCP to server IP:", server_ip)
        self.client_socket.connect((server_ip, tcp_port))
        self.send_bot_name()

        self.client_socket.settimeout(1)
        self.receive_game_start_message()

        # Wait for the server to assign a name to the client
        player_name = self.receive_message_from_server()
        if player_name.startswith("You are the only player connected. Waiting for more players."):
            print(player_name)
            self.disconnect()

        # Handle the case where the server sends a "No names available" message
        if player_name == "No names available.":
            print(player_name)
            self.disconnect()

        # Loop for receiving questions and sending answers
        while True:
            response = self.receive_message_from_server()
            if response.startswith("=="):
                enter_input = "Enter your answer (Y/T/1 for True, N/F/0 for False): "
                # print(response)  # Print the question
                answer = self.input(enter_input)
                if answer:
                    answer = answer.strip().lower()
                    self.send_answer_to_server(answer)
                else:
                    print("\n")
            elif response.startswith("You lose"):
                continue
            elif response.startswith("Game over!"):
                self.disconnect()
                break
            else:
                continue  # Print other messages from the server

        print("Game over!")

    def send_bot_name(self):
        self.send_player_name("")


def main():
    client = Client("127.0.0.1", 12345)
    client.start_client()


if __name__ == "__main__":
    main()
