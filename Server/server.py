# server/server.py
import socket
import ssl
import threading

# Danh sách các client đang kết nối
clients = []

# Gửi tin nhắn đến tất cả client trừ người gửi
def broadcast(message, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                client.send(message)
            except:
                pass

# Xử lý mỗi client trong 1 thread
def handle_client(connstream, address):
    print(f"[+] Client connected: {address}")
    clients.append(connstream)
    
    try:
        while True:
            data = connstream.recv(1024)
            if not data:
                break  # client ngắt kết nối
            print(f"[{address}] {data.decode()}")
            broadcast(data, connstream)
    except Exception as e:
        print(f"[!] Error with {address}: {e}")
    finally:
        print(f"[-] Client disconnected: {address}")
        clients.remove(connstream)
        connstream.close()

def main():
    # Tạo ngữ cảnh SSL
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    # Tạo socket TCP
    bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsocket.bind(('0.0.0.0', 12345))
    bindsocket.listen(5)
    print("[*] Secure Chat Server listening on port 12345...")

    while True:
        try:
            newsocket, fromaddr = bindsocket.accept()
            # Bọc socket thường thành socket bảo mật
            connstream = context.wrap_socket(newsocket, server_side=True)
            # Tạo thread riêng cho client
            thread = threading.Thread(target=handle_client, args=(connstream, fromaddr))
            thread.start()
        except KeyboardInterrupt:
            print("\n[!] Server shutting down.")
            break
        except Exception as e:
            print(f"[!] Server error: {e}")

    bindsocket.close()

if __name__ == "__main__":
    main()
