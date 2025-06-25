import socket
import threading

nickname = input("Enter your nickname: ").capitalize()
if nickname == "Admin":
    password = input("Enter password for Admin: ")

HOST = '127.0.0.1'
PORT = 10346

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

stop_event = threading.Event()


def receive():
    while not stop_event.is_set():
        try:
            message = client.recv(1024)
            if not message:
                print("Disconnected from server.")
                stop_event.set()
                break
            message = message.decode('utf-8')
            if message == "SHUTDOWN":
                print("Server is shutting down.")
                client.close()
                stop_event.set()
                break
            elif message == "NICK":
                client.send(nickname.encode('utf-8'))
                next_message = client.recv(1024).decode('utf-8')
                if next_message == "PASS":
                    client.send(password.encode('utf-8'))
                    final = client.recv(1024).decode('utf-8')
                    if final == "REFUSE":
                        print("Connection refused! Wrong password.")
                        client.close()
                        stop_event.set()
                    else:
                        print(final)
                elif next_message == "BAN":
                    print("Connection refused because you are banned!")
                    client.close()
                    stop_event.set()
                else:
                    print(next_message)
            else:
                print(message)
        except:
            client.close()
            stop_event.set()
            break


def write():
    while not stop_event.is_set():
        try:
            message = input('')
            if stop_event.is_set():
                break
            if message.lower() == 'q':
                client.send('q'.encode('utf-8'))
                print("You have left the chat.")
                client.close()
                stop_event.set()
                break
            if message.startswith('/'):
                if nickname == "Admin":
                    if message.startswith('/kick'):
                        client.send(f"KICK {message[6:].strip()}".encode('utf-8'))
                    elif message.startswith('/ban'):
                        client.send(f"BAN {message[5:].strip()}".encode('utf-8'))
                    else:
                        print("Unknown admin command.")
                else:
                    print("Commands can only be executed by the Admin!")
            else:
                client.send(f"{nickname}: {message}".encode('utf-8'))
        except:
            stop_event.set()
            break


threading.Thread(target=receive).start()
threading.Thread(target=write).start()
