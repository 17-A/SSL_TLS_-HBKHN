import socket
import ssl
import threading
import json
import time

# Cấu hình Host và Port
HOST = '0.0.0.0' # Lắng nghe trên tất cả các interface
PORT = 2021

# Danh sách người dùng online và lock để đồng bộ hóa truy cập
online_users = {}
online_users_lock = threading.Lock()

# Cờ để kiểm soát việc dừng server
server_running = True

def get_ssl_context(is_server=True):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH if is_server else ssl.Purpose.SERVER_AUTH)
    
    if is_server:
        # Cấu hình server để sử dụng chứng chỉ và khóa riêng của nó
        context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

        # Cấu hình server để yêu cầu và xác minh chứng chỉ của client (Mutual TLS)
        # Server cần tin tưởng CA đã ký cho chứng chỉ client (hoặc chính chứng chỉ client nếu self-signed)
        # Đường dẫn này phải đúng từ thư mục của server.py
        context.load_verify_locations(cafile="../Client/client_cert.pem") 
        context.verify_mode = ssl.CERT_REQUIRED # Bắt buộc xác minh chứng chỉ client
    else:
        # Cấu hình client (đã được xử lý trong client_CORE.py)
        pass # Không cần xử lý ở đây cho server

    # Khuyến nghị: Sử dụng các phiên bản TLS an toàn hơn
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context

def notify_user_status(username, status):
    """Gửi thông báo trạng thái người dùng (online/offline) tới tất cả các client."""
    status_message = {
        "type": "system",
        "sender": "Hệ thống",
        "content": f"Người dùng '{username}' đã {status}.",
        "timestamp": time.strftime("%H:%M:%S", time.gmtime())
    }
    broadcast(status_message) # Gửi tới tất cả, bao gồm cả người vừa online/offline

def send_online_users_list(connstream, target_username):
    """Gửi danh sách người dùng online hiện tại tới một client cụ thể."""
    with online_users_lock:
        users = list(online_users.keys())
    
    user_list_message = {
        "type": "user_list",
        "sender": "Hệ thống",
        "content": users,
        "timestamp": time.strftime("%H:%M:%S", time.gmtime())
    }
    try:
        connstream.sendall(json.dumps(user_list_message).encode('utf-8'))
        print(f"[+] Đã gửi danh sách người dùng online tới {target_username}.")
    except (socket.error, ssl.SSLError, Exception) as e:
        print(f"[-] Lỗi khi gửi danh sách người dùng tới {target_username}: {e}")

def broadcast(message_obj, sender_conn=None):
    """Gửi một tin nhắn JSON tới tất cả các client online."""
    message_json = json.dumps(message_obj)
    message_bytes = message_json.encode('utf-8')

    print(f"[DEBUG] Bắt đầu broadcast. Nội dung: {message_obj.get('content', '')} từ {message_obj.get('sender', 'Unknown')}") # DEBUG LOG
    with online_users_lock:
        print(f"[DEBUG] Số lượng người dùng online trong lock: {len(online_users)}") # DEBUG LOG
        
        sender_username_for_debug = "Không rõ"
        if sender_conn: 
            # Tìm username của người gửi để in log debug
            for u, c in online_users.items():
                if c == sender_conn:
                    sender_username_for_debug = u
                    break
        print(f"[DEBUG] Người gửi tin nhắn gốc: {sender_username_for_debug}")

        clients_to_remove = []
        sent_count = 0 
        for username, connstream in online_users.items():
            # Điều kiện này ngăn tin nhắn gửi lại cho chính người gửi
            if connstream != sender_conn: 
                # Dựa vào các log trước đó, bạn đã bỏ comment điều kiện này để test,
                # nên tôi sẽ giữ nguyên việc broadcast tới tất cả.
                
                print(f"[DEBUG] Đang cố gắng gửi tới: {username}") # DEBUG LOG
                try:
                    connstream.sendall(message_bytes)
                    sent_count += 1 
                    print(f"[DEBUG] Đã gửi thành công tới: {username}") # DEBUG LOG
                except (socket.error, ssl.SSLError, Exception) as e:
                    print(f"[-] Lỗi khi gửi broadcast tới {username}: {e}")
                    clients_to_remove.append(username)
        
        print(f"[DEBUG] Đã gửi tới {sent_count} client.") # DEBUG LOG
        # Xóa các client bị lỗi và thông báo
        for username in clients_to_remove:
            if username in online_users:
                print(f"[-] Xóa người dùng offline do lỗi gửi: {username}")
                try:
                    online_users[username].shutdown(socket.SHUT_RDWR)
                    online_users[username].close()
                except Exception as e:
                    print(f"[-] Lỗi đóng socket của {username} khi xóa: {e}")
                del online_users[username]
                notify_user_status(username, "offline")

