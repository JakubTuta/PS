import socket

IP = "localhost"
PORT = 7

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((IP, PORT))

    while True:
        try:
            msg = input("Enter message: ")
        except:
            break

        if msg is None or msg == "":
            break

        sock.send(msg.encode())

        data_received = sock.recv(1024).decode()
        print(f"Message from server: {data_received}")
