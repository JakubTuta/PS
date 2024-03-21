import socket
import threading

IP = "0.0.0.0"
PORT = 7


def handle_client_connection(connection, ip, client_id):
    print(f"Connected with #{client_id} {ip}")

    while True:
        try:
            if len(connection.recv(1, socket.MSG_PEEK)):
                data = connection.recv(1024).decode()

                print(f"Message from {ip}: {data}")

                connection.send(data.encode())
        except:
            connection.close()
            return


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind((IP, PORT))
    client_id = 0

    while True:
        sock.listen(1)
        connection, address = sock.accept()
        client_id += 1

        guest_ip = address[0]

        threading.Thread(
            target=handle_client_connection, args=(connection, guest_ip, client_id)
        ).start()
