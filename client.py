import socket  # socket: lets us talk to the server (internet/network stuff).
import threading
import tkinter as tk
import tkinter.scrolledtext as scrolledtext
from tkinter import simpledialog, messagebox
import queue
import sys

HOST = '127.0.0.1'
PORT = 10532


class Client:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        # socket.socket(...): create a phone
        # connect(...): dial the server's number

        # Ask for nickname
        msg_box = tk.Tk()
        msg_box.withdraw()
        self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname", parent=msg_box)
        if not self.nickname:
            self.sock.close()
            sys.exit()
        #We make a hidden window.
        # askstring(...): pop up a box asking "What’s your name?"
        # If they cancel or leave it blank, exit the app.

        self.running = True
        self.gui_done = False
        self.queue = queue.Queue()
        # running: means the app is still on.
        # gui_done: tells us when the GUI is fully built.
        # queue: holds messages we want to show.

        # Start receiving thread
        threading.Thread(target=self.receive, daemon=True).start()
        # This starts another worker (thread) that listens to the server.
        # Like having a friend read incoming texts aloud.

        # Start GUI in main thread
        self.gui_loop()

    def gui_loop(self):
        self.win = tk.Tk()
        self.win.title(f"Chat - {self.nickname}")
        self.win.configure(bg='lightgray')

        self.chat_label = tk.Label(self.win, text="Chat", bg='lightgray', font=("Arial", 12))
        self.chat_label.pack(padx=20, pady=5)

        self.text_area = scrolledtext.ScrolledText(self.win)
        self.text_area.pack(padx=20, pady=5)
        self.text_area.config(state="disabled")
        # This is where messages show up.
        # It's scrollable.
        # Disabled = can't type in it.

        self.msg_label = tk.Label(self.win, text="Message", bg='lightgray', font=("Arial", 12))
        self.msg_label.pack(padx=20, pady=5)
        # A label that says "Message".

        # A little box where you type your message.
        self.input_area = tk.Text(self.win, height=3)
        self.input_area.pack(padx=20, pady=5)

        self.send_button = tk.Button(self.win, text="Send", command=self.write, font=("Arial", 12))
        self.send_button.pack(padx=20, pady=5)

        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.gui_done = True

        # Periodically check the queue
        self.update_gui()
        self.win.mainloop()
        # protocol(...): if you click the "X", call stop() to cleanly close
        # gui_done = True: now GUI is ready
        # update_gui(): starts a loop to update messages
        # mainloop(): shows the window and keeps it running

    def update_gui(self):
        while not self.queue.empty():
            message = self.queue.get()
            self.text_area.config(state="normal")
            self.text_area.insert("end", message + "\n")
            self.text_area.yview("end")
            self.text_area.config(state="disabled")
        self.win.after(100, self.update_gui)
        # While there are new messages in the queue:
        # Enable the message box
        # Insert the new message
        # Scroll to the bottom
        # Disable it again
        # after(100, ...): do this again every 100ms

    def write(self):
        message = self.input_area.get("1.0", "end").strip()
        if message:
            try:
                self.sock.send(f"{self.nickname}: {message}".encode("utf-8"))
            except Exception as e:
                messagebox.showerror("Error", f"Could not send message:\n{e}")
        self.input_area.delete("1.0", "end")
        # get(...): grabs the message you typed
        # strip(): removes spaces/newlines
        # send(...): sends it to the server
        # Then it clears the box

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        self.win.destroy()
        sys.exit()

    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode("utf-8")
                if message == "NICK":
                    self.sock.send(self.nickname.encode("utf-8"))
                else:
                    self.queue.put(message)
            except Exception as e:
                self.queue.put(f"Error: {e}")
                self.sock.close()
                break
    # recv(...): waits for message from the server
    # If the server says "NICK", send your name
    # Otherwise, put the message into the queue
    # If anything breaks, close socket and exit loop


if __name__ == "__main__":
    Client(HOST, PORT)

# socket.connect()	Connects to the server
# simpledialog.askstring()	Asks for your nickname
# threading.Thread(...)	Lets you receive messages in the background
# tkinter GUI	Chat window you see and use
# queue.Queue()	Safely moves messages from background to GUI
# self.sock.send(...)	Sends a message to everyone
# self.sock.recv(...)	Listens for new messages