import socket
import ssl
import threading

clients = []

def broadcast(message, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                client.send(message)
            except:
                pass

def handle_client(connstream, address):
    print(f"[+] Client connected: {address}")
    clients.append(connstream)

    try:
        while True:
            data = connstream.recv(1024)
            if not data:
                break
            print(f"[{address}] {data.decode()}")
            broadcast(data, connstream)
    except Exception as e:
        print(f"[!] Error with {address}: {e}")
    finally:
        print(f"[-] Client disconnected: {address}")
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

    print("[*] Secure Chat Server (Tailscale) is listening on port 12345...")

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
