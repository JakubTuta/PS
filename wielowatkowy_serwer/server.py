import socket
import threading

IP = "0.0.0.0"
PORT = 7


def handle_client_connection(connection, ip):
    print(f"Connected with {ip}")

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

    while True:
        sock.listen(1)
        connection, address = sock.accept()

        guest_ip = address[0]

        threading.Thread(
            target=handle_client_connection, args=(connection, guest_ip)
        ).start()