def send_private_message(sender, receiver, message_obj):
    """Gửi tin nhắn riêng tư tới một người dùng cụ thể."""
    with online_users_lock:
        receiver_conn = online_users.get(receiver)
    
    if receiver_conn:
        try:
            message_json = json.dumps(message_obj)
            receiver_conn.sendall(message_json.encode('utf-8'))
            print(f"[+] Đã gửi tin nhắn riêng tư từ '{sender}' tới '{receiver}'.")
            return True
        except (socket.error, ssl.SSLError, Exception) as e:
            print(f"[-] Lỗi khi gửi tin nhắn riêng tư tới '{receiver}': {e}")
            # Xử lý người dùng offline nếu lỗi
            with online_users_lock:
                if receiver in online_users and online_users[receiver] == receiver_conn:
                    print(f"[-] Xóa người dùng offline do lỗi gửi riêng tư: {receiver}")
                    try:
                        online_users[receiver].shutdown(socket.SHUT_RDWR)
                        online_users[receiver].close()
                    except Exception as e:
                        print(f"[-] Lỗi đóng socket của {receiver} khi xóa riêng tư: {e}")
                    del online_users[receiver]
                    notify_user_status(receiver, "offline")
            return False
    else:
        print(f"[-] Người nhận '{receiver}' không online hoặc không tồn tại.")
        return False

def handle_client(connstream, address):
    """Xử lý kết nối từ một client."""
    client_username = None
    print(f"[+] Đã chấp nhận kết nối từ: {address}")
    try:
        # Bước 1: Nhận tin nhắn đăng nhập từ client
        # Đặt timeout ngắn để tránh bị kẹt vô thời hạn nếu client không gửi gì
        connstream.settimeout(15) 
        login_data = connstream.recv(4096)
        connstream.settimeout(None) # Reset timeout sau khi nhận
        
        if not login_data:
            print(f"[-] Kết nối bị đóng sớm từ {address}.")
            return

        login_message = json.loads(login_data.decode('utf-8'))
        if login_message.get("type") == "login":
            client_username = login_message.get("username")
            if client_username:
                with online_users_lock:
                    if client_username in online_users:
                        # Xử lý trường hợp username đã tồn tại (ví dụ: gửi lỗi hoặc thêm số vào tên)
                        print(f"[-] Người dùng '{client_username}' đã tồn tại. Ngắt kết nối mới.")
                        connstream.sendall(json.dumps({"type": "system", "sender": "Hệ thống", "content": f"Tên đăng nhập '{client_username}' đã được sử dụng. Vui lòng chọn tên khác."}).encode('utf-8'))
                        return # Thoát hàm handle_client

                    online_users[client_username] = connstream
                print(f"[+] Người dùng '{client_username}' đã đăng nhập.")
                notify_user_status(client_username, "online")
                send_online_users_list(connstream, client_username) # Gửi danh sách người dùng cho người mới đăng nhập
            else:
                print(f"[-] Lỗi đăng nhập từ {address}: Không có username.")
                return
        else:
            print(f"[-] Nhận được tin nhắn không phải đăng nhập từ {address}: {login_message.get('type')}")
            return

        # Bắt đầu vòng lặp nhận tin nhắn sau khi đăng nhập thành công
        print(f"[DEBUG] '{client_username}' đã đăng nhập. Bắt đầu vòng lặp nhận tin nhắn...") # DEBUG LOG
        while server_running: # Kiểm tra cờ server_running để thoát vòng lặp
            try:
                connstream.settimeout(1) # Đặt timeout ngắn cho recv() để không bị block mãi mãi
                data = connstream.recv(4096)
                connstream.settimeout(None) # Reset timeout sau khi nhận dữ liệu

                if not data:
                    print(f"[-] Người dùng '{client_username}' ({address}) đã ngắt kết nối.")
                    break # Thoát vòng lặp nếu client đóng kết nối

                print(f"[DEBUG] Nhận được dữ liệu thô từ '{client_username}': {data.decode(errors='ignore')}") # DEBUG LOG - Rất quan trọng!

                message_obj = json.loads(data.decode('utf-8'))
                message_type = message_obj.get("type")
                sender = message_obj.get("sender", "Unknown")
                content = message_obj.get("content", "")

                print(f"[<] Nhận từ '{sender}' ({address}) [Type: {message_type}]: {content}")

                if message_type == "chat":
                    # Tin nhắn chat chung
                    if "timestamp" not in message_obj:
                         message_obj["timestamp"] = time.strftime("%H:%M:%S", time.gmtime())
                    broadcast(message_obj, connstream) 
                    print(f"[DEBUG] Đã gọi broadcast cho tin nhắn chat từ '{sender}'.") # DEBUG LOG
                elif message_type == "private_chat":
                    # Tin nhắn riêng tư
                    receiver = message_obj.get("receiver")
                    if receiver and sender: 
                        if not send_private_message(sender, receiver, message_obj):
                            feedback_msg = {
                                "type": "system",
                                "sender": "Hệ thống",
                                "content": f"Người dùng '{receiver}' hiện không online hoặc không thể nhận tin nhắn của bạn.",
                                "timestamp": time.strftime("%H:%M:%S", time.gmtime())
                            }
                            try:
                                connstream.sendall(json.dumps(feedback_msg).encode('utf-8'))
                            except Exception as e:
                                print(f"[-] Lỗi gửi phản hồi cho {sender}: {e}")
                    else:
                        print(f"[-] Tin nhắn riêng tư từ {sender} thiếu thông tin người nhận hoặc người gửi.")
                        error_msg = {
                            "type": "system",
                            "sender": "Hệ thống",
                            "content": "Lỗi: Tin nhắn riêng tư thiếu thông tin người nhận hoặc người gửi.",
                            "timestamp": time.strftime("%H:%M:%S", time.gmtime())
                        }
                        try:
                            connstream.sendall(json.dumps(error_msg).encode('utf-8'))
                        except Exception as e:
                            print(f"[-] Lỗi gửi lỗi phản hồi cho {sender}: {e}")

                elif message_type == "request_user_list":
                    # Client yêu cầu danh sách người dùng online
                    send_online_users_list(connstream, client_username)
                else:
                    # Tin nhắn không xác định
                    print(f"[-] Nhận được loại tin nhắn không xác định từ {sender}: {message_obj}")
                    error_msg = {
                        "type": "system",
                        "sender": "Hệ thống",
                        "content": f"Lỗi: Loại tin nhắn '{message_type}' không xác định.",
                        "timestamp": time.strftime("%H:%M:%S", time.gmtime())
                    }
                    try:
                        connstream.sendall(json.dumps(error_msg).encode('utf-8'))
                    except Exception as e:
                        print(f"[-] Lỗi gửi lỗi phản hồi cho {sender}: {e}")

            except socket.timeout:
                # Không có dữ liệu trong 1 giây, tiếp tục vòng lặp để kiểm tra server_running
                continue
            except json.JSONDecodeError:
                print(f"[-] Lỗi giải mã JSON từ {client_username} ({address}): {data.decode(errors='ignore')}")
            except (socket.error, ssl.SSLError) as e:
                print(f"[-] Lỗi socket/SSL khi nhận dữ liệu từ {client_username} ({address}): {e}")
                break # Thoát vòng lặp nếu có lỗi socket/SSL
            except Exception as e:
                print(f"[-] Lỗi xử lý tin nhắn không xác định từ {client_username} ({address}): {e}")
                break # Thoát vòng lặp nếu có lỗi khác

    finally:
        # Đảm bảo người dùng bị xóa khỏi danh sách khi kết nối kết thúc
        if client_username:
            with online_users_lock:
                if client_username in online_users:
                    del online_users[client_username]
            print(f"[-] Người dùng '{client_username}' ({address}) đã ngắt kết nối và bị xóa.")
            notify_user_status(client_username, "offline")
        try:
            connstream.shutdown(socket.SHUT_RDWR)
            connstream.close()
        except Exception as e:
            print(f"[-] Lỗi đóng socket của {address}: {e}")

