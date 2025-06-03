# # Giao diện chat nâng cấp giống Messenger bằng PyQt5

# import sys
# import threading
# from datetime import datetime
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QLabel, QLineEdit, QPushButton,
#     QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QMessageBox,
#     QListWidget, QListWidgetItem, QInputDialog
# )
# from PyQt5.QtGui import QPixmap, QFont, QColor
# from PyQt5.QtCore import Qt, pyqtSignal, QObject
# import client_CORE # Import module cốt lõi client
# import os # Import thư viện os để kiểm tra sự tồn tại của file

# # Signal dispatcher để cập nhật GUI từ luồng khác
# class SignalDispatcher(QObject):
#     message_received = pyqtSignal(str, str, str, bool) # msg_content, sender_name, timestamp, is_private
#     connection_status = pyqtSignal(str)
#     user_list_updated = pyqtSignal(list)

# class ChatWindow(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Secure Chat - Messenger Style")
#         self.setGeometry(300, 100, 700, 600) # Tăng chiều rộng để có danh sách người dùng

#         self.username = self.get_initial_username() # Lấy tên người dùng khi khởi động
#         # self.avatar_path = "client/resources/avatar.png"  # Avatar của chính mình - Bỏ comment hoặc xóa nếu không dùng
#         # self.default_avatar_path = "client/resources/avatar_default.png" # Avatar mặc định cho người khác - Bỏ comment hoặc xóa nếu không dùng
        
#         # === KHÔNG CẦN KIỂM TRA FILE AVATAR NỮA NẾU BẠN KHÔNG SỬ DỤNG CHÚNG ===
#         # import os
#         # if not os.path.exists(self.avatar_path):
#         #     QMessageBox.warning(self, "Lỗi File", f"Không tìm thấy file avatar: {self.avatar_path}")
#         #     # Có thể đặt một avatar mặc định khác hoặc yêu cầu người dùng chọn
#         # if not os.path.exists(self.default_avatar_path):
#         #     QMessageBox.warning(self, "Lỗi File", f"Không tìm thấy file avatar mặc định: {self.default_avatar_path}")


#         self.dispatcher = SignalDispatcher()
#         self.dispatcher.message_received.connect(self.display_message)
#         self.dispatcher.connection_status.connect(self.show_connection_status)
#         self.dispatcher.user_list_updated.connect(self.update_user_list_gui)

#         # Truyền callback cho client_CORE để lấy username
#         self.client = client_CORE.SSLClient(self.receive_message_callback, self.get_current_username)
        
#         self.init_ui()
#         # Khởi động kết nối trong một luồng riêng
#         threading.Thread(target=self.client.connect, daemon=True).start()

#     def get_initial_username(self):
#         # Yêu cầu người dùng nhập tên khi khởi động ứng dụng
#         while True:
#             username, ok = QInputDialog.getText(self, "Tên người dùng", "Nhập tên người dùng của bạn:")
#             if ok and username.strip():
#                 return username.strip()
#             elif not ok: # Nếu người dùng nhấn Cancel
#                 sys.exit(0) # Thoát ứng dụng
#             else:
#                 QMessageBox.warning(self, "Tên người dùng", "Tên người dùng không được để trống.")


#     def get_current_username(self):
#         return self.username

#     def init_ui(self):
#         main_layout = QHBoxLayout()

#         # Phần chat chính (bên trái)
#         chat_section_layout = QVBoxLayout()

#         # Ô nhập tên (có thể chỉnh sửa nhưng không bắt buộc)
#         name_layout = QHBoxLayout()
#         name_label = QLabel("Tên bạn:")
#         self.name_input = QLineEdit()
#         self.name_input.setText(self.username)
#         self.name_input.editingFinished.connect(self.update_username)
#         self.name_input.setEnabled(False) # Tắt chỉnh sửa tên sau khi đăng nhập
#         name_layout.addWidget(name_label)
#         name_layout.addWidget(self.name_input)
#         chat_section_layout.addLayout(name_layout)

