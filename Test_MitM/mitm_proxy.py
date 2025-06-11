import socket

LISTEN_PORT = 5555  # cổng giả làm server
TARGET_HOST = '127.0.0.1'  # hoặc IP thật của server nếu qua mạng
TARGET_PORT = 2021        # server thật

proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy.bind(('0.0.0.0', LISTEN_PORT))
proxy.listen(1)
print(f"[MITM] Đang lắng nghe kết nối từ client...")

client_conn, client_addr = proxy.accept()
print(f"[MITM] Client kết nối từ {client_addr}")

# Kết nối đến server thật
server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_conn.connect((TARGET_HOST, TARGET_PORT))
print("[MITM] Đã kết nối đến server thật")

while True:
    data = client_conn.recv(4096)
    if not data:
        break
    print(f"[MITM] Chặn được: {data.decode('utf-8')}")

    server_conn.sendall(data)
    response = server_conn.recv(4096)
    client_conn.sendall(response)
