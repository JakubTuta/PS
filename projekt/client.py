import datetime
import json
import random
import socket
import string


def generate_random_id(length):
    return "".join(random.choices(string.ascii_letters + string.digits), k=length)


class Client:
    def __init__(self):
        self.subjects = []
        self.subscribed_to = []

    def start(self, server_address, server_port, client_id):
        self.client_id = client_id

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((server_address, server_port))

        self.start_listening()

    def start_listening(self):
        pass

    def is_connected(self):
        try:
            self.server_socket.setblocking(0)

            data = self.server_socket.recv(1, socket.MSG_PEEK)

            if data:
                return True
            else:
                return False

        except BlockingIOError:
            return True

        except ConnectionResetError:
            return False

        except socket.error:
            return False

        finally:
            self.server_socket.setblocking(1)

    def get_status(self):
        data = {
            "subjects": self.subjects,
            "subscribed_to": self.subscribed_to,
        }
        json_data = json.dumps(data, indent=4)

        return json_data

    def get_server_status(self):
        request_data = {
            "type": "status",
            "id": self.client_id,
            "topic": "logs",
            "mode": "subscriber",
            "timestamp": datetime.datetime.now(),
            "payload": {},
        }
        json_request_data = json.dumps(request_data)

        if self.is_connected():
            self.server_socket.sendall(json_request_data)

    def create_producer(self, topic_name):
        request_data = {
            "type": "register",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "producer",
            "timestamp": datetime.datetime.now(),
            "payload": {},
        }
        json_request_data = json.dumps(request_data)

        if self.is_connected():
            self.server_socket.sendall(json_request_data)

    @staticmethod
    def print_server_status(server_status):
        print(server_status)


if __name__ == "__main__":
    # server_address = input("Enter server address: ")
    # server_port = int(input('Enter server port: '))

    server_address = "localhost"
    server_port = 2137
    client_id = generate_random_id(20)

    client = Client()
    client.start(server_address, server_port, client_id)
