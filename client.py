# Import necessary modules
import socket
import time
import sys
from threading import Thread, Lock
import threading
import struct
import signal
from inputimeout import inputimeout, TimeoutOccurred

player_names = ["Arya Stark", "Walter White", "Rick Grimes"]


# player_names_copy = player_names.copy()


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SERVER_UDP_PORT = 13117
        self.MAGIC_COOKIE = 0xABCDDCBA
        self.OFFER_MESSAGE_TYPE = 0x2

    # def connect_to_server(self):
    #     try:
    #         print("Client started, listening for offer requests....")
    #         self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         self.client_socket.connect((self.host, self.port))
    #         print("Waiting for offer from server...")
    #         offer_msg = self.client_socket.recv(1024).decode("utf-8")
    #         server_name = offer_msg.split(" ")[3]  # Extract server name from offer message
    #         print(f"Received offer from server {server_name} at address {self.host}, attempting to connect...")
    #     except ConnectionRefusedError:
    #         sys.exit()
    # def listen_for_offers():
    #     print("Client started, listening for offer requests...")
    #     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    #         udp_socket.bind(("", SERVER_UDP_PORT))
    #
    #         while True:
    #             data, address = udp_socket.recvfrom(1024)
    #             magic_cookie, message_type, server_name, tcp_port = struct.unpack(
    #                 "!Ib32sH", data
    #             )
    #             server_name = server_name.decode().strip("\x00")
    #
    #             if magic_cookie == MAGIC_COOKIE and message_type == OFFER_MESSAGE_TYPE:
    #                 server_ip = address[0]
    #                 print(
    #                     f'Received offer from server "{server_name}" at address {server_ip}, attempting to connect...'
    #                 )
    #                 return server_ip, tcp_port

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
                    server_name = ''.join(char for char in server_name if char != ' ')
                    if magic_cookie == self.MAGIC_COOKIE and message_type == self.OFFER_MESSAGE_TYPE:
                        server_ip = addr[0]
                        print(
                            f'Received offer from server "{server_name}" at address {server_ip}, attempting to connect...'
                        )
                        print(f'server_ip: {server_ip} , tcp_port: {tcp_port}')
                        return server_ip, tcp_port
            except OSError as e:
                print(f"Error: {e}")

    def send_player_name(self, player_name):
        self.client_socket.sendall(player_name.encode("utf-8") + b'\n')

    def receive_game_start_message(self):
        try:
            game_start_message = self.client_socket.recv(1024).decode("utf-8")
            print(game_start_message)
        except Exception as e:
            print(e)

    def receive_message_from_server(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if message:
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

    # def game_handler(self,server_ip,tcp_port):
    # with self.client_socket as tcp_socket:
    #     tcp_socket.connect(server_ip,tcp_port)
    #     Thread(target=self.receive_message_from_server).start()
    #     self.send_message_to_server()

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

        # print(f"Assigned name: {player_name}")

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
            elif response.startswith("Game over!"):
                self.disconnect()
                break
            else:
                continue  # Print other messages from the server

        print("Game over!")


def main():
    client = Client("127.0.0.1", 12345)
    client.start_client()


if __name__ == "__main__":
    main()
