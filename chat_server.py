import socket
import threading

HOST = '127.0.0.1'
PORT = 10346

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
nicknames = []


def broadcast(message, exclude=None):
    if isinstance(message, str):
        message = message.encode('utf-8')
    for client in clients[:]:
        if client == exclude:
            continue
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
    try:
        lower_nicks = [n.lower() for n in nicknames]
        if name.lower() in lower_nicks:
            name_index = lower_nicks.index(name.lower())
            client_to_kick = clients[name_index]
            client_to_kick.send("You have been kicked by the Admin!".encode("utf-8"))
            clients.remove(client_to_kick)
            nicknames.pop(name_index)
            client_to_kick.close()
            name = name.capitalize()
            broadcast(f"{name} was kicked by Admin!".encode('utf-8'))
            print(f"{name} was kicked by Admin!")
        else:
            admin_index = lower_nicks.index("admin")
            admin_client = clients[admin_index]
            admin_client.send(f"{name} is not in the chat!".encode('utf-8'))
            return
    except:
        print("Error in kick user")


def unban_user(name):
    try:
        lower_nicks = [n.lower() for n in nicknames]
        with open("bans.txt", "r") as f:
            bans = [line.strip().lower() for line in f.readlines()]
        if name.lower() not in bans:
            if "admin" in lower_nicks:
                admin_index = lower_nicks.index("admin")
                admin_client = clients[admin_index]
                admin_client.send(f"{name} is not banned.".encode('utf-8'))
            return

        bans = [ban for ban in bans if ban != name.lower()]
        with open("bans.txt", "w") as f:
            for ban in bans:
                f.write(ban + "\n")

        broadcast(f"{name} has been unbanned by Admin!")
        print(f"{name} was unbanned by Admin!")

    except Exception as e:
        print(f"Error in unban user: {e}")


def handle(client):
    nickname = None
    try:
        index = clients.index(client)
        nickname = nicknames[index]
    except ValueError:
        return

    try:
        while True:
            msg = client.recv(1024)
            if not msg:
                break
            message = msg.decode().strip()

            if message.lower() == 'q':
                break
            elif message.startswith("KICK"):
                if nickname.lower() == "admin":
                    name = message[5:].strip()
                    kick_user(name)
                else:
                    client.send("Command was refused!".encode("utf-8"))
            elif message.startswith("BAN"):
                if nickname.lower() == "admin":
                    name = message[4:].strip()
                    kick_user(name)
                    with open("bans.txt", "a") as f:
                        f.write(name.lower() + "\n")
                    broadcast(f"{name} has been banned from the chat by Admin!")
                else:
                    client.send("Command was refused!".encode("utf-8"))
            elif message.startswith("UNBAN"):
                if nickname.lower() == "admin":
                    name = message[6:].strip()
                    unban_user(name)
                else:
                    client.send("Command was refused!".encode("utf-8"))
            else:
                broadcast(message)
    except:
        pass
    finally:
        if client in clients:
            try:
                index = clients.index(client)
                nickname = nicknames[index]
                clients.pop(index)
                nicknames.pop(index)
                broadcast(f"{nickname} has left the chat.")
                print(f"{nickname} has been removed.")
            except ValueError:
                pass
        client.close()


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

        print(f"{nickname} connected from {address}")
        broadcast(f"{nickname} has joined the chat!\n", exclude=client)

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
