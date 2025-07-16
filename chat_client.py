import socket
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QMessageBox, QHBoxLayout, QInputDialog
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFont

HOST = '127.0.0.1'
PORT = 10346


class ReceiveThread(QThread):
    new_message = pyqtSignal(str)
    connection_closed = pyqtSignal()

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.running = True

    def run(self):
        while self.running:
            try:
                data = self.client.recv(1024)
                if not data:
                    self.connection_closed.emit()
                    break
                msg = data.decode('utf-8')
                self.new_message.emit(msg)
                if msg == "SHUTDOWN":
                    self.running = False
            except:
                self.connection_closed.emit()
                break

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class Client(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chatroom")
        self.setStyleSheet("background-color: #FDDBE6;")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_thread = None
        self.nickname = None
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QVBoxLayout()

        form_layout = QHBoxLayout()
        self.nick_input = QLineEdit()
        self.nick_input.setPlaceholderText("Nickname")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password (admin only)")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.start_connection)
        form_layout.addWidget(self.nick_input)
        form_layout.addWidget(self.pass_input)
        form_layout.addWidget(self.connect_button)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 12))
        self.chat_display.setStyleSheet("background-color: white; color: black;")

        msg_input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type your message and press Enter (or 'q' to quit)")
        self.msg_input.returnPressed.connect(self.send_message)
        self.msg_input.setStyleSheet("background-color: white; color: black;")
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        msg_input_layout.addWidget(self.msg_input)
        msg_input_layout.addWidget(self.send_button)

        self.tip_label = QLabel("Admin commands: /kick NAME, /ban NAME, /unban NAME")
        self.tip_label.setFont(QFont("Arial", 10))

        self.layout.addLayout(form_layout)
        self.layout.addWidget(self.chat_display)
        self.layout.addLayout(msg_input_layout)
        self.layout.addWidget(self.tip_label)
        self.setLayout(self.layout)

    def start_connection(self):
        nick = self.nick_input.text().strip()
        pwd = self.pass_input.text()

        if not nick:
            QMessageBox.warning(self, "Error", "Nickname required")
            return

        if nick.lower() != "admin" and pwd:
            QMessageBox.warning(self, "Error", "Only Admin should enter a password.")
            return

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.client.connect((HOST, PORT))
            recv = self.client.recv(1024).decode('utf-8')
            if recv == "NICK":
                self.client.send(nick.encode('utf-8'))

            recv = self.client.recv(1024).decode('utf-8')
            if recv == "PASS":
                if not pwd:
                    QMessageBox.warning(self, "Error", "Admin password required.")
                    self.client.close()
                    return
                while True:
                    self.client.send(pwd.encode('utf-8'))
                    resp = self.client.recv(1024).decode('utf-8')
                    if resp == "REFUSE":
                        self.client.close()
                        pwd, ok = QInputDialog.getText(self, "Wrong Password", "Try admin password again:",
                                                       echo=QLineEdit.Password)
                        if not ok or not pwd:
                            return
                        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client.connect((HOST, PORT))
                        self.client.recv(1024)
                        self.client.send(nick.encode('utf-8'))
                        self.client.recv(1024)
                        continue
                    break

            elif recv == "BAN":
                self.chat_display.append("<i>[!] You are banned.</i>")
                self.client.close()
                return

            self.nickname = nick.capitalize()
        except Exception as e:
            self.chat_display.append(f"<i>[!] Connection error: {e}</i>")
            return

        self.chat_display.append(f"<i>You have joined the chat as {self.nickname}.</i>")
        self.connect_button.setEnabled(False)
        self.nick_input.setEnabled(False)
        self.pass_input.setEnabled(False)

        self.receive_thread = ReceiveThread(self.client)
        self.receive_thread.new_message.connect(self.handle_received)
        self.receive_thread.connection_closed.connect(self.handle_disconnected)
        self.receive_thread.start()

    def handle_received(self, msg):
        if msg.startswith("NICK"):
            return

        if "You have been kicked by the Admin!" in msg or "You are banned" in msg:
            QMessageBox.information(self, "Disconnected", msg)
            self.close()
            return

        if (
                msg.startswith("Command was refused")
                or msg.startswith("[!]")
                or "has joined the chat" in msg
                or "has left the chat" in msg
                or "was kicked by Admin!" in msg
                or "has been banned" in msg
                or "has been unbanned" in msg
        ):
            self.chat_display.append(f"<i>{msg}</i>")
        else:
            self.chat_display.append(msg)

    def handle_disconnected(self):
        self.chat_display.append("<i>[!] Disconnected from server.</i>")
        if self.receive_thread:
            self.receive_thread.stop()
        self.connect_button.setEnabled(True)
        self.nick_input.setEnabled(True)
        self.pass_input.setEnabled(True)

    def send_message(self):
        if self.connect_button.isEnabled():
            return

        text = self.msg_input.text().strip()
        if not text:
            return

        if text.lower() == 'q':
            self.client.close()
            self.chat_display.append("<i>You have left the chat.</i>")
            if self.receive_thread:
                self.receive_thread.stop()
            self.close()
            self.connect_button.setEnabled(True)
            self.nick_input.setEnabled(True)
            self.pass_input.setEnabled(True)
            return

        if text.startswith('/'):
            if self.nickname.lower() == "admin":
                if text.startswith('/kick'):
                    self.client.send(f"KICK {text[6:].strip()}".encode('utf-8'))
                elif text.startswith('/ban'):
                    self.client.send(f"BAN {text[5:].strip()}".encode('utf-8'))
                elif text.startswith('/unban'):
                    self.client.send(f"UNBAN {text[7:].strip()}".encode('utf-8'))
                else:
                    self.chat_display.append("<i>Unknown admin command.</i>")
            else:
                self.chat_display.append("<i>Only Admin can use commands.</i>")
        else:
            self.client.send(f"{self.nickname}: {text}".encode('utf-8'))

        self.msg_input.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Client()
    win.resize(600, 600)
    win.show()
    sys.exit(app.exec_())
