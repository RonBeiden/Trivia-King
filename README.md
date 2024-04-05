## Trivia King

### Overview
The Trivia King project consists of a server and client applications that facilitate a multiplayer trivia game. The server manages the game, broadcasting offers, accepting player connections, handling game rounds, and determining winners. Clients connect to the server, receive questions, and submit answers.

### Server
The server is responsible for orchestrating the trivia game. It broadcasts offers, accepts player connections, manages game rounds, and determines winners.

#### Server Features:
- **Broadcasting Offers:** The server broadcasts offers to potential clients using UDP.
- **Accepting Players:** It accepts player connections via TCP sockets.
- **Game Management:** Manages game rounds, sends questions to players, receives and processes answers, and determines winners.
- **Restart Mechanism:** If no players join or insufficient players join, the server restarts.

### Client
The client application connects to the server to participate in the trivia game. It receives questions, provides answers, and interacts with the server.

#### Client Features:
- **Connecting to Server:** Clients connect to the server using TCP sockets.
- **Receiving Questions:** Receives trivia questions from the server.
- **Submitting Answers:** Provides answers to trivia questions.
- **Game Participation:** Participates in the trivia game until it ends.
- **Reconnection:** Reconnects if disconnected.

### How to Run
1. **Server:** Run the server application. It will listen for connections and manage the game.
   
   ```
   python server.py
   ```
   
2. **Client:** Run the client application to connect to the server and participate in the game.
   
   ```
   python client.py
   ```

3. **Bot:** Optionally, run the bot application to simulate a player. The bot will choose random answers during the game.
   
   ```
   python bot.py
   ```

### Requirements
- Python 3.x
- `inputimeout` library (install via `pip install inputimeout`)

### Contributors
- Developed by Ron Beiden, Eyal Ben Barouch and Gilad Schwarz
