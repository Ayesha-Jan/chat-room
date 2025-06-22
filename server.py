import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 10532

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

clients = []
nicknames = []


def broadcast(message):
    for client in clients:
        client.send(message)


def handle(client):
    while True:
        try:
            msg = message = client.recv(1024)
            if msg.decode("utf-8").startswith("KICK"):
                if nicknames[clients.index(client)] == "Admin":
                    name_to_kick = msg.decode("utf-8")[5:]
                    kick_user(name_to_kick)
                    print(f"{name_to_kick} has been kicked!")
                else:
                    client.send("Command was refused!".encode("utf-8"))
            elif msg.decode("utf-8").startswith("BAN"):
                if nicknames[clients.index(client)] == "Admin":
                    name_to_ban = msg.decode("utf-8")[4:]
                    kick_user(name_to_ban)
                    with open ("bans.txt", "a") as f:
                        f.write(name_to_ban + "\n")
                    print(f"{name_to_ban} has been banned!")
                else:
                    client.send("Command was refused!".encode("utf-8"))
            else:
                broadcast(message)
        except:
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                broadcast(f"{nickname} has left the chat!".encode('utf-8'))
                nicknames.remove(nickname)
                break


def receive():
    try:
        while True:
            client, address = server.accept()

            client.send("NICK".encode("utf-8"))
            nickname = client.recv(1024).decode("utf-8")

            with open ("bans.txt", "r") as f:
                bans = f.readlines()

            if nickname+'\n' in bans:
                client.send("BAN".encode("utf-8"))
                client.close()
                continue

            if nickname == "Admin":
                client.send("PWD".encode("utf-8"))
                password = client.recv(1024).decode("utf-8")
                if password != "adminpass":
                    client.send("REFUSE".encode("utf-8"))
                    client.close()
                    continue

            nicknames.append(nickname)
            clients.append(client)

            print(f"Connected with {str(address)}")
            print(f"Nickname of the client is {nickname}")
            broadcast(f"{nickname} has joined the chat!\n".encode('utf-8'))
            client.send("Connected to the server!".encode("utf-8"))

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server...")
        for client in clients:
            try:
                client.close()
            except:
                pass
        server.close()
        sys.exit(0)


def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        client_to_kick.send("You have been kicked by the Admin!".encode("utf-8"))
        client_to_kick.close()
        nicknames.remove(name)
        broadcast(f"{name} was kicked by Admin!".encode('utf-8'))


print("Server is listening...")
receive()
