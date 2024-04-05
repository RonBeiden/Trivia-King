import socket
import time
import random
from threading import Timer, Thread
import threading
import struct
import select
UDP_PORT = 13117
TCP_PORT = 12345
MAGIC_COOKIE = 0xABCDDCBA
OFFER_MESSAGE_TYPE = 0x2
SERVER_NAME = "Mystic"
BROADCAST_INTERVAL = 1
GAME_START_DELAY = 15
GAME_DURATION = 15
class Server:
    def __init__(self, host, port):
        self.UDP_PORT = 13117
        self.TCP_PORT = 12345
        self.MAGIC_COOKIE = 0xABCDDCBA
        self.OFFER_MESSAGE_TYPE = 0x2
        self.SERVER_NAME = "Mystic"
        self.BROADCAST_INTERVAL = 1
        # self.GAME_START_DELAY = 15
        # self.GAME_DURATION = 15
        self.host = host
        self.port = port
        self.addresses = {}
        self.players = []
        self.player_answers = {}
        self.real_answers = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.server_udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.state = False  # Initial state is waiting
        self.timer = None  # Timer for state transition
        self.questions = {
            "Aston Villa's current manager is Pep Guardiola": False,
            "Aston Villa's mascot is a lion named Hercules": True,
            # Add more questions here
        }
        self.threads = []
        self.round = 0
        self.winners = []
        self.curr_winner = None
        self.lock = threading.Lock()
        self.player_names = ["Arya Stark", "Walter White", "Rick Grimes"]
        self.client_count = 0

    def start_init(self):
        self.players = []
        self.player_answers = {}
        self.state = False
        self.round = 0
        self.curr_winner = None

    def start(self):
        self.start_init()
        self.server_socket.bind(("", self.port))
        self.server_socket.listen()
        print("Server started, listening on Port", self.port)

    def send_offer_announcements(self):
        broadcast_address = (self.host, self.port)  # Broadcast address and port
        # offer_msg = f"offer from server {self.name} at address {self.host}:{self.port}"
        message = struct.pack(
                        "!Ib32sH",
                        MAGIC_COOKIE,
                        OFFER_MESSAGE_TYPE,
                        SERVER_NAME.encode().ljust(32),
                        TCP_PORT,
                    )
        # Create UDP socket
        print("Server broadcasting offers on UDP port", UDP_PORT)

        while not self.state:
                self.server_udp_socket.sendto(message, ("<broadcast>", UDP_PORT))
                time.sleep(BROADCAST_INTERVAL)
                print("Broadcast sent")
        print("======== Server broadcast Ended ==========")

    # def accept_clients(tcp_socket):
    #     global clients, game_in_progress
    #     tcp_socket.settimeout(GAME_START_DELAY)
    #     while not game_in_progress:
    #         try:
    #             client_socket, addr = tcp_socket.accept()
    #             client_name = client_socket.recv(1024).decode().strip()
    #             clients.append((client_name, client_socket))
    #             print(f"Accepted connection from {client_name}")
    #             threading.Thread(
    #                 target=handle_client, args=(client_socket, client_name)
    #             ).start()
    #         except socket.timeout:
    #             print("Accepting clients timed out")
    #             break
    def accept_players(self):
        print("Accepting players")
        self.server_socket.settimeout(10)  # Set socket timeout to 10 seconds
        start_time = time.time()  # Record the start time

        while True:
            if time.time() - start_time > 10 or len(self.players) == len(self.player_names):
                break  # Break out of the loop if 10 seconds have passed

            try:
                client_socket, addr = self.server_socket.accept()
                print("Client connected", addr)
                start_time = time.time()  # Reset the start time whenever a new player connects
                # print("Reset Timer because new player connected")
            except socket.timeout:
                continue  # Continue waiting if no new connections

            self.addresses[client_socket] = addr
            thr = Thread(target=self.handle_client, args=(client_socket,))
            self.threads.append(thr)
            thr.start()
            time.sleep(.1)

        ## Two Player or more have joined , can start the game
        self.state = True
        self.server_socket.settimeout(None)  # Reset sock

        # print("joining")
        for t in self.threads:
            t.join()
        time.sleep(1)
        # Check if no players joined within 10 seconds
        if not self.players:
            print("No players joined within 10 seconds. Restarting game...")
            self.rerun_server()
        if(len(self.players) == 1):
            print('Only one Player joined , Not enough to start game , Restarting')
            self.rerun_server()
        ### Starting Game
        self.start_game()

    # def handle_client(self, client_socket):
    #     player_name = client_socket.recv(1024).decode("utf-8")
    #     player_name = player_name[:-1]
    #     self.players.append((player_name, client_socket))
    #     print(f"Player {player_name} connected.")
    #     if self.state == "waiting":
    #         self.reset_timer()  # Reset the timer after a player joins
    #
    # def handle_client(self, client_socket):
    #     with self.lock:
    #         if self.client_count >= len(self.player_names):
    #             print("No names available.")
    #             client_socket.sendall(b"No names available. Connection terminated.")
    #             client_socket.close()
    #             return
    #         player_name = self.player_names[self.client_count]
    #         self.client_count += 1
    #
    #     player_name = player_name[:-1]  # Remove trailing newline character
    #     self.players.append((player_name, client_socket))
    #     print(f"Player {player_name} connected.")
    #
    #     if self.state == "waiting":
    #         self.reset_timer()  # Reset the timer after a player joins
    #
    #
    #
    #
    # def reset_timer(self):
    #     if self.timer is not None:
    #         self.timer.cancel()  # Cancel existing timer
    #     self.timer = Timer(10, self.start_game)  # Reset timer for 10 seconds
    #     self.timer.start()  # Start the timer
    #
    # def start_game(self):
    #     self.state = "game"  # Change state to game mode
    #     self.round += 1
    #     print(f"Starting round {self.round}...")
    #     player_names = [player[0] for player in self.players]
    #
    #     # Send welcome message with player names to all clients
    #     welcome_message = f"Welcome to the game! Players: {', '.join(player_names)}"
    #     self.send_message(welcome_message)
    #     # print(f"Trying to Send Question in round {self.round}...")
    #     self.send_question()

    def handle_client(self, client_socket):
        with self.lock:
            if self.client_count >= len(self.player_names):
                print("No names available.")
                client_socket.sendall(b"No names available. Connection terminated.")
                client_socket.close()
                return
            player_name = self.player_names[self.client_count]
            self.client_count += 1

        player_name = player_name[:-1]  # Remove trailing newline character
        self.players.append((player_name, client_socket))
        print(f"Player {player_name} connected.")


    def reset_timer(self):
        if self.timer is not None:
            self.timer.cancel()  # Cancel existing timer
        self.timer = Timer(10, self.start_game)  # Reset timer for 10 seconds
        self.timer.start()  # Start the timer

    def start_game(self):
        self.state = True  # Change state to game mode
        self.round += 1
        print(f"Starting round {self.round}...")
        player_names = [player[0] for player in self.players]

        # Send welcome message with player names to all clients
        welcome_message = f"Welcome to the game! Players: {', '.join(player_names)}"
        self.send_message(welcome_message)

        # Start the game logic
        # print("Sending Question to start game")
        time.sleep(1)
        self.send_question()

    def get_players_nums(self):
        p_num = 1
        p_message = []
        for p in self.players:
            p_message.append(f"Player {p_num}: {p[0]}\n")
            p_num += 1
        # p_message[-1] = p_message[-1][:-1]
        p_message = "".join(p_message)

        return p_message



    def send_message(self, message):
        for player in self.players:
            player[1].sendall(message.encode("utf-8"))

    def send_question(self):
        question, answer = random.choice(list(self.questions.items()))
        self.real_answers = {question:answer}
        p_message = self.get_players_nums()
        question_msg = "==\nTrue or false: {}\n".format(question)

        # Send question message to all players
        self.send_message(p_message)
        time.sleep(1)
        self.send_message(question_msg)
        self.receive_answers()

    def receive_answers(self):
        # print("Listening for answers...")
        self.player_answers = {}
        start_time = time.time()  # Record the start time
        while True:
            # Check if time limit (10 seconds) has been exceeded
            if time.time() - start_time > 10:
                break

            # Receive answers from players
            for player_name, player_socket in self.players:
                try:
                    # Set a timeout for receiving data
                    player_socket.settimeout(1)
                    data = player_socket.recv(1024).decode("utf-8").strip()
                    # print(f'Received answer: {data} from {player_name}')
                    # Reset the timeout after receiving data
                    player_socket.settimeout(None)
                    if data.lower() in ['y', 't', '1']:
                        response = True
                    elif data.lower() in ['n', 'f', '0']:
                        response = False
                    else:
                        response = -1

                    if response is True or response is False or response == -1:
                        self.player_answers[player_name] = response
                except socket.timeout:
                    # Timeout occurred, no data received
                    # print(f"Socket timed {socket.timeout}")
                    pass
                except socket.error:
                    # Error occurred while receiving data
                    # print(f'Socket error = {socket.error}')
                    pass

            # Check if all players have answered
            if len(self.player_answers) == len(self.players):
                self.process_answers()
                break

        print("10 Seconds have passed and Noone answered picking another question")
        self.send_question()

    def process_answers(self):
        first_question = next(iter(self.real_answers))
        correct_players = [player for player, response in self.player_answers.items() if response == self.real_answers[first_question]]
        if len(correct_players) == 1:
            # Only one player answered correctly, declare them as the winner
            winner = next(iter(correct_players))
            self.curr_winner = winner
            self.winners.append(winner)
            self.send_message(f"{winner} is correct! {winner} wins!")
            time.sleep(1)
            self.game_over()
        elif len(correct_players) > 1:
            # Multiple players answered correctly, continue the game for the next round
            print("Multiple players answered correctly. Continuing to the next round...")
            time.sleep(1)
            self.start_game()  # Start the next round
        else:
            # No players answered correctly, end the game
            print("No players answered correctly. Sending another Question.")
            self.send_question()

    def game_over(self):
        # Send summary message to all players
        summary_msg = f"Game over!\nCongratulations to the winner: {self.curr_winner}"
        self.send_message(summary_msg)
        time.sleep(1)
        print("Game over, Closing connections...")

        # Close all client connections
        for player in self.players:
            player[1].close()

        print("Connections closed, sending out offer requests...")
        self.rerun_server()

    def rerun_server(self):
        time.sleep(1)
        self.player_names = ["Arya Stark", "Walter White", "Rick Grimes"]
        print("Restarting server...")
        self.start_init()
        threading.Thread(target=self.send_offer_announcements, daemon=True).start()
        self.accept_players()

    def run_server(self):
        self.start()
        threading.Thread(target=self.send_offer_announcements, daemon=True).start()
        self.accept_players()


def main():
    server = Server("127.0.0.1", 12345)
    server.run_server()
# start (Intialize Server) -> send_offer_announcemts (Sends offer message on server) -> accept_players (recive clients as threads) ->for each client thread( handle_client -> reset_timer - > start game after 10 sec - > send_question -> recives answers-> process_answers -> start_game)

if __name__ == "__main__":
    main()
