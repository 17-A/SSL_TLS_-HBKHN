import socket
import ssl
import threading
import sys

clients = []

def broadcast(message, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                client.send(message)
                print(f"[<] Message sent to another client")
            except Exception as e:
                print(f"[!] Error sending to another client: {e}")

def handle_client(connstream, address):
    print(f"[+] Client connected from {address} — currently {len(clients) + 1} client(s) connected")
    clients.append(connstream)

    try:
        while True:
            data = connstream.recv(1024)
            if not data:
                break
            print(f"[{address}] {data.decode()}")
            print(f"[>] Message from {address}: {data.decode().strip()}")
            broadcast(data, connstream)
    except Exception as e:
        print(f"[!] Error with {address}: {e}")
    finally:
        print(f"[-] Client {address} disconnected. Remaining clients: {len(clients) - 1}")
        if connstream in clients:
            clients.remove(connstream)
        connstream.close()

def main():
    # Cấu hình SSL
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    # Tạo socket TCP
    bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Lắng nghe trên mọi IP (bao gồm IP Tailscale)
    bindsocket.bind(('0.0.0.0', 2021))
    bindsocket.listen(5)

    print("[*] Secure Chat Server (Tailscale) is listening on port 2021...")

    # Luồng riêng để cho phép gõ lệnh tắt server
    def shutdown_listener():
        while True:
            cmd = input()
            if cmd.strip().lower() == "exit":
                print("[!] Shutting down server as requested...")
                bindsocket.close()
                sys.exit(0)

    threading.Thread(target=shutdown_listener, daemon=True).start()

    try:
        while True:
            newsocket, fromaddr = bindsocket.accept()
            connstream = context.wrap_socket(newsocket, server_side=True)
            threading.Thread(target=handle_client, args=(connstream, fromaddr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down.")
    except Exception as e:
        print(f"[!] Server error: {e}")
    finally:
        bindsocket.close()

if __name__ == "__main__":
    main()
