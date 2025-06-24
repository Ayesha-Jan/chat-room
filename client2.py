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
            if message == "NICK":
                client.send(nickname.encode('utf-8'))
                next_message = client.recv(1024).decode('utf-8')
                if next_message == "PASS":
                    client.send(password.encode('utf-8'))
                    if client.recv(1024).decode('utf-8') == "REFUSE":
                        print("Connection refused! Wrong password.")
                        client.close()
                        stop_event.set()
                        break
                elif next_message == "BAN":
                    print("Connection refused because you are banned! ")
                    client.close()
                    stop_event.set()
                    break
            elif "kicked by the Admin" in message:
                print(message)
                stop_event.set()
                client.close()
                break
            else:
                print(message)
        except OSError:
            break
        except:
            print("An error occurred!")
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
                        client.send(f"KICK {message[6:]}".encode('utf-8'))
                    elif message.startswith('/ban'):
                        client.send(f"BAN {message[5:]}".encode('utf-8'))
                    else:
                        print("Unknown admin command.")
                else:
                    print("Commands can only be executed by the Admin!")
            else:
                client.send(f"{nickname}: {message}".encode('utf-8'))
        except:
            print("Cannot send message! Exiting...")
            stop_event.set()
            break


receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()