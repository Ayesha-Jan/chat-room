import sys
import socket
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QTextCursor

HOST = '127.0.0.1'
PORT = 10346


class ChatClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pink Chatroom")
        self.setStyleSheet("background-color: pink; font-family: Arial;")
        self.resize(500, 500)

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stop_event = threading.Event()

        self.layout = QVBoxLayout()
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("background-color: #fff0f5; color: black;")

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message here... Press Enter to send")
        self.input_box.setStyleSheet("background-color: white; padding: 5px;")
        self.input_box.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("background-color: #ff69b4; color: white;")

        self.admin_label = QLabel()
        self.admin_label.setStyleSheet("color: darkred; font-weight: bold;")

        self.layout.addWidget(self.chat_history)
        self.layout.addWidget(self.admin_label)
        self.layout.addWidget(self.input_box)
        self.layout.addWidget(self.send_button)

        self.setLayout(self.layout)

        self.nickname = ""
        self.password = ""

        self.connect_to_server()

    def connect_to_server(self):
        self.nickname, ok = self.get_input("Enter your nickname:")
        if not ok:
            sys.exit()

        if self.nickname.lower() == "admin":
            self.password, ok = self.get_input("Enter admin password:")
            if not ok:
                sys.exit()
            self.admin_label.setText("Admin Commands: /kick <user>, /ban <user> | Type 'q' to quit")
        else:
            self.admin_label.setText("Type 'q' to quit")

        try:
            self.client.connect((HOST, PORT))
        except Exception as e:
            self.show_error(f"Failed to connect: {e}")
            sys.exit()

        threading.Thread(target=self.receive).start()

    def receive(self):
        while not self.stop_event.is_set():
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                elif message == 'PASS':
                    self.client.send(self.password.encode('utf-8'))
                elif message == 'REFUSE':
                    self.show_error("Admin password incorrect.")
                    self.stop_event.set()
                elif message == 'BAN':
                    self.show_error("You are banned from this server.")
                    self.stop_event.set()
                elif message == 'SHUTDOWN':
                    self.append_chat("Server has shut down.")
                    self.stop_event.set()
                else:
                    self.append_chat(message)
            except:
                self.stop_event.set()
                break

    def send_message(self):
        if self.stop_event.is_set():
            return
        message = self.input_box.text().strip()
        if not message:
            return

        if message.lower() == 'q':
            self.client.send('q'.encode('utf-8'))
            self.append_chat("You have left the chat.")
            self.client.close()
            self.stop_event.set()
            self.close()
            return

        if message.startswith('/'):
            if self.nickname == "Admin":
                if message.startswith('/kick'):
                    self.client.send(f"KICK {message[6:].strip()}".encode('utf-8'))
                elif message.startswith('/ban'):
                    self.client.send(f"BAN {message[5:].strip()}".encode('utf-8'))
                else:
                    self.append_chat("Unknown command.")
            else:
                self.append_chat("Only Admin can use commands.")
        else:
            self.client.send(f"{self.nickname}: {message}".encode('utf-8'))

        self.input_box.clear()

    def append_chat(self, message):
        self.chat_history.append(message)
        self.chat_history.moveCursor(QTextCursor.End)

    def get_input(self, prompt):
        text, ok = QInputDialog.getText(self, "Chat Login", prompt)
        return text.strip().capitalize(), ok

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        self.stop_event.set()
        try:
            self.client.close()
        except:
            pass
        event.accept()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QInputDialog

    app = QApplication(sys.argv)
    window = ChatClient()
    window.show()
    sys.exit(app.exec_())
