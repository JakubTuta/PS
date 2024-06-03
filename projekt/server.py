import json
import queue
import socket
import threading

config = {}


def load_config():
    with open("config.json", "r") as file:
        data = json.load(file)

        for key, value in data.items():
            config[key] = value


def create_server_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind((config["ListenAddress"], config["ListenPort"]))

    server_socket.listen(config["TimeOut"])

    return server_socket


def listening(server_socket):
    while True:
        pass


def start_listening_thread(server_socket):
    worker = threading.Thread(target=listening, args=(server_socket,))
    worker.start()

    return worker


def main():
    load_config()

    server_socket = create_server_socket()

    listening_thread = start_listening_thread(server_socket)


if __name__ == "__main__":
    main()
