import socket
import threading

IP = "0.0.0.0"
PORT = 7


def handle_client_connection(connection, address, client_id, clients):
    ip, port = address
    client_name = f"#{client_id} {ip}:{port}"
    print(f"Connected with {client_name}")

    while True:
        try:
            if len(connection.recv(1, socket.MSG_PEEK)):
                data = connection.recv(1024).decode()

                print(f"Message from {client_name}: {data}")

                for client in clients:
                    client.send(f"Message from {client_name}: {data}".encode())

        except (socket.error, OSError):
            print(f"Connection from {client_name} was closed")
            clients.remove(connection)
            connection.close()
            return


def accept_connections(server_socket):
    clients = []
    client_id = 0

    while True:
        connection, address = server_socket.accept()

        if len(clients) > 2:
            connection.sendall("SERVER BUSY".encode())
            connection.close()
            continue

        client_id += 1
        clients.append(connection)

        threading.Thread(
            target=handle_client_connection,
            args=(connection, address, client_id, clients),
        ).start()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind((IP, PORT))
    sock.listen(1)

    accept_connections(sock)
