# Giao diện chat nâng cấp giống Messenger bằng PyQt5

import sys
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QScrollArea, QFrame
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
import client_CORE

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure Chat - Messenger Style")
        self.setGeometry(300, 100, 500, 600)

        self.username = "Bạn"
        self.avatar_path = "client/resources/avatar.png"  # Avatar của chính mình

        self.client = client_CORE.SSLClient(self.receive_message)

        self.init_ui()
        threading.Thread(target=self.client.connect, daemon=True).start()

    def init_ui(self):
        layout = QVBoxLayout()

        # Ô nhập tên
        name_layout = QHBoxLayout()
        name_label = QLabel("Tên bạn:")
        self.name_input = QLineEdit()
        self.name_input.setText(self.username)
        self.name_input.editingFinished.connect(self.update_username)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Scroll area cho khung chat
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_widget.setLayout(self.chat_layout)

        self.chat_area.setWidget(self.chat_widget)
        layout.addWidget(self.chat_area)

        # Khung nhập và nút gửi
        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Nhập tin nhắn...")
        self.msg_input.returnPressed.connect(self.send_message)
        send_button = QPushButton("Gửi")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(send_button)

        layout.addLayout(input_layout)
        self.setLayout(layout)

    def update_username(self):
        self.username = self.name_input.text().strip()

    def send_message(self):
        msg = self.msg_input.text()
        if msg:
            formatted = f"{self.username}: {msg}"
            self.client.send(formatted)
            self.display_message(formatted)
            self.msg_input.clear()

    def receive_message(self, msg):
        print(f"[GUI] Nhận từ server: {msg}")
        try:
            name, content = msg.split(":", 1)
        except ValueError:
            self.display_message(msg)
            return
        name = name.strip()
        print(f"[So sánh] name='{name}' vs self.username='{self.username}'")
        if name != self.username:
            self.display_message(msg)

    def display_message(self, msg):
        try:
            name, content = msg.split(":", 1)
        except ValueError:
            name, content = "Hệ thống", msg
        name = name.strip()
        content = content.strip()

        # Avatar
        avatar = QLabel()
        avatar_path = self.avatar_path if name == self.username else "client/resources/avatar_default.png"
        avatar.setPixmap(QPixmap(avatar_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Tên người gửi
        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", 9, QFont.Bold))
        name_label.setStyleSheet("margin-left: 4px;")

        # Tin nhắn
        message_label = QLabel(content)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(
            """
            background-color: #DCF8C6;
            padding: 10px;
            border-radius: 15px;
            max-width: 300px;
            """ if name == self.username else
            """
            background-color: #FFFFFF;
            padding: 10px;
            border-radius: 15px;
            max-width: 300px;
            """
        )

        # Thời gian gửi
        time = datetime.now().strftime("%H:%M")
        time_label = QLabel(time)
        time_label.setStyleSheet("color: gray; font-size: 10px; margin-top: 2px;")
        time_label.setAlignment(Qt.AlignRight)

        # Layout dọc chứa name, message, time
        msg_inner_layout = QVBoxLayout()
        msg_inner_layout.addWidget(name_label)
        msg_inner_layout.addWidget(message_label)
        msg_inner_layout.addWidget(time_label)

        # Layout ngang gồm avatar + nội dung
        msg_layout = QHBoxLayout()
        if name == self.username:
            msg_layout.addStretch()
            msg_layout.addLayout(msg_inner_layout)
            msg_layout.addWidget(avatar)
        else:
            msg_layout.addWidget(avatar)
            msg_layout.addLayout(msg_inner_layout)
            msg_layout.addStretch()

        frame = QFrame()
        frame.setLayout(msg_layout)
        self.chat_layout.addWidget(frame)

        # Cuộn xuống cuối cùng
        QApplication.processEvents()
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("\U0001F4E2 Đang mở cửa sổ chat...")
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())