#         # Scroll area cho khung chat
#         self.chat_area = QScrollArea()
#         self.chat_area.setWidgetResizable(True)

#         self.chat_widget = QWidget()
#         self.chat_layout = QVBoxLayout()
#         self.chat_layout.setAlignment(Qt.AlignTop)
#         self.chat_widget.setLayout(self.chat_layout)

#         self.chat_area.setWidget(self.chat_widget)
#         chat_section_layout.addWidget(self.chat_area)

#         # Khung nhập và nút gửi
#         input_layout = QHBoxLayout()
#         self.msg_input = QLineEdit()
#         self.msg_input.setPlaceholderText("Nhập tin nhắn...")
#         self.msg_input.returnPressed.connect(self.send_message)
#         send_button = QPushButton("Gửi")
#         send_button.clicked.connect(self.send_message)
#         input_layout.addWidget(self.msg_input)
#         input_layout.addWidget(send_button)

#         chat_section_layout.addLayout(input_layout)
#         main_layout.addLayout(chat_section_layout, 3) # Chiếm 3 phần chiều rộng

#         # Phần danh sách người dùng (bên phải)
#         user_list_section_layout = QVBoxLayout()
#         user_list_label = QLabel("Người dùng online:")
#         user_list_label.setFont(QFont("Arial", 10, QFont.Bold))
#         user_list_section_layout.addWidget(user_list_label)

#         self.user_list_widget = QListWidget()
#         self.user_list_widget.itemClicked.connect(self.select_recipient)
#         user_list_section_layout.addWidget(self.user_list_widget)

#         self.private_chat_target_label = QLabel("Chat riêng với: (Chung)")
#         font = QFont("Arial", 9)
#         font.setItalic(True)
#         self.private_chat_target_label.setFont(font)    

#         user_list_section_layout.addWidget(self.private_chat_target_label)

#         refresh_button = QPushButton("Làm mới danh sách")
#         refresh_button.clicked.connect(self.client.request_online_users_list)
#         user_list_section_layout.addWidget(refresh_button)

#         main_layout.addLayout(user_list_section_layout, 1) # Chiếm 1 phần chiều rộng

#         self.setLayout(main_layout)

#         self.private_chat_recipient = None # Không có người nhận riêng tư ban đầu


#     def update_username(self):
#         # Tên người dùng chỉ được thiết lập ban đầu, không thay đổi được sau đó
#         pass # Không làm gì khi chỉnh sửa xong ô tên


#     def send_message(self):
#         msg = self.msg_input.text().strip()
#         if msg:
#             if self.private_chat_recipient:
#                 self.client.send_private_chat_message(self.private_chat_recipient, msg)
#                 # Hiển thị tin nhắn của mình trong khung chat (có thể khác với khi nhận được từ server)
#                 formatted = f"[RIÊNG TƯ GỬI ĐI] {self.username} -> {self.private_chat_recipient}: {msg}"
#                 self.display_message(formatted, sender_name=self.username, timestamp=datetime.now().strftime("%H:%M:%S"), is_private=True)
#             else:
#                 self.client.send_chat_message(msg)
#                 # Hiển thị tin nhắn của mình trong khung chat
#                 formatted = f"{self.username}: {msg}"
#                 self.display_message(formatted, sender_name=self.username, timestamp=datetime.now().strftime("%H:%M:%S"))
#             self.msg_input.clear()

#     # Callback từ client_CORE, chạy trong luồng khác
#     def receive_message_callback(self, content_str, sender_name="Hệ thống", timestamp="", is_private=False):
#         # Phát tín hiệu để cập nhật GUI trên luồng chính
#         self.dispatcher.message_received.emit(content_str, sender_name, timestamp, is_private)

