import socket
import ssl
import json
import threading
import time
from datetime import datetime # Import datetime

# Host và Port của server
# Sử dụng '100.85.83.9' nếu bạn đang dùng Tailscale và server cũng dùng IP đó.
# Hoặc '127.0.0.1' nếu bạn chạy server và client trên cùng một máy mà không dùng Tailscale
# hoặc muốn kết nối qua localhost.
HOST = '100.85.83.9'  
PORT = 2021

class SSLClient:
    def __init__(self, display_callback, username_callback=None):
        self.ssl_socket = None
        self.display_callback = display_callback # Hàm để hiển thị tin nhắn lên GUI
        self.username_callback = username_callback # Hàm để lấy username từ GUI
        self.username = None # Tên người dùng sẽ được thiết lập sau khi kết nối
        self.running = True # Cờ để kiểm soát vòng lặp nhận tin nhắn

    def get_context(self):
        # Tạo SSLContext cho client
        # ssl.Purpose.SERVER_AUTH: Client sẽ xác thực server
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        # BẮT BUỘC: Client xác minh chứng chỉ của server (Mutual TLS)
        # Client cần tin tưởng CA đã ký cho chứng chỉ server (hoặc chính chứng chỉ server)
        # Nếu server_cert.pem là self-signed, client sẽ tin tưởng chính server_cert.pem.
        # Đảm bảo đường dẫn này đúng từ thư mục của client_CORE.py.
        context.load_verify_locations(cafile="../Server/cert.pem") 
        context.verify_mode = ssl.CERT_REQUIRED # Bắt buộc xác minh chứng chỉ server

        # Client cung cấp chứng chỉ của mình cho server (Mutual TLS)
        # Đảm bảo đường dẫn này đúng từ thư thư mục của client_CORE.py.
        context.load_cert_chain(certfile="client_cert.pem", keyfile="client_key.pem") 
        # context.load_cert_chain(certfile="fake_client_cert.pem", keyfile="fake_client_key.pem") # check về việc dùng sai chứng chỉ + khóa


        # TẮT hostname verification nếu cert common name không khớp với HOST
        # Chỉ làm điều này trong môi trường phát triển nếu bạn gặp lỗi hostname mismatch
        # context.check_hostname = False

        return context

    def connect(self):
        print("[+] Đang cố gắng kết nối tới server...")
        try:
            # Tạo socket TCP cơ bản
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10) # Timeout cho việc kết nối
            sock.connect((HOST, PORT))
            sock.settimeout(None) # Reset timeout sau khi kết nối

            # Bọc socket TCP với SSL/TLS
            context = self.get_context()
            # server_hostname=HOST: Đây là tên máy chủ mà client mong đợi từ chứng chỉ của server.
            # Rất quan trọng cho việc xác thực TLS. Đảm bảo nó khớp với Common Name (CN) trong cert.pem của server.
            self.ssl_socket = context.wrap_socket(sock, server_hostname=HOST) 
            if self.ssl_socket:
                cipher_info = self.ssl_socket.cipher()
                print(f"[🔐] Kết nối SSL đã thiết lập.")
                print(f"[🔒] Thuật toán mã hóa đang sử dụng: {cipher_info[0]} ({cipher_info[2]}-bit), Giao thức: {cipher_info[1]}")

            print(f"[+] Kết nối đến server thành công.")

            # --- ĐĂNG NHẬP NGƯỜI DÙNG SAU KHI KẾT NỐI TLS ---
            if self.ssl_socket: # Thêm kiểm tra này để đảm bảo socket hợp lệ trước khi gửi
                if self.username_callback:
                    self.username = self.username_callback() # Lấy username từ GUI
                else:
                    self.username = "Guest" # Tên mặc định nếu không có callback
                
                login_message = {
                    "type": "login",
                    "username": self.username,
                    "timestamp": time.time() # Sử dụng Unix timestamp
                }
                self.send_json(login_message) # Gọi send_json để gửi tin nhắn đăng nhập
                print(f"[+] Đã gửi yêu cầu đăng nhập với tên: {self.username}")
            else:
                print(f"[!] Không thể gửi yêu cầu đăng nhập. Kết nối SSL chưa được thiết lập.")

            # Bắt đầu luồng nhận tin nhắn
            threading.Thread(target=self.receive_messages, daemon=True).start()

        except ssl.SSLError as e:
            print(f"[!] Lỗi SSL/TLS khi kết nối: {e}\nĐảm bảo chứng chỉ server được tin cậy và Mutual TLS được cấu hình đúng.")
            self.disconnect()
        except socket.timeout:
            print("[!] Timeout khi kết nối. Server có thể không phản hồi.")
            self.disconnect()
        except socket.error as e:
            print(f"[!] Lỗi socket khi kết nối: {e}\nKiểm tra IP/Port hoặc kết nối mạng.")
            self.disconnect()
        except Exception as e:
            print(f"[!] Lỗi kết nối không xác định: {e}")
            self.disconnect()

    def receive_messages(self):
        while self.running and self.ssl_socket:
            try:
                # Đặt timeout ngắn để có thể thoát vòng lặp khi self.running = False
                self.ssl_socket.settimeout(1) 
                data = self.ssl_socket.recv(4096)
                self.ssl_socket.settimeout(None) # Reset timeout

                if not data:
                    self.display_callback("[!] Server đã ngắt kết nối.")
                    break

                try:
                    message = json.loads(data.decode('utf-8'))
                    message_type = message.get("type", "unknown")
                    sender = message.get("sender", "Hệ thống")
                    content = message.get("content", "")
                    
                    # Chuyển đổi timestamp từ Unix timestamp sang định dạng chuỗi hiển thị
                    timestamp_unix = message.get("timestamp")
                    if timestamp_unix:
                        timestamp_str = datetime.fromtimestamp(timestamp_unix).strftime("%H:%M:%S")
                    else:
                        timestamp_str = datetime.now().strftime("%H:%M:%S") # Fallback nếu không có timestamp

                    if message_type == "user_list":
                        # message['content'] sẽ là một list các username
                        # Chúng ta sẽ không hiển thị tin nhắn hệ thống này trong khung chat nữa, 
                        # thay vào đó chỉ cập nhật danh sách người dùng trên GUI.
                        # self.display_callback(f"[Hệ thống]: Danh sách người dùng online: {', '.join(content)}")
                        # Phát tín hiệu cập nhật danh sách người dùng lên GUI (nếu có dispatcher)
                        if hasattr(self.display_callback.__self__, 'dispatcher'):
                            self.display_callback.__self__.dispatcher.user_list_updated.emit(content)
                    elif message_type == "private_chat":
                        # Tin nhắn riêng tư từ người khác
                        self.display_callback(content, sender_name=f"[RIÊNG TƯ TỪ] {sender}", timestamp=timestamp_str, is_private=True)
                    elif message_type == "system": # XỬ LÝ CẢ TIN NHẮN HỆ THỐNG Ở ĐÂY
                        self.display_callback(content, sender_name=sender, timestamp=timestamp_str) # Hiển thị trong khung chat
                    elif message_type == "chat": # Bao gồm "chat"
                        self.display_callback(content, sender_name=sender, timestamp=timestamp_str)
                    elif message_type == "history": # Xử lý lịch sử tin nhắn
                        if hasattr(self.display_callback.__self__, 'dispatcher'):
                            self.display_callback.__self__.dispatcher.message_history_received.emit(content) # Phát tín hiệu lịch sử

                except json.JSONDecodeError:
                    self.display_callback(f"[!] Nhận được dữ liệu không phải JSON từ server: {data.decode(errors='ignore')}")
                except Exception as e:
                    self.display_callback(f"[!] Lỗi khi xử lý tin nhắn từ server: {e}")

            except socket.timeout:
                continue # Tiếp tục vòng lặp để kiểm tra self.running
            except (socket.error, ssl.SSLError) as e:
                self.display_callback(f"[!] Lỗi socket/SSL khi nhận dữ liệu từ server: {e}")
                break # Ngắt kết nối
            except Exception as e:
                self.display_callback(f"[!] Lỗi không xác định trong luồng nhận tin nhắn: {e}")
                break # Ngắt kết nối
        
        self.disconnect() # Đảm bảo ngắt kết nối khi vòng lặp kết thúc

    def send_chat_message(self, message):
        if not self.ssl_socket:
            self.display_callback("[!] Không kết nối tới server. Không thể gửi tin nhắn.")
            return

        # Kiểm tra xem self.username đã được thiết lập chưa (phòng trường hợp race condition)
        if not self.username and self.username_callback:
            self.username = self.username_callback()
            if not self.username:
                self.username = "Guest" # Fallback nếu vẫn không có tên

        chat_message = {
            "type": "chat",  # Đảm bảo type là "chat"
            "sender": self.username,
            "content": message
            # Timestamp sẽ được server thêm vào để đảm bảo đồng bộ
        }
        self.send_json(chat_message)
        # self.display_callback(f"[+] Đã gửi tin nhắn chat: {message}") # Có thể bỏ dòng này nếu GUI tự hiển thị tin nhắn đã gửi

    def send_private_chat_message(self, recipient_username, message):
        if not self.ssl_socket:
            self.display_callback("[!] Không kết nối tới server. Không thể gửi tin nhắn riêng tư.")
            return

        if not self.username and self.username_callback:
            self.username = self.username_callback()
            if not self.username:
                self.username = "Guest"

        private_message = {
            "type": "private_chat",
            "sender": self.username,
            "receiver": recipient_username,
            "content": message
            # Timestamp sẽ được server thêm vào để đảm bảo đồng bộ
        }
        self.send_json(private_message)
        # GUI sẽ tự hiển thị tin nhắn đã gửi, nên không cần display_callback ở đây

    def request_online_users_list(self):
        if not self.ssl_socket:
            self.display_callback("[!] Không kết nối tới server. Không thể yêu cầu danh sách người dùng.")
            return

        request_message = {
            "type": "request_user_list",
            "sender": self.username if self.username else "Guest"
            # Timestamp không cần thiết cho request này
        }
        self.send_json(request_message)
        print("[+] Đã yêu cầu danh sách người dùng online từ server.")

    def send_json(self, data):
        """Gửi dữ liệu JSON qua SSL socket."""
        try:
            json_data = json.dumps(data)
            self.ssl_socket.sendall(json_data.encode('utf-8'))
            print(f"[CLIENT-DEBUG] Đã gửi JSON: {json_data}") # RẤT QUAN TRỌNG: DÒNG DEBUG LOG NÀY
        except (socket.error, ssl.SSLError) as e:
            self.display_callback(f"[!] Lỗi khi gửi dữ liệu: {e}")
            self.disconnect() # Ngắt kết nối nếu lỗi gửi
        except Exception as e:
            self.display_callback(f"[!] Lỗi không xác định khi gửi dữ liệu: {e}")
            self.disconnect()

    def disconnect(self):
        self.running = False # Đặt cờ để dừng luồng nhận tin nhắn
        if self.ssl_socket:
            try:
                self.ssl_socket.shutdown(socket.SHUT_RDWR)
                self.ssl_socket.close()
                print("[!] Đã ngắt kết nối với server.")
            except Exception as e:
                print(f"[-] Lỗi khi đóng socket: {e}")
            finally:
                self.ssl_socket = None

