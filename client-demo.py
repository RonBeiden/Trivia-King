# Import necessary modules
import socket
import time
import sys
from threading import Thread

player_names = ["Arya Stark", "Walter White", "Rick Grimes"]
player_names_copy = player_names.copy()

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        try:
            print("Client started, listening for offer requests....")
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"Received offer from server Mystic at address {self.host}, attempting to connect...")

        except ConnectionRefusedError:
            sys.exit()

    def send_player_name(self, player_name):
        self.client_socket.sendall(player_name.encode("utf-8") + b'\n')

    def receive_game_start_message(self):
        game_start_message = self.client_socket.recv(1024).decode("utf-8")
        print(game_start_message)

    def receive_message_from_server(self):
        message = self.client_socket.recv(1024).decode("utf-8")
        return message

    def send_key_press_to_server(self, key):
        self.client_socket.sendall(key.encode("utf-8"))

    def send_answer_to_server(self, answer):
        self.client_socket.sendall(answer.encode("utf-8"))

    def disconnect(self):
        self.client_socket.close()


def start_client(client):
    global player_names_copy

    client.connect_to_server()
    # Enter player name
    player_name = player_names_copy.pop(0)
    client.send_player_name(player_name)
    # Wait for game start message
    client.receive_game_start_message()


def main():
    global player_names_copy

    client = Client("localhost", 12345)
    receive_thread = Thread(target=start_client(client))
    receive_thread.start()
    while True:
        response = client.receive_message_from_server()
        if response.startswith("=="):
            print(response)  # Print the question
            answer = input("Enter your answer (Y/T/1 for True, N/F/0 for False): ").strip().lower()
            client.send_answer_to_server(answer)
        elif response.startswith("Game over!"):
            print("Server disconnected, listening for offer requests...")
            client.disconnect()
            # time.sleep(1)
            player_names_copy = player_names.copy()
            receive_thread = Thread(target=start_client(client))
            receive_thread.start()
        else:
            print(response)  # Print other messages from the server


if __name__ == "__main__":
    main()
