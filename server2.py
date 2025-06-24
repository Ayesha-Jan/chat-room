import socket
import sys
import threading

HOST = '127.0.0.1'
PORT = 10346

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
nicknames = []


def broadcast(message):
    if isinstance(message, str):
        message = message.encode('utf-8')
    for client in clients[:]:  # Iterate over a copy
        try:
            client.send(message)
        except:
            try:
                index = clients.index(client)
                nickname = nicknames[index]
                clients.remove(client)
                nicknames.remove(nickname)
                print(f"Removed disconnected client: {nickname}")
                client.close()
            except ValueError:
                pass


def handle(client):
    nickname = None
    try:
        index = clients.index(client)
        nickname = nicknames[index]
    except ValueError:
        pass  # Client might've been removed earlier

    while True:
        try:
            msg = client.recv(1024)
            if not msg:
                break
            message = msg.decode()
            if message.lower() == 'q':
                break
            elif message.startswith("KICK"):
                if nicknames[clients.index(client)] == "Admin":
                    name_to_kick = message[5:]
                    kick_user(name_to_kick)
                    print(f"{name_to_kick} has been kicked!")
                    return
                else:
                    client.send("Command was refused!".encode("utf-8"))
            elif message.startswith("BAN"):
                if nicknames[clients.index(client)] == "Admin":
                    name_to_ban = message[4:]
                    kick_user(name_to_ban)
                    with open("bans.txt", "a") as f:
                        f.write(name_to_ban + "\n")
                    broadcast(f"{name_to_ban} has been banned from the chat!".encode('utf-8'))
                    print(f"{name_to_ban} has been banned!")
                    return
                else:
                    client.send("Command was refused!".encode("utf-8"))
            if not (message.startswith("KICK") or message.startswith("BAN")):
                broadcast(message)
        except:
            break  # Any connection error

    # Cleanup after disconnect
    if client in clients:
        try:
            index = clients.index(client)
            nickname = nicknames[index]
            broadcast(f"{nickname} has left the chat.".encode('utf-8'))
            clients.remove(client)
            nicknames.remove(nickname)
            print(f"{nickname} has been removed.")
        except ValueError:
            pass
    client.close()


def receive():
    try:
        while True:
            client, address = server.accept()

            client.send("NICK".encode("utf-8"))
            nickname = client.recv(1024).decode("utf-8")

            if nickname in nicknames:
                client.send("This user is already in the chat room.".encode("utf-8"))
                client.close()
                continue

            with open("bans.txt", "r") as f:
                bans = f.readlines()
            if nickname+'\n' in bans:
                client.send("BAN".encode("utf-8"))
                client.close()
                continue

            if nickname == "Admin":
                client.send("PASS".encode("utf-8"))
                password = client.recv(1024).decode("utf-8")
                if password != "adminpass":
                    client.send("REFUSE".encode("utf-8"))
                    client.close()
                    break

            clients.append(client)
            nicknames.append(nickname)

            print(f"Connected with {str(address)}")
            print(f"Nickname of the client is {nickname}")
            broadcast(f"{nickname} has joined the chat!\n".encode('utf-8'))
            client.send("You have joined the chat!".encode("utf-8"))

            handle_thread = threading.Thread(target=handle, args=(client,))
            handle_thread.start()

    except OSError:
        print("Server socket closed. Exiting.")


def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        client_to_kick.send("You have been kicked by the Admin!".encode("utf-8"))
        broadcast(f"{name} has been kicked from the chat!".encode('utf-8'))
        clients.remove(client_to_kick)
        client_to_kick.close()
        nicknames.remove(name)


def server_shutdown():
    while True:
        cmd = input('').lower()
        if cmd == 'q':
            broadcast("SHUTDOWN".encode("utf-8"))
            for client in clients:
                client.close()
            server.close()
            print("Server shutting down...")
            sys.exit()


print("Server starting...")
thread = threading.Thread(target=server_shutdown, daemon=True).start()
receive()
