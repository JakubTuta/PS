import datetime
import json
import random
import socket
import string
import threading
import typing

""" subscriber_thread = {
    "thread": threading.Thread,
    "is_stop": bool,
    "queue": typing.List[dict],
}
"""

""" message = {
    "type": str,
    "id": str,
    "topic": str,
    "mode": str,
    "timestamp": str,
    "payload": typing.Dict[str, typing.Union[datetime.datetime, str, bool, str]],
}
"""

""" payload = {
    "timestamp_of_message": str,
    "topic_of_message": str,
    "success": bool,
    "message": str,
}
"""


def generate_random_id(length: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


class Client:
    def __init__(self):
        self.created_subjects: typing.List[str] = []
        self.subscriber_threads: typing.Dict[
            str,
            typing.Dict[str, typing.Union[bool, threading.Thread, typing.List[dict]]],
        ] = {}

        self.is_listening = True

    def start(self, server_address: str, server_port: int, client_id: str):
        self.client_id = client_id

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((server_address, server_port))

        self.__get_config()

        self.__start_listening_thread()

    def is_connected(self) -> bool:
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

    def get_status(self) -> str:
        data = {
            "created_subjects": self.created_subjects,
            "subscribed_subjects": list(self.subscriber_threads.keys()),
        }
        json_data = json.dumps(data, indent=4)

        return json_data

    def get_server_status(self, callback_function: typing.Callable[[str], None]):
        request_data = {
            "type": "status",
            "id": self.client_id,
            "topic": "logs",
            "mode": "subscriber",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(self.__prepare_send_data(request_data))
            response = self.server_socket.recv(1024).decode()
            message = json.loads(response)

            if message["type"] == "status":
                callback_function(response)
            else:
                self.__add_to_queue(message)

    def create_producer(self, topic_name: str):
        request_data = {
            "type": "register",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "producer",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(self.__prepare_send_data(request_data))
            self.created_subjects.append(topic_name)

    def produce(
        self, topic_name: str, payload: typing.Dict[str, typing.Union[str, int, float]]
    ):
        request_data = {
            "type": "message",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "producer",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": payload,
        }

        if self.is_connected():
            self.server_socket.send(self.__prepare_send_data(request_data))

    def withdraw_producer(self, topic_name: str):
        request_data = {
            "type": "withdraw",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "producer",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(self.__prepare_send_data(request_data))

    def create_subscriber(
        self, topic_name: str, callback_function: typing.Callable[[str], None]
    ):
        request_data = {
            "type": "register",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "subscriber",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(self.__prepare_send_data(request_data))
            callback_function(topic_name)

    def withdraw_subscriber(self, topic_name: str):
        request_data = {
            "type": "withdraw",
            "id": self.client_id,
            "topic": topic_name,
            "mode": "subscriber",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(self.__prepare_send_data(request_data))

    def create_subscriber_thread(self, topic_name: str):
        self.subscriber_threads[topic_name] = {
            "is_stop": False,
            "queue": [],
        }

        thread = threading.Thread(
            target=self.__handle_subscriber_thread, args=(topic_name,)
        )
        thread.daemon = True
        thread.start()

        self.subscriber_threads[topic_name]["thread"] = thread

    def stop(self):
        self.is_listening = False

        if self.is_connected():
            self.server_socket.close()

        for subscriber_obj in self.subscriber_threads.values():
            subscriber_obj["is_stop"] = True

    def __handle_subscriber_thread(self, topic_name: str):
        while not self.subscriber_threads[topic_name]["is_stop"]:
            if self.is_connected():
                data = self.server_socket.recv(1024).decode()
                message = json.loads(data)

                if message["topic"] == topic_name:
                    print(message)
                else:
                    self.__add_to_queue(message)

            self.__print_from_queue(topic_name)

    def __add_to_queue(self, message: dict):
        topic_name = message["topic"]

        if topic_name not in self.subscriber_threads:
            self.subscriber_threads[topic_name] = {"queue": []}

        self.subscriber_threads[topic_name]["queue"].append(message)

    def __print_from_queue(self, topic_name: str):
        if topic_name in self.subscriber_threads[topic_name]["queue"]:
            queue = self.subscriber_threads[topic_name]["queue"]

            for message in queue:
                print(message)

            self.subscriber_threads[topic_name]["queue"] = []

    def __get_config(self):
        request_data = {
            "type": "config",
            "id": self.client_id,
            "topic": "logs",
            "mode": "subscriber",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": {},
        }

        if self.is_connected():
            self.server_socket.send(self.__prepare_send_data(request_data))
            response = self.server_socket.recv(1024).decode()
            message = json.loads(response)

            if message["type"] == "config":
                self.__server_config = message["payload"]
            else:
                self.__add_to_queue(message)

    def __start_listening_thread(self):
        listening_thread = threading.Thread(target=self.__listening_thread)
        listening_thread.daemon = True
        listening_thread.start()

    def __listening_thread(self):
        while self.is_listening and self.is_connected():
            if self.server_socket.recv(1, socket.MSG_PEEK):
                data = self.server_socket.recv(1024).decode()
                print(data)

    @staticmethod
    def __prepare_send_data(
        data: typing.Dict[str, typing.Union[str, int, float, datetime.datetime]]
    ) -> bytes:
        json_data = json.dumps(data)
        encoded_data = json_data.encode()

        return encoded_data


if __name__ == "__main__":
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
                client.get_server_status(lambda response: print(response))

            case "create producer":
                topic = input("Enter subject topic: ")
                client.create_producer(topic)

            case "produce":
                topic = input("Enter subject topic: ")
                payload = {}
                client.produce(topic, payload)

            case "withdraw producer":
                topic = input("Enter subject topic: ")
                client.withdraw_producer(topic)

            case "create subscriber":
                topic = input("Enter subject topic: ")
                client.create_subscriber(
                    topic,
                    client.create_subscriber_thread,
                )

            case "withdraw subscriber":
                topic = input("Enter subject topic: ")
                client.withdraw_subscriber(topic)

            case "stop":
                client.stop()
                break

            case _:
                print("Incorrect command")
