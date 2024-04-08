import socket
import time
import random
from threading import Timer, Thread
import threading
import struct

UDP_PORT = 13117
TCP_PORT = 12345
MAGIC_COOKIE = 0xABCDDCBA
OFFER_MESSAGE_TYPE = 0x2
SERVER_NAME = "Solidim"
BROADCAST_INTERVAL = 1
GAME_START_DELAY = 15
GAME_DURATION = 15


class Server:
    def __init__(self, host, port):
        self.UDP_PORT = 13117
        self.TCP_PORT = 12345
        self.MAGIC_COOKIE = 0xABCDDCBA
        self.OFFER_MESSAGE_TYPE = 0x2
        self.SERVER_NAME = SERVER_NAME
        self.BROADCAST_INTERVAL = 1
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
        self.player_name_bot = None
        self.questions = {
            "Cristiano Ronaldo has won the FIFA Ballon d'Or more than once.": True,
            "The fastest goal scored in a FIFA World Cup match was less than 10 seconds.": True,
            "Brazil has won the FIFA World Cup more times than any other country.": True,
            "Lionel Messi has never won an international trophy with Argentina.": False,
            "The English Premier League was founded in the 20th century.": False,
            "The 'Hand of God' goal was scored by Diego Maradona.": True,
            "Pele won three FIFA World Cup titles with Brazil.": True,
            "Zinedine Zidane headbutted Marco Materazzi in the 2006 FIFA World Cup final.": True,
            "The UEFA Champions League final is a single match played at a neutral venue.": True,
            "The term 'hat-trick' in football refers to scoring three goals in a single match.": True,
            "The offside rule in football was introduced in the 19th century.": False,
            "FIFA was founded before the UEFA.": True,
            "The 'Miracle of Istanbul' refers to Liverpool's comeback in the 2005 UEFA Champions League final.": True,
            "The official FIFA anthem is called 'Waka Waka'.": False,
            "The 2022 FIFA World Cup was hosted by Qatar.": True,
            "The fastest red card in a football match was issued within 5 seconds of kickoff.": True,
            "The Bundesliga is the top-tier football league in Italy.": False,
            "Diego Maradona played for Napoli during his club career.": True,
            "The FIFA World Cup has been hosted by Africa more than once.": False,
            "VAR stands for Video Assistant Referee.": True
        }

        self.threads = []
        self.round = 0
        self.winners = []
        self.curr_winner = None
        self.lock = threading.Lock()
        self.player_names = [
            "Arya Stark",
            "Walter White",
            "Rick Grimes",
            "Daenerys Targaryen",
            "Sherlock Holmes",
            "Hermione Granger",
            "Tony Stark",
            "Michael Scott",
            "Dexter Morgan",
            "Marge Simpson"
        ]
        self.client_count = 0
        self.full_player = {}
        self.active_players = []

    def start_init(self):
        self.players = []
        self.player_answers = {}
        self.state = False
        self.round = 0
        self.curr_winner = None
        self.full_player = {}
        self.active_players = []

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
            # print("Broadcast sent")
        print("======== Server broadcast Ended ==========")

    def accept_players(self):
        print("Accepting players")
        self.server_socket.settimeout(10)  # Set socket timeout to 10 seconds
        start_time = time.time()  # Record the start time

        while True:
            if time.time() - start_time > 10 or len(self.players) == len(self.player_names):
                break  # Break out of the loop if 10 seconds have passed

            try:
                client_socket, addr = self.server_socket.accept()
                self.player_name_bot = client_socket.recv(1024).decode().strip()
                print("Client connected", addr, end="")
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

        for t in self.threads:
            t.join()
        time.sleep(1)
        # Check if no players joined within 10 seconds
        if not self.players:
            print("No players joined within 10 seconds. Restarting game...")
            self.rerun_server()
        if len(self.players) == 1:
            print('Only one Player joined , Not enough to start game , Restarting')
            self.send_message("You are the only player connected. Waiting for more players.")
            time.sleep(1)
            self.rerun_server()
        ### Starting Game
        self.start_game()

    def handle_client(self, client_socket):
        with self.lock:
            if self.client_count >= len(self.player_names):
                print("No names available.")
                client_socket.sendall(b"No names available. Connection terminated.")
                client_socket.close()
                return
            if self.player_name_bot == "":
                print(self.player_name_bot)
                player_name = self.player_names[self.client_count]
                self.client_count += 1
            else:
                player_name = self.player_name_bot

        self.players.append((player_name, client_socket))
        self.active_players = self.players.copy()
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
        welcome_message = f"Welcome to the game! Players: {', '.join(player_names)}\n"
        self.send_message(welcome_message)

        # Start the game logic
        time.sleep(1)
        self.send_question()

    def get_players_nums(self):
        p_num = 1
        p_message = []
        for p in self.active_players:
            p_message.append(f"Player {p_num}: {p[0]}\n")
            p_num += 1
        p_message = "".join(p_message)

        return p_message

    def send_message(self, message):
        curr = 0
        try:
            for i, player in enumerate(self.active_players):
                curr = i
                player[1].send(message.encode("utf-8"))
        except (ConnectionAbortedError, BrokenPipeError) as e:
            print("a client disconnected, rerunning server")
            self.active_players.pop(curr)
            self.connection_reset()

    def send_question(self):
        question, answer = random.choice(list(self.questions.items()))
        self.real_answers = {question: answer}

        p_message = self.get_players_nums()
        question_msg = "==\nTrue or false: {}\n".format(question)

        # Send question message to all players
        self.send_message(p_message)
        time.sleep(1)
        self.send_message(question_msg)

        self.receive_answers()

    def receive_answers(self):
        self.player_answers = {}
        start_time = time.time()  # Record the start time
        while True:
            # Check if time limit (10 seconds) has been exceeded
            if time.time() - start_time > 10:
                break

            # Receive answers from players
            for player_name, player_socket in self.players:
                try:
                    self.full_player[player_name] = player_socket
                    # Set a timeout for receiving data
                    player_socket.settimeout(1)
                    data = player_socket.recv(1024).decode("utf-8").strip()

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
                    pass
                except socket.error:
                    # Error occurred while receiving data
                    pass

            # Check if all players have answered
            if len(self.player_answers) == len(self.active_players):
                if all(answer == -1 for answer in self.player_answers.values()):
                    continue
                self.process_answers()
                break
        new_q_message = "10 Seconds have passed and Not all players answered picking another question"
        self.send_message(new_q_message)
        print(new_q_message)
        self.send_question()

    def process_answers(self):
        first_question = next(iter(self.real_answers))
        correct_players = [player for player, response in self.player_answers.items() if
                           response == self.real_answers[first_question]]
        wrong_players = [player for player, response in self.player_answers.items() if
                         response != self.real_answers[first_question]]

        if len(correct_players) != 0:
            self.active_players = []

        for pl in correct_players:
            self.active_players.append((pl, self.full_player[pl]))

        wrong_players_soc = []
        for pl in wrong_players:
            wrong_players_soc.append(self.full_player[pl])

        if len(correct_players) == 1:
            # Only one player answered correctly, declare them as the winner
            winner = next(iter(correct_players))
            self.curr_winner = winner
            self.winners.append(winner)
            self.send_message(f"{winner} is correct! {winner} wins!\n")
            time.sleep(1)
            for player in wrong_players_soc:
                player.send("You lose\n".encode("utf-8"))
            time.sleep(3)
            self.active_players = self.players.copy()  # for sending game over to all
            self.game_over()

        elif len(correct_players) > 1:
            if wrong_players_soc:
                for player in wrong_players_soc:
                    #player.send("You lose\n").encode("utf-8")
                    player.send(b"You lose\n")

            # Multiple players answered correctly, continue the game for the next round
            print("Multiple players answered correctly. Continuing to the next round...")
            time.sleep(1)
            self.start_game()  # Start the next round

        else:
            # No players answered correctly, send another question
            print("All players answered incorrectly. Sending another Question.")
            self.send_question()

    def connection_reset(self):
        # Send summary message to all players
        summary_msg = f"Game over!\nReset game, a client disconnected\n"
        self.send_message(summary_msg)
        time.sleep(1)
        print("Game over, Reset game, a client disconnected")
        time.sleep(3)
        # Close all client connections
        for player in self.active_players:
            player[1].close()

        print("Connections closed, sending out offer requests...")
        self.rerun_server()

    def game_over(self):
        # Send summary message to all players
        summary_msg = f"Game over!\nCongratulations to the winner: {self.curr_winner}\n"
        self.send_message(summary_msg)
        time.sleep(1)
        print("Game over, Closing connections...")

        # Close all client connections
        for player in self.active_players:
            player[1].close()

        print("Connections closed, sending out offer requests...")
        self.rerun_server()

    def rerun_server(self):
        time.sleep(1)
        self.client_count = 0
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
