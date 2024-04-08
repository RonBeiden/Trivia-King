import random
import threading
import sys
from client import Client
import uuid


class Bot(Client):
    """
    Represents a bot player in the trivia game.
    Inherits from the Client class.

    Attributes:
        host (str): The hostname of the server.
    """

    def __init__(self, host):
        super().__init__(host)

    def send_bot_name(self):
        """
        Send the bot unique name to the server.
        Generates a unique name for the bot using a UUID and sends it to the server.

        Returns:
            None
        """
        unique_id = uuid.uuid4()
        bot_name = f"\nBOT_{unique_id}"
        self.send_player_name(bot_name)

    def choose_random_answer(self):
        """
        Choose a random answer for the trivia question.

        Returns:
            str: A random answer choice ('y', 't', '1' for True, 'n', 'f', '0' for False).
        """
        # Choose a random answer (Y/T/1 for True, N/F/0 for False)
        return random.choice(['y', 't', '1', 'n', 'f', '0'])

    def input(self, enter_input):
        """
        Handle bot input.
        Bot doesn't need to wait for input; it chooses randomly.
        Prints the bot's chosen answer for logging purposes.

        Args:
            enter_input: Placeholder argument for consistency with the superclass method.

        Returns:
            str: The randomly chosen answer ('y', 't', '1' for True, 'n', 'f', '0' for False).
        """
        # Bot doesn't need to wait for input, it chooses randomly
        bot_ans = self.choose_random_answer()
        print(f"Bot answer {bot_ans}")
        return bot_ans


def run_bot():
    bot = Bot("127.0.0.1")
    bot.start_client()


if __name__ == "__main__":
    # Run the bot when executing 'python bot.py'
    run_bot()
