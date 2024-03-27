import socket
import threading

IP = "localhost"
PORT = 7


def send(connection, is_connection_broken):
    while not is_connection_broken.is_set():
        try:
            msg = input()

            connection.send(msg.encode())
        except (socket.error, OSError, KeyboardInterrupt):
            is_connection_broken.set()
            break


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((IP, PORT))
    is_connection_broken = threading.Event()

    threading.Thread(target=send, args=(sock, is_connection_broken)).start()

    while not is_connection_broken.is_set():
        try:
            data_received = sock.recv(1024).decode()
        except (socket.error, OSError):
            is_connection_broken.set()
            break
        else:
            if data_received == "SERVER BUSY":
                is_connection_broken.set()
                break

        print(data_received)

    print("Connection with server ended")