#     def show_connection_status(self, status_message):
#         # Hiển thị trạng thái kết nối lên GUI (ví dụ: ở một label riêng hoặc trong khung chat)
#         self.display_message(status_message, sender_name="Hệ thống", timestamp=datetime.now().strftime("%H:%M:%S"))
#         if "[!] Mất kết nối" in status_message:
#             self.name_input.setEnabled(True) # Cho phép người dùng nhập lại tên nếu muốn kết nối lại
#             # Có thể thêm nút kết nối lại
#             # self.client.disconnect() # Đảm bảo đã ngắt kết nối hoàn toàn

#     def update_user_list_gui(self, user_list):
#         self.user_list_widget.clear()
#         for user in user_list:
#             item = QListWidgetItem(user)
#             self.user_list_widget.addItem(item)
#         self.display_message(f"[Hệ thống]: Danh sách người dùng được cập nhật.", sender_name="Hệ thống", timestamp=datetime.now().strftime("%H:%M:%S"))


#     def select_recipient(self, item):
#         selected_user = item.text()
#         if selected_user == self.username:
#             QMessageBox.information(self, "Chat riêng", "Bạn không thể chat riêng với chính mình.")
#             self.private_chat_recipient = None
#             self.private_chat_target_label.setText("Chat riêng với: (Chung)")
#         else:
#             self.private_chat_recipient = selected_user
#             self.private_chat_target_label.setText(f"Chat riêng với: {selected_user}")
#             self.msg_input.setPlaceholderText(f"Nhập tin nhắn riêng tư cho {selected_user}...")


#     def display_message(self, content_str, sender_name="Hệ thống", timestamp="", is_private=False):
#         # Kiểm tra xem có phải là tin nhắn từ chính mình không
#         is_self_message = (sender_name == self.username) and not is_private
        
#         # === THAY ĐỔI ĐỂ KHÔNG YÊU CẦU FILE AVATAR ===
#         avatar = QLabel()
#         # Thay vì cố gắng tải pixmap, chỉ cần tạo một QLabel trống có kích thước cố định
#         # để giữ bố cục. Bạn có thể điều chỉnh kích thước nếu muốn.
#         avatar_size = 40
#         avatar.setFixedSize(avatar_size, avatar_size)
#         # Tùy chọn: Thêm một khung hoặc màu nền cho 'avatar' trống
#         # avatar.setStyleSheet("border: 1px solid lightgray; border-radius: 20px;")
#         # Nếu bạn muốn hiển thị chữ cái đầu tên thay avatar:
#         # avatar.setText(sender_name[0].upper() if sender_name else "?")
#         # avatar.setAlignment(Qt.AlignCenter)
#         # avatar.setFont(QFont("Arial", 16, QFont.Bold))
#         # avatar.setStyleSheet("background-color: #A9D1C2; color: white; border-radius: 20px;")


#         # Tên người gửi
#         name_label = QLabel(sender_name)
#         name_label.setFont(QFont("Arial", 9, QFont.Bold))
#         name_label.setStyleSheet("margin-left: 4px;")
#         if is_private: # Đánh dấu tin nhắn riêng tư
#             name_label.setStyleSheet("color: #007BFF; margin-left: 4px;") # Màu xanh dương cho tên người gửi

#         # Tin nhắn
#         message_label = QLabel(content_str)
#         message_label.setWordWrap(True)
        
#         # Định dạng màu nền và góc bo cho tin nhắn
#         bg_color = "#DCF8C6" if is_self_message else "#FFFFFF" # Xanh lá cho mình, trắng cho người khác
#         if is_private and not is_self_message:
#             bg_color = "#E0BBE4" # Màu tím nhạt cho tin nhắn riêng tư nhận được
#         elif is_private and is_self_message:
#             bg_color = "#957DAD" # Màu tím đậm hơn cho tin nhắn riêng tư gửi đi