def main():
    global server_running
    ssl_context = get_ssl_context(is_server=True)
    
    # Tạo socket lắng nghe
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Cho phép tái sử dụng địa chỉ
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"[+] Server đang lắng nghe trên {HOST}:{PORT}...")

    # Chạy vòng lặp chấp nhận kết nối trong một luồng riêng hoặc luồng chính
    # Để có thể xử lý tín hiệu dừng server, chúng ta sẽ chấp nhận kết nối có timeout
    
    # Tạo một luồng để xử lý việc dừng server bằng lệnh 'exit'
    def server_input_handler():
        global server_running
        while True:
            cmd = input()
            if cmd.strip().lower() == 'exit':
                print("[!] Đang tắt server...")
                server_running = False
                # Để ngắt blocked accept, ta có thể tạo một kết nối giả
                try:
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((HOST, PORT))
                except Exception as e:
                    pass # Bỏ qua lỗi kết nối giả
                break

    input_thread = threading.Thread(target=server_input_handler, daemon=True)
    input_thread.start()

    try:
        while server_running:
            try:
                # Đặt timeout cho accept để vòng lặp có thể kiểm tra server_running
                server_socket.settimeout(1) 
                conn, addr = server_socket.accept()
                connstream = ssl_context.wrap_socket(conn, server_side=True)
                
                # Bắt đầu một luồng mới để xử lý client
                client_handler = threading.Thread(target=handle_client, args=(connstream, addr))
                client_handler.daemon = True # Đặt daemon để luồng tự tắt khi chương trình chính tắt
                client_handler.start()
            except socket.timeout:
                # Không có kết nối trong 1 giây, kiểm tra lại server_running
                continue
            except ssl.SSLError as e:
                print(f"[!] Lỗi SSL/TLS khi chấp nhận kết nối mới: {e}")
                # Đóng kết nối nếu có lỗi SSL
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                except:
                    pass
            except Exception as e:
                if server_running: # Chỉ in lỗi nếu server không đang tắt
                    print(f"[-] Lỗi khi chấp nhận kết nối: {e}")
                break # Thoát vòng lặp chính nếu có lỗi nghiêm trọng

    except KeyboardInterrupt:
        print("[!] Đang tắt server bằng Ctrl+C...")
    finally:
        server_running = False # Đảm bảo cờ tắt server
        try:
            # Gửi một kết nối giả để giải phóng accept() nếu nó đang bị block
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((HOST, PORT))
        except Exception as e:
            pass
        server_socket.close()
        print("[+] Server đã tắt.")

if __name__ == "__main__":
    main()