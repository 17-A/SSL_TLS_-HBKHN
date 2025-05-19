import socket
import ssl
import threading

# Cấu hình kết nối
HOST = 'localhost'       # Địa chỉ server
PORT = 12345             # Cổng server đang lắng nghe

def receive_messages(ssl_socket):
    """Luồng nhận tin nhắn"""
    while True:
        try:
            data = ssl_socket.recv(1024)
            if not data:
                break
            print("\n[Nhận] >", data.decode())
        except:
            print("\n[!] Mất kết nối với server.")
            break

def main():
    # Tạo socket TCP/IP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Tạo SSL context cho client
    context = ssl.create_default_context()
    
    # Vì dùng chứng chỉ tự ký, ta bỏ qua bước xác minh (nếu không sẽ bị lỗi)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Gói socket lại trong SSL
    ssl_socket = context.wrap_socket(client_socket, server_hostname=HOST)

    try:
        # Kết nối tới server
        ssl_socket.connect((HOST, PORT))
        print(f"[+] Đã kết nối bảo mật tới server {HOST}:{PORT}.")

        # Khởi chạy luồng nhận tin nhắn
        threading.Thread(target=receive_messages, args=(ssl_socket,), daemon=True).start()

        # Gửi tin nhắn
        while True:
            msg = input("Bạn: ")
            if msg.lower() == "exit":
                print("[+] Đã thoát.")
                break
            ssl_socket.send(msg.encode())
    except Exception as e:
        print("[!] Lỗi:", e)
    finally:
        ssl_socket.close()

if __name__ == "__main__":
    main()
 