#         message_label.setStyleSheet(
#             f"""
#             background-color: {bg_color};
#             padding: 10px;
#             border-radius: 15px;
#             max-width: 300px;
#             """
#         )

#         # Thời gian gửi
#         if not timestamp: # Nếu không có timestamp từ server, dùng thời gian hiện tại
#             timestamp = datetime.now().strftime("%H:%M:%S")
#         time_label = QLabel(timestamp)
#         time_label.setStyleSheet("color: gray; font-size: 10px; margin-top: 2px;")
#         time_label.setAlignment(Qt.AlignRight)

#         # Layout dọc chứa name, message, time
#         msg_inner_layout = QVBoxLayout()
#         msg_inner_layout.addWidget(name_label)
#         msg_inner_layout.addWidget(message_label)
#         msg_inner_layout.addWidget(time_label)

#         # Layout ngang gồm avatar + nội dung
#         msg_layout = QHBoxLayout()
        
#         # === ĐIỀU CHỈNH BỐ CỤC ĐỂ HIỂN THỊ HOẶC ẨN AVATAR ===
#         if is_self_message: # Tin nhắn của mình nằm bên phải
#             msg_layout.addStretch()
#             msg_layout.addLayout(msg_inner_layout)
#             # Không thêm avatar vào đây nếu bạn muốn ẩn hoàn toàn hoặc chỉ hiển thị cho người khác
#             # msg_layout.addWidget(avatar) # Nếu bạn muốn avatar của mình bên phải
#         else: # Tin nhắn của người khác nằm bên trái
#             if sender_name != "Hệ thống": # Không hiển thị avatar cho hệ thống
#                 msg_layout.addWidget(avatar)
#             msg_layout.addLayout(msg_inner_layout)
#             msg_layout.addStretch()
#         # === KẾT THÚC ĐIỀU CHỈNH BỐ CỤC AVATAR ===


#         frame = QFrame()
#         frame.setLayout(msg_layout)
#         self.chat_layout.addWidget(frame)

#         # Cuộn xuống cuối cùng
#         # Cần sử dụng QTimer.singleShot hoặc processEvents để đảm bảo cuộn sau khi layout được cập nhật
#         QApplication.processEvents()
#         self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())


#     def closeEvent(self, event):
#         # Đảm bảo ngắt kết nối khi đóng ứng dụng
#         self.client.disconnect()
#         event.accept()

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     print("\U0001F4E2 Đang mở cửa sổ chat...")
#     window = ChatWindow()
#     window.show()
#     sys.exit(app.exec_())


# Giao diện chat nâng cấp giống Messenger bằng PyQt5

# Giao diện chat nâng cấp giống Messenger bằng PyQt5

import sys
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QMessageBox,
    QListWidget, QListWidgetItem, QInputDialog
)
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer # Thêm QTimer

import client_CORE # Import module cốt lõi client
import os # Import thư viện os để kiểm tra sự tồn tại của file

