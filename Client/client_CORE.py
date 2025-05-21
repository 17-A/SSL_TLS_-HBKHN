# Giao tiếp với server qua socket
import socket
import ssl
import threading

# === CẤU HÌNH SERVER ===
HOST = '100.85.83.9'  # IP Tailscale của server
PORT = 2021           # Cổng server

class SSLClient:
    def __init__(self, display_callback):
        self.display_callback = display_callback
        self.running = True
        self.ssl_socket = None

    def connect(self):
        try:
            # Tạo socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Cấu hình SSL
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # Chấp nhận chứng chỉ tự ký

            # Bọc socket với SSL
            self.ssl_socket = context.wrap_socket(client_socket, server_hostname=HOST)
            self.ssl_socket.connect((HOST, PORT))
            self.display_callback(f"[+] Kết nối đến server {HOST}:{PORT} thành công.")

            # Khởi động luồng nhận dữ liệu
            threading.Thread(target=self.receive_messages, daemon=True).start()

        except Exception as e:
            self.display_callback(f"[!] Lỗi kết nối: {e}")

    def receive_messages(self):
        while self.running:
            try:
                data = self.ssl_socket.recv(1024)
                if not data:
                    self.display_callback("[!] Mất kết nối với server.")
                    break
                message = data.decode()
                self.display_callback(message)
            except Exception as e:
                self.display_callback(f"[!] Lỗi khi nhận: {e}")
                break

    def send(self, message):
        try:
            self.ssl_socket.send(message.encode())
        except Exception as e:
            self.display_callback(f"[!] Không thể gửi: {e}")
