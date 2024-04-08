import socket
import time
import random
from threading import Timer, Thread
import threading
import struct


class Server:
    """
    A class representing the "Solidim" trivia game server

    Attributes:
        UDP_PORT (int): UDP port number for communication.
        TCP_PORT (int): TCP port number for communication.
        MAGIC_COOKIE (int): Unique identifier for protocol communication.
        OFFER_MESSAGE_TYPE (int): Message type for an offer message.
        SERVER_NAME (str): Name or identifier of the server.
        BROADCAST_INTERVAL (int): Interval (in seconds) for broadcasting messages.
        host (str): Host address.
        port (int): Port number.
        addresses (dict): Dictionary to store client addresses.
        players (list): List to store player information.
        player_answers (dict): Dictionary to store player answers.
        real_answers (dict): Dictionary to store correct answers.
        server_socket (socket.socket): TCP socket object for server-client communication.
        server_udp_socket (socket.socket): UDP socket object for broadcasting.
        state (bool): State of the server (True for active, False for waiting).
        timer: Timer for state transition.
        player_name_bot (str): Name of a bot player.
        questions (dict): Dictionary containing trivia questions and answers.
        threads (list): List to store thread objects.
        round (int): Current round number.
        winners (dict): Dictionary to store winners' information.
        curr_winner (str): Current winner's name.
        lock (threading.Lock): Threading lock object.
        player_names (list): List of predefined player names.
        client_count (int): Number of connected clients.
        full_player (dict): Dictionary to store full player information.
        active_players (list): List to store active player information.
        inputs (dict): Dictionary to store input data.
    """

    def __init__(self, host):
        self.UDP_PORT = 13117
        self.TCP_PORT = 12345
        self.MAGIC_COOKIE = 0xABCDDCBA
        self.OFFER_MESSAGE_TYPE = 0x2
        self.SERVER_NAME = "Solidim"
        self.BROADCAST_INTERVAL = 1
        self.host = host
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
        self.winners = {}
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
        self.inputs = {}

    def game_statistics(self):
        """
        Calculate and display game statistics.

        Calculates statistics such as the player/s with the most wins in game history
        and the most common answer among players. Sends the statistics as messages to
        connected clients and prints them to the server console.

        Note:
            This method assumes that self.winners and self.inputs dictionaries are populated
            with relevant data.

        Returns:
            None
        """
        statistics_message = "Game Statistics:\n"
        max_value_wins = max(self.winners.values())
        keys_with_max_value = [key for key, value in self.winners.items() if value == max_value_wins]
        keys_with_max_value = " ".join(keys_with_max_value)
        max_winner = f"Players with most wins in game history: {keys_with_max_value}\n"

        max_value_answer = max(self.inputs.values())
        keys_with_max_value_answer = [key for key, value in self.inputs.items() if value == max_value_answer]
        most_common_answer = f"The most common answer is: {keys_with_max_value_answer}\n"

        final_message = statistics_message + max_winner + most_common_answer
        self.send_message(final_message)
        print(final_message)
        time.sleep(1)

    def start_init(self):
        """
        Reset game-related attributes to their initial state.

        Clears player lists, resets game state, round number, current winner, and active players.

        Returns:
            None
        """

        self.players = []
        self.player_answers = {}
        self.state = False
        self.round = 0
        self.curr_winner = None
        self.full_player = {}
        self.active_players = []
        self.UDP_PORT = self.find_available_udp_port(11111, 12000)
        self.TCP_PORT = self.find_available_tcp_port(11111, 12000, self.UDP_PORT)

    def start_init_rerun(self):
        """
        Reset game-related attributes to their initial state for rerun.

        Clears player lists, resets game state, round number, current winner, and active players.

        This method is intended for resetting game-related attributes when restarting the game for a rerun.

        Returns:
            None
        """
        self.players = []
        self.player_answers = {}
        self.state = False
        self.round = 0
        self.curr_winner = None
        self.full_player = {}
        self.active_players = []

    def start(self):
        """
         Start the server and initialize game state.
         Binds the server socket to the specified port, listens for incoming connections,
         and prints a message indicating that the server has started.


         Returns:
             None
         """
        self.start_init()
        self.server_socket.bind(("", self.TCP_PORT))
        self.server_socket.listen()
        print("Server started, listening on Port", self.TCP_PORT)

    def send_offer_announcements(self):
        """
        Broadcast offer announcements to clients using UDP.

        Constructs a message packet with a magic cookie, offer message type, server name, and TCP port.
        Sends the packet as a UDP broadcast to all clients on the network.

        Returns:
            None
        """
        message = struct.pack(
            "!Ib32sH",
            self.MAGIC_COOKIE,
            self.OFFER_MESSAGE_TYPE,
            self.SERVER_NAME.encode().ljust(32),
            self.TCP_PORT,
        )
        # Create UDP socket
        print("Server broadcasting offers on UDP port", self.UDP_PORT)

        while not self.state:
            self.server_udp_socket.sendto(message, ("<broadcast>", self.UDP_PORT))
            time.sleep(self.BROADCAST_INTERVAL)
        print("======== Server broadcast Ended ==========")

    def accept_players(self):
        """
        Accept incoming player connections and start the game when enough players join.

        Listens for incoming connections from players for a duration of 10 seconds or until
        the maximum number of players (determined by the length of self.player_names) is reached.
        Creates a thread to handle each player's connection and starts the thread.
        Sets the server state to True and starts the game when enough players have joined.
        Restarts the game if no players join within 10 seconds or only one player joins.

        Returns:
            None
        """
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
                print("")
                player_name = self.player_name_bot

        self.players.append((player_name, client_socket))
        self.active_players = self.players.copy()
        print(f"Player {player_name} connected.")

    def reset_timer(self):
        """
        Reset the game timer for the next round.
        Cancels any existing timer and sets a new timer for 10 seconds,
        after which the game will automatically start.

        Returns:
            None
        """
        if self.timer is not None:
            self.timer.cancel()  # Cancel existing timer
        self.timer = Timer(10, self.start_game)  # Reset timer for 10 seconds
        self.timer.start()  # Start the timer

    def start_game(self):
        """
        Start the trivia game.
        Changes the server state to game mode, increments the round number,
        sends a welcome message with player names to all clients, and starts
        the game logic by sending the first trivia question.

        Returns:
            None
        """
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
        """
        Send a message to all active players.
        Sends the provided message to each active player in self.active_players list.
        If an error occurs during sending, the method prints an error message and removes
        the disconnected player from the active players list.

        Returns:
            None
        """
        curr = 0
        try:
            for i, player in enumerate(self.active_players):
                curr = i
                player[1].send(message.encode("utf-8"))
        except Exception as e:
            print(f"The error is: {e}")
            print("a client disconnected, rerunning server")
            self.active_players.pop(curr)
            self.connection_reset()

    def send_question(self):
        """
        Send a trivia question to all active players.
        Randomly selects a trivia question from the self.questions dictionary,
        sends the question along with a players' count message to all active players,
        and initiates the process to receive player answers.

        Returns:
            None
        """
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
        """
        Receive and process answers from active players.
        Waits for answers from active players for a duration of 10 seconds.
        Receives player answers and processes them. If all players have answered,
        proceeds to process the answers. If not, sends a message to indicate
        that not all players have answered and picks another question.

        Returns:
            None
        """
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
                    if data.lower() in ['y', 't', '1', 'n', 'f', '0']:
                        self.inputs[data] = self.inputs.get(data, 0) + 1

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
        new_q_message = "10 Seconds have passed and Not all players answered picking another question \n"
        self.send_message(new_q_message)
        print(new_q_message)
        self.send_question()

    def process_answers(self):
        """
        Process player answers and handle game logic based on responses.
        Compares player answers with the correct answer for the current question.
        Determines winners, losers, and next steps based on player responses.
        Sends appropriate messages to players to inform them of the game outcome.

        Returns:
            None
        """
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
            self.winners[winner] = self.winners.get(winner, 0) + 1
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
                    # player.send("You lose\n").encode("utf-8")
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
        """
        Reset the game and send summary message to all players when a client disconnects.
        Sends a summary message to all players indicating that the game is over and
        will be reset due to a client disconnection. Closes all client connections
        and restarts the server to accept new connections.

        Returns:
            None
        """
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
        """
        Handle the game over scenario.

        Displays game statistics, announces the winner to all players,
        closes all client connections, and restarts the server to accept new connections.

        Returns:
            None
        """
        # Send summary message to all players
        self.game_statistics()
        time.sleep(1)
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
        """
        Restart the server to accept new connections.
        Resets server attributes for rerun, restarts offer announcements, and
        accepts new player connections.

        Returns:
            None
        """
        time.sleep(1)
        self.client_count = 0
        print("Restarting server...")
        self.start_init_rerun()
        threading.Thread(target=self.send_offer_announcements, daemon=True).start()
        self.accept_players()

    def run_server(self):
        """
        Start the server and begin accepting player connections.
        Starts the server and initiates offer announcements, then accepts player connections.

        Returns:
            None
        """
        self.start()
        threading.Thread(target=self.send_offer_announcements, daemon=True).start()

        self.accept_players()

    def find_available_udp_port(self, start_port, end_port):
        """
        Find an available UDP port within a specified range.

        Attempts to bind a socket to each port within the specified range to check for availability.
        Returns the first available port found within the range.

        Args:
            start_port (int): The starting port of the range to search.
            end_port (int): The ending port of the range to search.

        Returns:
            int: The first available UDP port found within the specified range.
        """
        for port in range(start_port, end_port + 1):
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind(("localhost", port))
                server_socket.close()
                return port
            except OSError as e:
                if e.errno == 98:  # errno 98: Address already in use
                    print(f"Port {port} is already in use. Trying the next port...")
                else:
                    continue  # Re-raise other OSError types

    def find_available_tcp_port(self, start_port, end_port, udp_port):
        """
        Find an available TCP port within a specified range excluding the UDP port.
        Attempts to bind a socket to each port within the specified range (excluding the UDP port)
        to check for availability. Returns the first available port found within the range.

        Args:
            start_port (int): The starting port of the range to search.
            end_port (int): The ending port of the range to search.
            udp_port (int): The UDP port to exclude from the search.

        Returns:
            int: The first available TCP port found within the specified range (excluding the UDP port).
        """
        for port in range(start_port, end_port + 1):
            if port != udp_port:
                try:
                    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_socket.bind(("", port))
                    server_socket.close()
                    return port
                except OSError as e:
                    if e.errno in (98, 48):  # errno 98: Address already in use
                        print(f"Port {port} is already in use. Trying the next port...")
                    else:
                        continue  # Re-raise other OSError types


def main():
    server = Server("127.0.0.1")
    server.run_server()


if __name__ == "__main__":
    main()
