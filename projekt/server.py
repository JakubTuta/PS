import json
import queue
import socket
import threading
import time

config = {}


class Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_socket.bind((config["ListenAddress"], config["ListenPort"]))

        self.server_socket.settimeout(config["TimeOut"])

        self.clients = {}
        self.received_messages = queue.Queue()
        self.messages_to_send = queue.Queue()
        self.subjects = []

        self.stop_server = False
        self.stop_messages = False

    def create_listening_thread(self):
        thread = threading.Thread(target=self.__listening_thread)
        thread.start()

    def stop_listening_thread(self):
        self.stop_server = True

    def create_client_handle_thread(self, client_socket, client_ip):
        thread = threading.Thread(target=self.__client_handle, args=(client_socket,))
        thread.start()

        self.clients[client_ip]["socket"] = client_socket
        self.clients[client_ip]["thread"] = thread

    def create_messages_thread(self):
        thread = threading.Thread(target=self.__messages_thread)
        thread.start()

    def stop_messages_thread(self):
        self.stop_messages = True

    def __listening_thread(self):
        self.server_socket.listen(1)

        while not self.stop_server:
            try:
                client_socket, client_address = self.server_socket.accept()
                guest_ip = client_address[0]

                self.create_client_handle_thread(client_socket, guest_ip)

            except socket.timeout:
                pass

            except:
                self.stop_server = True
                return

    def __client_handle(self, client_socket, client_ip):
        client_socket.settimeout(config["TimeOut"])

        while True:
            try:
                if len(client_socket.recv(1, socket.MSG_PEEK)):
                    data = client_socket.recv(1024).decode()

                    self.received_messages.put((client_socket, data))

            except socket.timeout:
                pass

            except:
                self.clients[client_ip]["socket"].close()
                del self.clients[client_ip]

                return

    def __messages_thread(self):
        while not self.stop_messages:
            if self.received_messages.empty():
                time.sleep(0.001)


def load_config():
    with open("config.json", "r") as file:
        data = json.load(file)

        for key, value in data.items():
            config[key] = value


def main():
    load_config()

    server_socket = Server()


if __name__ == "__main__":
    main()
