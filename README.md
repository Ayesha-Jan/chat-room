# 💬 Chatroom

A simple Python-based chatroom application with a server and a PyQt5 client interface. Supports multiple clients, admin commands, and basic user management including bans and password-protected admin access.

---

## Features

- Multi-client chat with simultaneous connections via sockets.
- Admin user with password protection (`adminpass`).
- Admin commands:
  - `/kick <username>` — kick a user out of the chat
  - `/ban <username>` — ban a user (adds to ban list and kicks them)
  - `/unban <username>` — remove user from ban list
- Clients can quit by sending `q`.
- Server shutdown command (`q`) shuts down server and notifies clients.
- GUI client built with PyQt5.
- Clean user interface with chat display, message input, and admin controls.

---

## Files

- chat_server.py — The chat server implementation.
- chat_client.py — The PyQt5 client application.
- bans.txt — Stores banned usernames (created automatically).

---

## Getting Started

### Prerequisites

- Python 3.9+
- PyQt5

### Clone the Repository 
    
    git clone https://github.com/Ayesha-Jan/chat-room.git
    cd chat-room

---

### Server Usage

- Run the server script: `python chat_server.py`
- The server listens on localhost (127.0.0.1) port 10346.
- To shut down the server gracefully, enter `q` in the server console.

### Client Usage

- Run the client script: `python chat_client.py`
- Enter your Nickname in the input field.
- If you want to log in as Admin, enter the password: `adminpass`.
- Use the chat interface to send and receive messages.
- To quit the chat, type `q` and press Enter or click Send.

---

## Author

Developed by: Ayesha A. Jan
Email: Ayesha.Jan@stud.srh-campus-berlin.de
🎓 BST Computer Networks Project – 2025
