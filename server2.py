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
    for client in clients[:]:
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


def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        client_to_kick.send("You have been kicked by the Admin!".encode("utf-8"))
        clients.remove(client_to_kick)
        client_to_kick.close()
        nicknames.remove(name)
        broadcast(f"{name} was kicked by Admin!".encode('utf-8'))
    else:
        broadcast(f"{name} is not in the chat!".encode('utf-8'))


def handle(client):
    nickname = None
    try:
        index = clients.index(client)
        nickname = nicknames[index]
    except ValueError:
        return

    while True:
        try:
            msg = client.recv(1024)
            if not msg:
                break
            message = msg.decode().strip()

            if message.lower() == 'q':
                break

            elif message.startswith("KICK"):
                if nicknames[clients.index(client)].lower() == "admin":
                    name = message[5:].strip()
                    kick_user(name)
                else:
                    client.send("Command was refused!".encode("utf-8"))
            elif message.startswith("BAN"):
                if nicknames[clients.index(client)].lower() == "admin":
                    name = message[4:].strip()
                    kick_user(name)
                    with open("bans.txt", "a") as f:
                        f.write(name.lower() + "\n")
                    broadcast(f"{name} has been banned from the chat!")
                    print(f"{name} has been banned!")
                else:
                    client.send("Command was refused!".encode("utf-8"))
            else:
                broadcast(message)
        except:
            if client in clients:
                try:
                    index = clients.index(client)
                    nickname = nicknames[index]
                    broadcast(f"{nickname} has left the chat.")
                    clients.pop(index)
                    nicknames.pop(index)
                    print(f"{nickname} has been removed.")
                    client.close()
                    break
                except ValueError:
                    pass


def receive():
    while True:
        try:
            client, address = server.accept()
        except OSError:
            break

        client.send("NICK".encode("utf-8"))
        nickname = client.recv(1024).decode("utf-8").strip()
        nickname = nickname[0].upper() + nickname[1:].lower()

        if nickname.lower() in [n.lower() for n in nicknames]:
            client.send("This user is already in the chat room.".encode("utf-8"))
            client.close()
            continue

        with open("bans.txt", "r") as f:
            bans = [line.strip().lower() for line in f.readlines()]
        if nickname.lower() in bans:
            client.send("BAN".encode("utf-8"))
            client.close()
            continue

        if nickname.lower() == "admin":
            client.send("PASS".encode("utf-8"))
            password = client.recv(1024).decode("utf-8")
            if password != "adminpass":
                client.send("REFUSE".encode("utf-8"))
                client.close()
                continue

        clients.append(client)
        nicknames.append(nickname)
        client.send("OK".encode("utf-8"))

        broadcast(f"{nickname} has joined the chat!\n")
        client.send(f"You have joined the chat as {nickname}.".encode('utf-8'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


def server_shutdown():
    while True:
        cmd = input().lower()
        if cmd == 'q':
            print("Server shutting down...")
            broadcast("SHUTDOWN".encode("utf-8"))
            for client in clients:
                try:
                    client.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                client.close()
            server.close()
            break


print("Server starting...")
threading.Thread(target=server_shutdown, daemon=True).start()
receive()
