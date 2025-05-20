import socket
import ssl
import threading

# Địa chỉ IP Tailscale của server
HOST = '100.85.83.9'     # IP Tailscale thật
PORT = 2021           # Port server
# Địa chỉ IP Tailscale của client    

def receive_messages(ssl_socket):
    while True:
        try:
            data = ssl_socket.recv(1024)
            if not data:
                print("\n[!] Server disconnected.")
                break
            print("\n[Nhận] >", data.decode())
        except:
            print("\n[!] Lỗi kết nối.")
            break

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Cấu hình SSL client (chấp nhận self-signed cert)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    ssl_socket = context.wrap_socket(client_socket, server_hostname=HOST)

    try:
        ssl_socket.connect((HOST, PORT))
        print(f"[+] Đã kết nối đến {HOST}:{PORT} qua SSL (Tailscale).")

        threading.Thread(target=receive_messages, args=(ssl_socket,), daemon=True).start()

        while True:
            msg = input("Bạn: ")
            if msg.lower() in ["exit", "quit"]:
                print("[+] Đã thoát.")
                break
            ssl_socket.send(msg.encode())
    except Exception as e:
        print("[!] Không thể kết nối hoặc lỗi:", e)
    finally:
        ssl_socket.close()

if __name__ == "__main__":
    main()