# Signal dispatcher để cập nhật GUI từ luồng khác
class SignalDispatcher(QObject):
    message_received = pyqtSignal(str, str, str, bool) # msg_content, sender_name, timestamp, is_private
    connection_status = pyqtSignal(str)
    user_list_updated = pyqtSignal(list)

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure Chat - Messenger Style")
        self.setGeometry(300, 100, 700, 600) # Tăng chiều rộng để có danh sách người dùng

        self.username = self.get_initial_username() # Lấy tên người dùng khi khởi động
        
        # === KHÔNG CẦN KIỂM TRA FILE AVATAR NỮA NẾU BẠN KHÔNG SỬ DỤNG CHÚNG ===
        # self.avatar_path = "client/resources/avatar.png"  
        # self.default_avatar_path = "client/resources/avatar_default.png" 
        # import os
        # if not os.path.exists(self.avatar_path):
        #     QMessageBox.warning(self, "Lỗi File", f"Không tìm thấy file avatar: {self.avatar_path}")
        # if not os.path.exists(self.default_avatar_path):
        #     QMessageBox.warning(self, "Lỗi File", f"Không tìm thấy file avatar mặc định: {self.default_avatar_path}")

        self.dispatcher = SignalDispatcher()
        self.dispatcher.message_received.connect(self.display_message)
        self.dispatcher.connection_status.connect(self.show_connection_status)
        self.dispatcher.user_list_updated.connect(self.update_user_list_gui)

        # Truyền callback cho client_CORE để lấy username
        self.client = client_CORE.SSLClient(self.receive_message_callback, self.get_current_username)
        
        self.init_ui()
        # Khởi động kết nối trong một luồng riêng, sau một khoảng thời gian ngắn
        # để GUI có thời gian khởi tạo hoàn chỉnh.
        QTimer.singleShot(100, lambda: threading.Thread(target=self.client.connect, daemon=True).start())


    def get_initial_username(self):
        # Yêu cầu người dùng nhập tên khi khởi động ứng dụng
        while True:
            username, ok = QInputDialog.getText(self, "Tên người dùng", "Nhập tên người dùng của bạn:")
            if ok and username.strip():
                return username.strip()
            elif not ok: # Nếu người dùng nhấn Cancel
                sys.exit(0) # Thoát ứng dụng
            else:
                QMessageBox.warning(self, "Tên người dùng", "Tên người dùng không được để trống.")

    def get_current_username(self):
        return self.username

    def init_ui(self):
        main_layout = QHBoxLayout()

        # Phần chat chính (bên trái)
        chat_section_layout = QVBoxLayout()

        # Ô nhập tên (hiển thị, không cho sửa)
        name_layout = QHBoxLayout()
        name_label = QLabel("Tên bạn:")
        self.name_input = QLineEdit() # Giữ lại QLineEdit để có thể thiết lập text
        self.name_input.setText(self.username)
        self.name_input.setReadOnly(True) # Đặt là read-only để không cho sửa
        self.name_input.setFont(QFont("Arial", 10, QFont.Bold)) # Đặt font cho QLineEdit
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        name_layout.addStretch(1) # Đẩy tên sang trái
        chat_section_layout.addLayout(name_layout)

        # Scroll area cho khung chat
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_widget.setLayout(self.chat_layout)

        self.chat_area.setWidget(self.chat_widget)
        chat_section_layout.addWidget(self.chat_area)

        # Khung nhập và nút gửi
        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Nhập tin nhắn...")
        self.msg_input.returnPressed.connect(self.send_message)
        send_button = QPushButton("Gửi")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(send_button)

        chat_section_layout.addLayout(input_layout)
        main_layout.addLayout(chat_section_layout, 3) # Chiếm 3 phần chiều rộng

        # Phần danh sách người dùng (bên phải)
        user_list_section_layout = QVBoxLayout()
        user_list_label = QLabel("Người dùng online:")
        user_list_label.setFont(QFont("Arial", 10, QFont.Bold))
        user_list_section_layout.addWidget(user_list_label)

        self.user_list_widget = QListWidget()
        self.user_list_widget.itemClicked.connect(self.select_recipient)
        user_list_section_layout.addWidget(self.user_list_widget)

        self.private_chat_target_label = QLabel("Chat riêng với: (Chung)")
        # SỬA LỖI QFont.Italic Ở ĐÂY
        font = QFont("Arial", 9)
        font.setItalic(True)
        self.private_chat_target_label.setFont(font)
        
        user_list_section_layout.addWidget(self.private_chat_target_label)

        refresh_button = QPushButton("Làm mới danh sách")
        refresh_button.clicked.connect(self.client.request_online_users_list)
        user_list_section_layout.addWidget(refresh_button)

        main_layout.addLayout(user_list_section_layout, 1) # Chiếm 1 phần chiều rộng

        self.setLayout(main_layout)

        self.private_chat_recipient = None # Không có người nhận riêng tư ban đầu


    def update_username(self):
        # Hàm này không còn được sử dụng vì tên được lấy từ QInputDialog lúc đầu và QLineEdit là ReadOnly.
        pass


    def send_message(self):
        msg = self.msg_input.text().strip()
        if msg:
            if self.private_chat_recipient:
                self.client.send_private_chat_message(self.private_chat_recipient, msg)
                # Khi gửi tin nhắn riêng tư, tự hiển thị với content thuần túy
                self.display_message(msg, sender_name=self.username, is_private=True) 
            else:
                self.client.send_chat_message(msg)
                # Khi gửi tin nhắn chung, tự hiển thị với content thuần túy
                self.display_message(msg, sender_name=self.username) 
            self.msg_input.clear()

    # Callback từ client_CORE, chạy trong luồng khác
    def receive_message_callback(self, content_str, sender_name="Hệ thống", timestamp="", is_private=False):
        # Phát tín hiệu để cập nhật GUI trên luồng chính
        self.dispatcher.message_received.emit(content_str, sender_name, timestamp, is_private)

    def show_connection_status(self, status_message):
        # Hiển thị trạng thái kết nối lên GUI (ví dụ: ở một label riêng hoặc trong khung chat)
        self.display_message(status_message, sender_name="Hệ thống", timestamp=datetime.now().strftime("%H:%M:%S"))
        if "[!] Mất kết nối" in status_message:
            self.name_input.setReadOnly(False) # Cho phép người dùng sửa tên nếu muốn kết nối lại
            # Có thể thêm nút kết nối lại
            # self.client.disconnect() # Đảm bảo đã ngắt kết nối hoàn toàn

    def update_user_list_gui(self, user_list):
        self.user_list_widget.clear()
        for user in user_list:
            item = QListWidgetItem(user)
            self.user_list_widget.addItem(item)
        self.display_message(f"[Hệ thống]: Danh sách người dùng được cập nhật.", sender_name="Hệ thống", timestamp=datetime.now().strftime("%H:%M:%S"))


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
        # Kiểm tra xem có phải là tin nhắn từ chính mình không
        is_self_message = (sender_name == self.username) and not is_private
        
        # === THAY ĐỔI ĐỂ KHÔNG YÊU CẦU FILE AVATAR ===
        avatar = QLabel()
        avatar_size = 40
        avatar.setFixedSize(avatar_size, avatar_size)
        # Tùy chọn: Thêm một khung hoặc màu nền cho 'avatar' trống
        # avatar.setStyleSheet("border: 1px solid lightgray; border-radius: 20px;")
        # Nếu bạn muốn hiển thị chữ cái đầu tên thay avatar:
        # avatar.setText(sender_name[0].upper() if sender_name else "?")
        # avatar.setAlignment(Qt.AlignCenter)
        # avatar.setFont(QFont("Arial", 16, QFont.Bold))
        # avatar.setStyleSheet("background-color: #A9D1C2; color: white; border-radius: 20px;")


        # Tên người gửi
        # Logic này được sửa để chỉ hiển thị tên nếu nó khác với tên của mình
        # và không phải là tin nhắn hệ thống
        display_sender_name = sender_name
        if sender_name == self.username and not is_private: # Tin của mình gửi chat chung
            display_sender_name = "Bạn"
        elif sender_name == "Hệ thống":
            display_sender_name = "Hệ thống"
        elif is_private: # Tin nhắn riêng tư đến hoặc đi
             # Nếu là tin riêng tư được gửi đi (is_self_message=True)
             # thì sender_name vẫn là self.username, ta cần kiểm soát định dạng.
             # Nếu là tin riêng tư từ người khác (is_self_message=False)
             # thì sender_name là tên người gửi.
            if is_self_message: # Nếu là tin riêng tư của mình gửi đi
                 display_sender_name = f"Bạn [Đến {self.private_chat_recipient}]"
                 # Nếu tin nhắn từ client_CORE mà is_private = True và sender_name là tên người gửi ban đầu
                 # thì display_sender_name sẽ là tên người gửi.
            elif sender_name.startswith("[RIÊNG TƯ TỪ]"): # Nếu đã được định dạng từ client_CORE
                display_sender_name = sender_name.replace("[RIÊNG TƯ TỪ] ", "") # Xóa prefix nếu client_CORE đã thêm
                display_sender_name = f"Từ {display_sender_name}"
            else:
                display_sender_name = f"Từ {sender_name}" # Hoặc chỉ là sender_name

        name_label = QLabel(display_sender_name)
        name_label.setFont(QFont("Arial", 9, QFont.Bold))
        name_label.setStyleSheet("margin-left: 4px;")
        if is_private: # Đánh dấu tin nhắn riêng tư
            name_label.setStyleSheet("color: #007BFF; margin-left: 4px;") # Màu xanh dương cho tên người gửi

        # Tin nhắn
        message_label = QLabel(content_str) # Content_str giờ chỉ là nội dung thuần túy
        message_label.setWordWrap(True)
        
        # Định dạng màu nền và góc bo cho tin nhắn
        bg_color = "#DCF8C6" if is_self_message else "#FFFFFF" # Xanh lá cho mình, trắng cho người khác
        if is_private and not is_self_message:
            bg_color = "#E0BBE4" # Màu tím nhạt cho tin nhắn riêng tư nhận được
        elif is_private and is_self_message:
            bg_color = "#957DAD" # Màu tím đậm hơn cho tin nhắn riêng tư gửi đi

        message_label.setStyleSheet(
            f"""
            background-color: {bg_color};
            padding: 10px;
            border-radius: 15px;
            max-width: 300px;
            """
        )

        # Thời gian gửi
        if not timestamp: # Nếu không có timestamp từ server, dùng thời gian hiện tại
            timestamp = datetime.now().strftime("%H:%M:%S")
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
        
        # === ĐIỀU CHỈNH BỐ CỤC ĐỂ HIỂN THỊ HOẶC ẨN AVATAR ===
        if is_self_message: # Tin nhắn của mình nằm bên phải
            msg_layout.addStretch()
            msg_layout.addLayout(msg_inner_layout)
            # Không thêm avatar vào đây nếu bạn muốn ẩn hoàn toàn hoặc chỉ hiển thị cho người khác
            # msg_layout.addWidget(avatar) # Nếu bạn muốn avatar của mình bên phải
        else: # Tin nhắn của người khác nằm bên trái
            if sender_name != "Hệ thống": # Không hiển thị avatar cho hệ thống
                msg_layout.addWidget(avatar)
            msg_layout.addLayout(msg_inner_layout)
            msg_layout.addStretch()
        # === KẾT THÚC ĐIỀU CHỈNH BỐ CỤC AVATAR ===


        frame = QFrame()
        frame.setLayout(msg_layout)
        self.chat_layout.addWidget(frame)
        
        # === Cải thiện việc tự động cuộn xuống cuối ===
        # Sử dụng QTimer.singleShot để đảm bảo layout đã được cập nhật hoàn chỉnh
        # trước khi cố gắng cuộn. Một độ trễ nhỏ (ví dụ 10ms) thường là đủ.
        QTimer.singleShot(10, self.scroll_to_bottom)

    # Đặt hàm scroll_to_bottom Ở ĐÂY, ngang hàng với các phương thức khác của class ChatWindow
    def scroll_to_bottom(self):
        """Hàm trợ giúp để cuộn thanh cuộn dọc xuống cuối."""
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


    def closeEvent(self, event):
        # Đảm bảo ngắt kết nối khi đóng ứng dụng
        self.client.disconnect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("\U0001F4E2 Đang mở cửa sổ chat...")
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())