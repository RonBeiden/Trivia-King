import socket
import time
import random
from threading import Timer, Thread


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.name = "Mystic"
        self.addresses = {}
        self.players = []
        self.player_answers = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.state = "waiting"  # Initial state is waiting
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

    def start_init(self):
        self.players = []
        self.player_answers = {}
        self.state = "waiting"
        self.round = 0
        self.curr_winner = None

    def start(self):
        self.start_init()
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Server started, listening on IP address", self.host)

    def send_offer_announcements(self):
        offer_msg = "offer from server Mystic at address {}:{}".format(self.host, self.port)
        # Implement UDP broadcast to send offer announcements
        print(offer_msg)

    def accept_players(self):
        start_time = time.time()  # Record the start time
        while True:
            if time.time() - start_time > 10:
                break  # Break out of the loop if 10 seconds have passed

            client_socket, addr = self.server_socket.accept()
            self.addresses[client_socket] = addr
            thr = Thread(target=self.handle_client, args=(client_socket,))
            self.threads.append(thr)
            thr.start()
            time.sleep(.1)

        # print("joining")
        for t in self.threads:
            t.join()
        time.sleep(1)

        # Check if no players joined within 10 seconds
        if not self.players:
            print("No players joined within 10 seconds. Exiting...")
            return

    def handle_client(self, client_socket):
        player_name = client_socket.recv(1024).decode("utf-8")
        player_name = player_name[:-1]
        self.players.append((player_name, client_socket))
        print(f"Player {player_name} connected.")
        if self.state == "waiting":
            self.reset_timer()  # Reset the timer after a player joins

    def reset_timer(self):
        if self.timer is not None:
            self.timer.cancel()  # Cancel existing timer
        self.timer = Timer(10, self.start_game)  # Reset timer for 10 seconds
        self.timer.start()  # Start the timer

    def start_game(self):
        self.state = "game"  # Change state to game mode
        self.round += 1
        print(f"Starting round {self.round}...")
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

    def send_question(self):
        question, answer = random.choice(list(self.questions.items()))
        p_message = self.get_players_nums()
        question_msg = "==\nTrue or false: {}\n".format(question)

        # Send question message to all players
        self.send_message(p_message)
        time.sleep(1)
        self.send_message(question_msg)

        # Store the correct answer for each player
        self.player_answers = {player: answer for player in self.players}
        # Start receiving answers
        self.receive_answers()

    def send_message(self, message):
        for player in self.players:
            player[1].sendall(message.encode("utf-8"))

    def receive_answers(self):
        answers = {}
        while True:
            time.sleep(1)  # Adjust sleep time as needed
            for player in self.players:
                try:
                    data = player[1].recv(1024).decode("utf-8").strip()
                    if data.lower() in ['y', 't', '1']:
                        response = True
                    elif data.lower() in ['n', 'f', '0']:
                        response = False
                    else:
                        response = -1
                    answers[player] = response
                    if len(answers) == len(self.players):
                        self.process_answers(answers)
                except socket.error:
                    pass

    def process_answers(self, answers):
        correct_players = [player for player, response in answers.items() if response == self.player_answers[player]]
        if len(correct_players) == 1:
            winner = next(iter(correct_players))
            self.curr_winner = winner[0]
            self.winners.append(winner[0])
            self.send_message(f"{winner[0]} is correct! {winner[0]} wins!")
            self.game_over()
        else:
            for player, response in answers.items():
                if response == self.player_answers[player]:
                    self.send_message(f"{player[0]} is correct!")
                    correct_players.append(player)
                else:
                    self.send_message(f"{player[0]} is incorrect!")
                    self.players.remove(player)

            self.start_game()

    def game_over(self):
        # Send summary message to all players
        summary_msg = f"Game over!\nCongratulations to the winner: {self.curr_winner}"
        self.send_message(summary_msg)
        print("Game over, sending out offer requests...")
        self.run_server()

    def run_server(self):
        self.start()
        self.send_offer_announcements()
        self.accept_players()


def main():
    server = Server("localhost", 12345)
    server.run_server()


if __name__ == "__main__":
    main()
