import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 20777))
print("Waiting for ANY data...")
while True:
    data, addr = sock.recvfrom(2048)
    print(f"Success! Received {len(data)} bytes from {addr}")