import json
import queue
import socket
import threading

config = {}


class Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_socket.bind((config["ListenAddress"], config["ListenPort"]))

        self.server_socket.settimeout(config["TimeOut"])

        self.clients = {}

        self.stop_server = False

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

            except socket.timeout:
                pass

            except:
                self.clients[client_ip]["socket"].close()
                del self.clients[client_ip]

                return


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
