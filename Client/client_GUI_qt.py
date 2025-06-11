# Giao diện chat nâng cấp giống Messenger bằng PyQt5

import sys
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QMessageBox,
    QListWidget, QListWidgetItem, QInputDialog
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer 

import client_CORE # Import module cốt lõi client
import os # Import thư viện os để kiểm tra sự tồn tại của file

# Signal dispatcher để cập nhật GUI từ luồng khác
class SignalDispatcher(QObject):
    message_received = pyqtSignal(str, str, str, bool) # msg_content, sender_name, timestamp_str, is_private
    connection_status = pyqtSignal(str)
    user_list_updated = pyqtSignal(list)
    message_history_received = pyqtSignal(list) # Thêm signal để nhận lịch sử tin nhắn

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure Chat - Messenger Style")
        self.setGeometry(300, 100, 700, 600) 

        self.username = self.get_initial_username() 
        
        self.dispatcher = SignalDispatcher()
        self.dispatcher.message_received.connect(self.display_message)
        self.dispatcher.connection_status.connect(self.show_connection_status)
        self.dispatcher.user_list_updated.connect(self.update_user_list_gui)
        self.dispatcher.message_history_received.connect(self.display_message_history) # Kết nối signal lịch sử

        # Truyền callback cho client_CORE để lấy username và hiển thị thông báo
        self.client = client_CORE.SSLClient(
            self.receive_message_callback, 
            self.get_current_username
        )
        
        self.init_ui()
        QTimer.singleShot(100, lambda: threading.Thread(target=self.client.connect, daemon=True).start())


    def get_initial_username(self):
        while True:
            username, ok = QInputDialog.getText(self, "Tên người dùng", "Nhập tên người dùng của bạn:")
            if ok and username.strip():
                return username.strip()
            elif not ok: 
                sys.exit(0) 
            else:
                QMessageBox.warning(self, "Tên người dùng", "Tên người dùng không được để trống.")

    def get_current_username(self):
        return self.username

    def init_ui(self):
        main_layout = QHBoxLayout()

        chat_section_layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        name_label = QLabel("Tên bạn:")
        self.name_input = QLineEdit() 
        self.name_input.setText(self.username)
        self.name_input.setReadOnly(True) 
        self.name_input.setFont(QFont("Arial", 10, QFont.Bold)) 
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        name_layout.addStretch(1) 
        chat_section_layout.addLayout(name_layout)

        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_widget.setLayout(self.chat_layout)

        self.chat_area.setWidget(self.chat_widget)
        chat_section_layout.addWidget(self.chat_area)

        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Nhập tin nhắn...")
        self.msg_input.returnPressed.connect(self.send_message)
        send_button = QPushButton("Gửi")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(send_button)

        chat_section_layout.addLayout(input_layout)
        main_layout.addLayout(chat_section_layout, 3) 

        user_list_section_layout = QVBoxLayout()
        user_list_label = QLabel("Người dùng online:")
        user_list_label.setFont(QFont("Arial", 10, QFont.Bold))
        user_list_section_layout.addWidget(user_list_label)

        self.user_list_widget = QListWidget()
        self.user_list_widget.itemClicked.connect(self.select_recipient)
        user_list_section_layout.addWidget(self.user_list_widget)

        self.private_chat_target_label = QLabel("Chat riêng với: (Chung)")
        font = QFont("Arial", 9)
        font.setItalic(True)
        self.private_chat_target_label.setFont(font)
        
        user_list_section_layout.addWidget(self.private_chat_target_label)

        refresh_button = QPushButton("Làm mới danh sách")
        refresh_button.clicked.connect(self.client.request_online_users_list)
        user_list_section_layout.addWidget(refresh_button)

        main_layout.addLayout(user_list_section_layout, 1) 

        self.setLayout(main_layout)

        self.private_chat_recipient = None 

    def send_message(self):
        msg = self.msg_input.text().strip()
        if msg:
            timestamp_str = datetime.now().strftime("%H:%M:%S") # Lấy timestamp hiện tại của client
            if self.private_chat_recipient:
                self.client.send_private_chat_message(self.private_chat_recipient, msg)
                # Client tự hiển thị tin nhắn mình gửi với timestamp hiện tại của client
                self.display_message(msg, sender_name=self.username, timestamp=timestamp_str, is_private=True)
            else:
                self.client.send_chat_message(msg)
                # Client tự hiển thị tin nhắn mình gửi với timestamp hiện tại của client
                self.display_message(msg, sender_name=self.username, timestamp=timestamp_str)
            self.msg_input.clear()

    # Callback từ client_CORE, chạy trong luồng khác
    def receive_message_callback(self, content_str, sender_name="Hệ thống", timestamp="", is_private=False):
        # Phát tín hiệu để cập nhật GUI trên luồng chính
        self.dispatcher.message_received.emit(content_str, sender_name, timestamp, is_private)
    
    def show_connection_status(self, status_message):
        # Hiển thị trạng thái kết nối lên GUI (ví dụ: ở một label riêng hoặc trong khung chat)
        self.display_message(status_message, sender_name="Hệ thống", timestamp=datetime.now().strftime("%H:%M:%S"))
        if "[!] Mất kết nối" in status_message:
            self.name_input.setReadOnly(False) 

    def update_user_list_gui(self, user_list):
        self.user_list_widget.clear()
        for user in user_list:
            item = QListWidgetItem(user)
            self.user_list_widget.addItem(item)
        
    def display_message_history(self, history_list): # Hàm mới để hiển thị lịch sử tin nhắn
        for msg_obj in history_list:
            message_type = msg_obj.get("type")
            sender = msg_obj.get("sender", "Hệ thống")
            content = msg_obj.get("content", "")
            timestamp_unix = msg_obj.get("timestamp")
            
            if timestamp_unix:
                timestamp_str = datetime.fromtimestamp(timestamp_unix).strftime("%H:%M:%S")
            else:
                timestamp_str = datetime.now().strftime("%H:%M:%S")

            # Chỉ hiển thị tin nhắn chat trong lịch sử, bỏ qua tin nhắn hệ thống hoặc tin riêng tư
            if message_type == "chat":
                self.display_message(content, sender_name=sender, timestamp=timestamp_str)
        QTimer.singleShot(10, self.scroll_to_bottom) # Cuộn xuống sau khi hiển thị lịch sử

    def select_recipient(self, item):
        selected_user = item.text()
        if selected_user == self.username:
            QMessageBox.information(self, "Chat riêng", "Bạn không thể chat riêng với chính mình.")
            self.private_chat_recipient = None
            self.private_chat_target_label.setText("Chat riêng với: (Chung)")
        else:
            self.private_chat_recipient = selected_user
            self.private_chat_target_label.setText(f"Chat riêng với: {selected_user}")
            self.msg_input.setPlaceholderText(f"Nhập tin nhắn riêng tư cho {selected_user}...")


    def display_message(self, content_str, sender_name="Hệ thống", timestamp="", is_private=False):
        # is_self_message = (sender_name == self.username) and not is_private
        
        # Để tin nhắn hệ thống luôn hiển thị ở giữa và có màu riêng
        if sender_name == "Hệ thống":
            message_label = QLabel(content_str)
            message_label.setAlignment(Qt.AlignCenter)
            message_label.setStyleSheet("color: gray; font-style: italic; margin-bottom: 5px; margin-top: 5px;")
            self.chat_layout.addWidget(message_label)
            QTimer.singleShot(10, self.scroll_to_bottom)
            return

        is_self_message = (sender_name == self.username) and not is_private
        
        avatar = QLabel()
        avatar_size = 40
        avatar.setFixedSize(avatar_size, avatar_size)

        display_sender_name = sender_name
        if is_self_message: 
            display_sender_name = "Bạn"
        elif is_private: 
            if (sender_name == self.username): 
                 display_sender_name = f"Bạn [Đến {self.private_chat_recipient}]"
            elif sender_name.startswith("[RIÊNG TƯ TỪ]"): 
                display_sender_name = sender_name.replace("[RIÊNG TƯ TỪ] ", "") 
                display_sender_name = f"Từ {display_sender_name}"
            else:
                display_sender_name = f"Từ {sender_name}" 

        name_label = QLabel(display_sender_name)
        name_label.setFont(QFont("Arial", 9, QFont.Bold))
        name_label.setStyleSheet("margin-left: 4px;")
        if is_private: 
            name_label.setStyleSheet("color: #007BFF; margin-left: 4px;")

        message_label = QLabel(content_str) 
        message_label.setWordWrap(True)
        
        bg_color = "#DCF8C6" if is_self_message else "#FFFFFF" 
        if is_private and not is_self_message:
            bg_color = "#E0BBE4" 
        elif is_private and is_self_message:
            bg_color = "#957DAD" 

        message_label.setStyleSheet(
            f"""
            background-color: {bg_color};
            padding: 10px;
            border-radius: 15px;
            max-width: 300px;
            """
        )

        # Sử dụng timestamp được truyền vào
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: gray; font-size: 10px; margin-top: 2px;")
        time_label.setAlignment(Qt.AlignRight)

        # Layout dọc chứa name, message, time
        msg_inner_layout = QVBoxLayout()
        msg_inner_layout.addWidget(name_label)
        msg_inner_layout.addWidget(message_label)
        msg_inner_layout.addWidget(time_label)

        # Layout ngang gồm avatar + nội dung
        msg_layout = QHBoxLayout()
        
        if is_self_message: 
            msg_layout.addStretch()
            msg_layout.addLayout(msg_inner_layout)
        else: 
            if sender_name != "Hệ thống": 
                msg_layout.addWidget(avatar)
            msg_layout.addLayout(msg_inner_layout)
            msg_layout.addStretch()

        frame = QFrame()
        frame.setLayout(msg_layout)
        self.chat_layout.addWidget(frame)
        
        QTimer.singleShot(10, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


    def closeEvent(self, event):
        self.client.disconnect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("\U0001F4E2 Đang mở cửa sổ chat...")
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())

