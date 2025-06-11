import socket

HOST = '0.0.0.0'
PORT = 2021  

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print(f"[+] Server KHÔNG SSL đang lắng nghe tại {HOST}:{PORT}...")

conn, addr = server.accept()
print(f"[+] Client kết nối từ {addr}")

while True:
    data = conn.recv(1024)
    if not data:
        break
    print(f"[Server nhận được]: {data.decode('utf-8')}")
    conn.sendall(data)
