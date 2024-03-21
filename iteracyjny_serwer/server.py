import socket

IP = "0.0.0.0"
PORT = 7

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind((IP, PORT))
    client_id = 0

    while True:
        sock.listen(1)
        connection, address = sock.accept()
        client_id += 1

        guest_ip = address[0]
        print(f"Connection from #{client_id} {guest_ip}")

        while True:
            try:
                data_received = connection.recv(1024).decode()
            except:
                break

            if data_received is None or data_received == "":
                break

            print(data_received)

            connection.send(data_received.encode())

        connection.close()
