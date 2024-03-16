import socket
import time
import random
from threading import Timer


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.players = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.timer = None

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Server started, listening on IP address", self.host)

    def send_offer_announcements(self):
        while True:
            offer_msg = "offer from server Mystic at address {}:{}".format(self.host, self.port)
            # Implement UDP broadcast to send offer announcements
            print("Sending offer announcement:", offer_msg)
            time.sleep(1)

    def accept_players(self):
        if self.timer is None:
            self.timer = Timer(10, self.start_game)  # Set initial timer
            self.timer.start()  # Start the initial timer

        while True:
            client_socket, addr = self.server_socket.accept()
            player_name = client_socket.recv(1024).decode("utf-8")
            self.players.append((player_name, client_socket))
            print("Player", player_name, "connected.")
            if len(self.players) == 3:  # Start game if 3 players have joined
                self.start_game()
            else:
                self.reset_timer()

    def reset_timer(self):
        if self.timer is not None:
            self.timer.cancel()  # Cancel existing timer
        self.timer = Timer(10, self.start_game)  # Reset timer for 10 seconds
        self.timer.start()  # Start the timer

    def start_game(self):
        welcome_msg = "Welcome to the Mystic server, where we are answering trivia questions about Aston Villa FC.\n"
        for idx, player in enumerate(self.players, start=1):
            welcome_msg += "Player {}: {}\n".format(idx, player[0])
        welcome_msg += "==\nTrue or false: Aston Villa's current manager is Pep Guardiola"
        # Send welcome message to all players
        for player in self.players:
            player[1].sendall(welcome_msg.encode("utf-8"))
            print("Sent message to player", player[0], ":", welcome_msg)
        # Start game logic


def main():
    server = Server("localhost", 12345)
    server.start()
    server.accept_players()


if __name__ == "__main__":
    main()
