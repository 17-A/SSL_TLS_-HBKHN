import socket

HOST = '127.0.0.1'  # giả định MITM proxy chạy local/có thể thay bằng ip tailscale server
PORT = 5555         # cổng MITM

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
print("[+] Đã kết nối đến server qua proxy (không mã hóa)")

while True:
    msg = input("Nhập tin nhắn: ")
    if not msg:
        break
    client.sendall(msg.encode())
    data = client.recv(1024)
    print(f"[Client nhận lại]: {data.decode()}")
