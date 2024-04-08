# Import necessary modules
import socket
import struct
from inputimeout import inputimeout, TimeoutOccurred


class Client:
    """
    Represents a client connecting to the trivia game server.

    Attributes:
        host (str): The hostname of the server.
        client_socket: The TCP socket for communication with the server.
        udp_socket: The UDP socket for broadcast communication.
        MAGIC_COOKIE (int): A unique identifier used in communication with the server.
        OFFER_MESSAGE_TYPE (int): The message type for offer announcements.
        UDP_PORT (int): The UDP port for communication with the server.
        TCP_PORT (int): The TCP port for communication with the server.
        SERVER_IP (str): The IP address of the server.
        colors (dict): A dictionary containing ANSI escape codes for color formatting.
    """
    def __init__(self, host):
        self.host = host
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.MAGIC_COOKIE = 0xABCDDCBA
        self.OFFER_MESSAGE_TYPE = 0x2
        self.UDP_PORT = None
        self.TCP_PORT = None
        self.SERVER_IP = None
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

    def get_offer_from_server(self, portstart, portend):
        """
        Listen for offer messages from the server on UDP within a specified port range.
        Continuously listens for offer messages from the server on UDP ports within the specified range.
        When an offer message is received, validates it and extracts relevant information (server IP and TCP port).
        Sets the client's UDP port, TCP port, and server IP attributes accordingly.

        Args:
            portstart (int): The starting port of the range to listen on.
            portend (int): The ending port of the range to listen on.

        Returns:
            tuple: A tuple containing the server's IP address and TCP port if a valid offer message is received,
                   or None if no valid offer message is received within the specified range.
        """
        print(f"Client started, listening for UDP messages.... in range of {portstart} to {portend}")
        for port in range(portstart, portend + 1):
            print(port)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                udp_socket.settimeout(2)
                udp_socket.bind(("", port))
                try:
                    while True:
                        print("Waiting for message...")
                        data, addr = udp_socket.recvfrom(1024)
                        print("Received")

                        magic_cookie, message_type, server_name, tcp_port = struct.unpack(
                            "!Ib32sH", data
                        )
                        server_name = server_name.decode().strip("\x00")
                        # server_name = ''.join(char for char in server_name if char != ' ')
                        if magic_cookie == self.MAGIC_COOKIE and message_type == self.OFFER_MESSAGE_TYPE:
                            self.UDP_PORT = port
                            self.TCP_PORT = tcp_port
                            server_ip = addr[0]
                            self.SERVER_IP = server_ip
                            print(
                                f'Received offer from server "{server_name}" at address {server_ip}, '
                                f'attempting to connect...'
                            )
                            print(f'server_ip: {server_ip} , tcp_port: {tcp_port}')
                            return server_ip, tcp_port
                except OSError as e:
                    print(f"Error occurred while listening on port {port} error is {e}")
                    pass

    def send_player_name(self, player_name):
        """
        Send the player's name to the server.
        Encodes the player's name as UTF-8 and sends it to the server through the client socket.

        Args:
            player_name (str): The name of the player.

        Returns:
            None
        """
        self.client_socket.sendall(player_name.encode("utf-8") + b'\n')

    def receive_game_start_message(self):
        """
        Receive the game start message from the server.
        Attempts to receive the game start message from the server through the client socket.
        If successful, decodes and prints the message.

        Returns:
            None
        """
        try:
            game_start_message = self.client_socket.recv(1024).decode("utf-8")
            print(game_start_message)
        except Exception:
            pass

    def print_color(self, color, message):
        """
        Print a message in the specified color.
        Checks if the specified color exists in the color dictionary; if not, defaults to white.
        Prints the message with the specified color.

        Args:
            color (str): The name of the color to print the message in.
                         Possible values: 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'
            message (str): The message to be printed.

        Returns:
            None
        """
        # Check if the specified color exists, otherwise default to white
        color_code = self.colors.get(color, self.colors['white'])
        # Send the colored message to the player
        print(color_code + message + self.colors['reset'], end="")

    def receive_message_from_server(self):
        """
        Receive a message from the server and process it accordingly.
        Continuously listens for messages from the server through the client socket.
        Processes the received message based on its content and prints it with the appropriate color.
        Handles ConnectionResetError and socket.timeout exceptions gracefully.

        Returns:
            str: The received message from the server.
        """
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

    def send_answer_to_server(self, answer):
        """
        Send the player's answer to the server.
        Encodes the player's answer as UTF-8 and sends it to the server through the client socket.

        Args:
            answer (str): The player's answer.

        Returns:
            None
        """
        self.client_socket.send(answer.encode("utf-8"))

    def disconnect(self):  # disconnect and rerun
        """
        Disconnect from the server and prepare to reconnect.
        Closes the client socket and creates a new one for potential reconnection.
        Closes the UDP socket.
        Prints a message indicating disconnection and readiness to listen for offer requests.
        Restarts the client.

        Returns:
            None
        """
        self.client_socket.close()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket.close()
        print('Server disconnected, listening for offer requests....')
        self.start_client()

    def input(self, enter_input):
        """
        Get input from the user with a timeout.
        Displays the prompt to the user and waits for input for a maximum of 10 seconds.
        If no input is received within the timeout period, returns None.

        Args:
            enter_input (str): The prompt message for the user.

        Returns:
            str or None: The input provided by the user or None if no input is received within the timeout.
        """
        answer = None
        try:
            answer = inputimeout(prompt=enter_input, timeout=10)
        except TimeoutOccurred:
            pass
        return answer

    def start_client(self):
        """
        Start the client and connect to the server.

        Attempts to connect to the server using TCP/IP protocol.
        If successful, sends the bot's name to the server and waits for the game to start.
        Receives a player name assigned by the server and handles various scenarios based on the received messages.
        Enters a loop to receive questions from the server and send answers until the game ends.

        Returns:
            None
        """
        # if not self.UDP_PORT and not self.TCP_PORT:
        try:
            self.SERVER_IP, self.TCP_PORT = self.get_offer_from_server(11110, 11210)
            self.client_socket.connect((self.SERVER_IP, self.TCP_PORT))
        except Exception:
            self.disconnect()

        print("Connecting using TCP to server IP:", self.SERVER_IP)
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
        """
        Send the bot's name to the server.
        Sends an empty string as the bot's name to the server using the `send_player_name` method.

        Returns:
            None
        """
        self.send_player_name("")


def main():
    client = Client("127.0.0.1")
    client.start_client()


if __name__ == "__main__":
    main()
