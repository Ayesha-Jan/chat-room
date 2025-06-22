import socket
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

        # Ask for nickname
        msg_box = tk.Tk()
        msg_box.withdraw()
        self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname", parent=msg_box)
        if not self.nickname:
            self.sock.close()
            sys.exit()

        self.running = True
        self.gui_done = False
        self.queue = queue.Queue()

        # Start receiving thread
        threading.Thread(target=self.receive, daemon=True).start()

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

        self.msg_label = tk.Label(self.win, text="Message", bg='lightgray', font=("Arial", 12))
        self.msg_label.pack(padx=20, pady=5)

        self.input_area = tk.Text(self.win, height=3)
        self.input_area.pack(padx=20, pady=5)

        self.send_button = tk.Button(self.win, text="Send", command=self.write, font=("Arial", 12))
        self.send_button.pack(padx=20, pady=5)

        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.gui_done = True

        # Periodically check the queue
        self.update_gui()
        self.win.mainloop()

    def update_gui(self):
        while not self.queue.empty():
            message = self.queue.get()
            self.text_area.config(state="normal")
            self.text_area.insert("end", message + "\n")
            self.text_area.yview("end")
            self.text_area.config(state="disabled")
        self.win.after(100, self.update_gui)

    def write(self):
        message = self.input_area.get("1.0", "end").strip()
        if message:
            try:
                self.sock.send(f"{self.nickname}: {message}".encode("utf-8"))
            except Exception as e:
                messagebox.showerror("Error", f"Could not send message:\n{e}")
        self.input_area.delete("1.0", "end")

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


if __name__ == "__main__":
    Client(HOST, PORT)
