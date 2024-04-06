import random
import threading
import sys
from client import Client
import uuid


class Bot(Client):
    def __init__(self, host, port):
        super().__init__(host, port)

    def send_bot_name(self):
        unique_id = uuid.uuid4()
        bot_name = f"Bot_{unique_id}"
        self.send_player_name(bot_name)

    def choose_random_answer(self):
        # Choose a random answer (Y/T/1 for True, N/F/0 for False)
        return random.choice(['y', 't', '1', 'n', 'f', '0'])

    def input(self, enter_input):
        # Bot doesn't need to wait for input, it chooses randomly
        bot_ans = self.choose_random_answer()
        print(f"Bot answer {bot_ans}")
        return bot_ans


def run_bot():
    bot = Bot("127.0.0.1", 12345)
    bot.start_client()


if __name__ == "__main__":
    # Run the bot when executing 'python bot.py'
    run_bot()
