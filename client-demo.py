import socket
import time


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        self.client_socket.connect((self.host, self.port))
        print("Connected to server.")

    def send_player_name(self, player_name):
        self.client_socket.sendall(player_name.encode("utf-8") + b'\n')

    def receive_game_start_message(self):
        game_start_message = self.client_socket.recv(1024).decode("utf-8")
        print(game_start_message)

    def receive_message_from_server(self):
        message = self.client_socket.recv(1024).decode("utf-8")
        print("Received message from server:", message)

    def send_key_press_to_server(self, key):
        self.client_socket.sendall(key.encode("utf-8"))

    def disconnect(self):
        self.client_socket.close()


def main():
    client = Client("localhost", 12345)
    client.connect_to_server()

    # Prompt the user to enter their name
    player_name = input("Enter your name: ")
    client.send_player_name(player_name)

    # Wait for the game to start or additional players to join
    print("Waiting for the game to start or additional players to join...")
    time.sleep(10)

    # Receive the game start message
    client.receive_game_start_message()

    # Receive and print messages from the server
    while True:
        #client.receive_message_from_server()

        # Wait for user input and send it to the server
        key = input("Press any key to send to the server: ")
        client.send_key_press_to_server(key)
    client.disconnect()


if __name__ == "__main__":
    main()
