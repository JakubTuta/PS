import json
import queue
import socket
import threading

config = {}


class Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_socket.bind((config["ListenAddress"], config["ListenPort"]))

        self.server_socket.listen(1)

        self.server_socket.settimeout(config["TimeOut"])


def load_config():
    with open("config.json", "r") as file:
        data = json.load(file)

        for key, value in data.items():
            config[key] = value


def listening(server_socket):
    while True:
        pass


def start_listening_thread(server_socket):
    worker = threading.Thread(target=listening, args=(server_socket,))
    worker.start()

    return worker


def main():
    load_config()

    server_socket = Server()

    listening_thread = start_listening_thread(server_socket)


if __name__ == "__main__":
    main()
