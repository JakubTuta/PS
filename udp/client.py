import socket

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server_address = ("<broadcast>", 2137)

    while True:
        try:
            data = input("Message for server: ")
        except KeyboardInterrupt:
            break
        else:
            if not data:
                break

        client_socket.sendto(data.encode(), server_address)

        data, server_address = client_socket.recvfrom(1024)
        print(f"Message from server: {data.decode()}")
