import socket

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    server_address = ("0.0.0.0", 2137)
    server_socket.bind(server_address)

    print("Server is running")

    while True:
        data, client_address = server_socket.recvfrom(1024)

        print(f"Message from {client_address}: {data.decode()}")

        server_socket.sendto(data, client_address)
