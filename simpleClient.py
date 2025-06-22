import socket
import threading

nickname = input("Enter your nickname: ").capitalize()
if nickname == "Admin":
    password = input("Enter password for Admin: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 10532))
client.settimeout(2.0)

stop_thread = False


def receive():
    while True:
        global stop_thread
        if stop_thread:
            break
        try:
            message = client.recv(1024).decode('utf-8')
            if message == "NICK":
                client.send(nickname.encode('utf-8'))
                next_message = client.recv(1024).decode('utf-8')
                if next_message == "PWD":
                    client.send(password.encode('utf-8'))
                    if client.recv(1024).decode('utf-8') == "REFUSE":
                        print("Connection refused! Wrong password. ")
                        stop_thread = True
                elif next_message == "BAN":
                    print("Connection refused because you are banned! ")
                    client.close()
                    stop_thread = True
            elif "kicked by the Admin" in message:
                print(message)
                stop_thread = True
                client.close()
                break
            else:
                print(message)
        except socket.timeout:
            continue
        except:
            print("An error occurred!")
            client.close()
            break


def write():
    while True:
        if stop_thread:
            break
        try:
            msg = input('')
            if msg.startswith('/'):
                if nickname == "Admin":
                    if msg.startswith('/kick'):
                        client.send(f"KICK {msg[6:]}".encode('utf-8'))
                    elif msg.startswith('/ban'):
                        client.send(f"BAN {msg[5:]}".encode('utf-8'))
                    else:
                        print("Unknown admin command.")
                else:
                    print("Commands can only be executed by the Admin!")
            else:
                message = f"{nickname}: {msg}"
                client.send(message.encode('utf-8'))
        except:
            print("Cannot send message. Server is likely down.")
            break


receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
