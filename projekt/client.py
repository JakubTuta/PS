import datetime
import json
import random
import socket
import string
import threading


def generate_random_id(length):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


class Client:
    def __init__(self):
        self.created_subjects = []
        self.subjects = []

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
            "created_subjects": self.created_subjects,
            "subjects": list(map(lambda subject: subject["topic"], self.subjects)),
        }
        json_data = json.dumps(data, indent=4, default=Client.__json_serial)

        return json_data

    def get_server_status(self, callback_function):
        request_data = {
            "type": "status",
            "id": self.client_id,
            "topic": "logs",
            "mode": "subscriber",
            "timestamp": datetime.datetime.now(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(Client.__prepare_send_data(request_data))

    def create_producer(self, topic_name):
        request_data = {
            "type": "register",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "producer",
            "timestamp": datetime.datetime.now(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(Client.__prepare_send_data(request_data))
            self.created_subjects.append(topic_name)

    def produce(self, topic_name, payload):
        request_data = {
            "type": "message",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "producer",
            "timestamp": datetime.datetime.now(),
            "payload": payload,
        }

        if self.is_connected():
            self.server_socket.send(Client.__prepare_send_data(request_data))

    def withdraw_producer(self, topic_name):
        request_data = {
            "type": "withdraw",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "producer",
            "timestamp": datetime.datetime.now(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(Client.__prepare_send_data(request_data))

    def create_subscriber(self, topic_name, callback_function):
        request_data = {
            "type": "register",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "subscriber",
            "timestamp": datetime.datetime.now(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(Client.__prepare_send_data(request_data))

            callback_function(topic_name)

    def withdraw_subscriber(self, topic_name):
        request_data = {
            "type": "withdraw",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "subscriber",
            "timestamp": datetime.datetime.now(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(Client.__prepare_send_data(request_data))

    def create_subscriber_thread(self, topic_name):
        thread = threading.Thread(
            target=self.__handle_subscriber_thread, args=(topic_name,)
        )
        thread.daemon = True
        thread.start()

        self.subscriber_threads[topic_name]["thread"] = thread
        self.subscriber_threads[topic_name]["is_stop"] = False

    def stop(self):
        if self.is_connected():
            self.server_socket.close()

        for subscriber_obj in self.subscriber_threads:
            subscriber_obj["is_stop"] = True

    def __handle_subscriber_thread(self, topic_name):
        while not self.subscriber_threads[topic_name]["is_stop"]:
            pass

    @staticmethod
    def __prepare_send_data(data):
        json_data = json.dumps(data, default=Client.__json_serial)
        encoded_data = json_data.encode()

        return encoded_data

    @staticmethod
    def __json_serial(data):
        if isinstance(data, (datetime.datetime, datetime.date)):
            return data.isoformat()

        raise TypeError(f"Type {type(data)} not serializable")


if __name__ == "__main__":
    # server_address = input("Enter server address: ")
    # server_port = int(input('Enter server port: '))

    server_address = "localhost"
    server_port = 2137
    client_id = generate_random_id(20)

    client = Client()
    client.start(server_address, server_port, client_id)

    while True:
        command = input(
            "Enter command\
                \n\tis connected\n \
                \tget status\n \
                \tget server status\n \
                \tcreate producer\n \
                \tproduce\n \
                \twithdraw producer\n \
                \tcreate subscriber\n \
                \twithdraw subscriber\n \
                \tstop\n"
        )

        match command.lower():
            case "is connected":
                print(client.is_connected())

            case "get status":
                print(client.get_status())

            case "get server status":
                print(client.get_server_status())

            case "create producer":
                topic = input("Enter subject topic: ")
                client.create_producer(topic)

            case "produce":
                topic = input("Enter subject topic: ")
                client.produce(topic, {})

            case "withdraw producer":
                topic = input("Enter subject topic: ")
                client.withdraw_producer(topic)

            case "create subscriber":
                topic = input("Enter subject topic: ")
                client.create_subscriber(topic, client.create_subscriber_thread)

            case "withdraw subscriber":
                topic = input("Enter subject topic: ")
                client.withdraw_subscriber(topic)

            case "stop":
                client.stop()

            case _:
                print("Incorrect command")
