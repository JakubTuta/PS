import datetime
import json
import queue
import socket
import threading
import time

""" clients:
[
    client_ip:
    {
        is_stop: bool
        socket: socket
    }   
]
"""

""" subject:
{
    topic: str
    creator_id: str
    creator_socket: socket
    subscribers:
        [
            {
                id: str
                socket: socket
            }
        ]
}
"""

""" received_message (KKO):
{
    type: str = 'register', 'withdraw', 'message', 'status'
    id: str
    topic: str
    mode: str = 'producer', 'subscriber'
    timestamp: datetime
    payload: {}
}
"""

""" message_to_send (KKW):
{
    creator_socket: socket | None
    subscribers: [socket]
    type: str = 'reject'
    id: str
    topic: str = 'logs'
    timestamp: datetime
    payload: {}
}
"""

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
        
        self.start_server()
        
    def start_server(self):
        self.create_client_handle_thread()
        self.create_listening_thread()
        self.create_messages_thread()
    
    def stop_server(self):
        self.stop_client_handle_thread()
        self.stop_listening_thread()
        self.stop_messages_thread()

    def create_listening_thread(self):
        thread = threading.Thread(target=self.__listening_thread)
        thread.start()

    def stop_listening_thread(self):
        self.stop_server = True

    def create_client_handle_thread(self, client_socket, client_ip):
        new_client = {"is_stop": False, "socket": client_socket}
        self.clients[client_ip] = new_client

        thread = threading.Thread(target=self.__client_handle, args=(new_client,))
        thread.start()

    def stop_client_handle_thread(self):
        for client in self.clients:
            client["is_stop"] = True

    def create_messages_thread(self):
        thread_KKO = threading.Thread(target=self.__messages_KKO_thread)
        thread_KKW = threading.Thread(target=self.__messages_KKW_thread)

        thread_KKO.start()
        thread_KKW.start()

    def stop_messages_thread(self):
        self.stop_messages = True

    def user_interface(self):
        while True:
            print(
                "Available commands: (quit, users/clients, subjects, server info, stop server)"
            )
            user_command = input("Enter command: ")

            match user_command.lower():
                case "quit":
                    break

                case "users" | "clients":
                    self.__print_clients()

                case "subjects":
                    self.__print_subjects()

                case "server info":
                    self.__print_server_info()

                case "stop server":
                    self.stop_server()

                case _:
                    print("Invalid command")

    def __print_clients(self):
        if not len(self.clients):
            return

        print("Currently active users:")

        for client_ip in self.clients.keys():
            print(f'\t{client_ip}')

        print()

    def __print_subjects(self):
        if not len(self.subjects):
            return

        print("Current subjects:")

        for subject in self.subjects:
            print(f"\tSubject: {subject['topic']}")
            print(f'\tSubscribers:')
            
            if len(subject['subscribers']):
                for subscriber in subject['subscribers']:
                    print(f'\t\t{subscriber['id']}')
            
            print()

    def __print_server_info(self):
        print(f"Host: {config['ListenAddress']}")
        print(f"Port: {config['ListenPort']}")
        print()

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

    def __client_handle(self, client):
        client["socket"].settimeout(config["TimeOut"])

        while not client["is_stop"]:
            try:
                if len(client["socket"].recv(1, socket.MSG_PEEK)):
                    data = client["socket"].recv(1024).decode()

                    self.received_messages.put(
                        {"socket": client["socket"], "message": data}
                    )

            except socket.timeout:
                pass

            except:
                break

        client["socket"].close()

    def __messages_KKO_thread(self):
        while not self.stop_messages:
            if self.received_messages.empty():
                time.sleep(0.001)

            data = self.received_messages.get()

            client_socket = data["socket"]
            message = data["message"]

            if Server.__message_validation(message):
                self.__handle_KOM(client_socket, message)

    def __messages_KKW_thread(self):
        while not self.stop_messages:
            if self.messages_to_send.empty():
                time.sleep(0.001)

            message = self.messages_to_send.get()

    def __handle_KOM(self, client_socket, message):
        match message["type"]:
            case "register":
                self.__handle_KOM_register(client_socket, message)

            case "withdraw":
                self.__handle_KOM_withdraw(message)

            case "message":
                self.__handle_KOM_message(message)

            case "status":
                self.__handle_KOM_status(client_socket, message)

    def __handle_KOM_register(self, client_socket, message):
        found_subject = self.__find_subject(message["topic"])

        if message["mode"] == "subscriber" and found_subject:
            found_subject["subscribers"].append(
                {
                    "id": message["id"],
                    "socket": "client_socket",
                }
            )

        elif (
            message["mode"] == "producer"
            and not found_subject
            and found_subject["creator_id"] != message["id"]
        ):
            self.subjects.append(
                {
                    "topic": message["topic"],
                    "creator_id": message["id"],
                    "creator_socket": client_socket,
                    "subscribers": [],
                }
            )

    def __handle_KOM_withdraw(self, message):
        found_subject = self.__find_subject(message["topic"])

        if not found_subject:
            return

        if message["mode"] == "producer":
            if self.__check_if_can_close_socket(found_subject["creator_id"]):
                found_subject["creator_socket"].close()

            for id, subscriber in enumerate(found_subject["subscribers"]):
                if self.__check_if_can_close_socket(subscriber["id"]):
                    subscriber["socket"].close()
                    del found_subject["subscribers"][id]

            self.__delete_subject(message["topic"])

        else:
            for id, subscriber in found_subject["subscribers"]:
                if subscriber["id"] == message["id"]:
                    del found_subject["subscribers"][id]

                    return

    def __handle_KOM_message(self, message):
        found_subject = message["topic"]

        new_KKW_message = {
            "subscribers": map(
                lambda subscriber: subscriber["socket"], found_subject["subscribers"]
            ),
            "creator_socket": None,
            **message,
        }

        self.messages_to_send.put(new_KKW_message)

    def __handle_KOM_status(self, client_socket, message):
        payload = map(
            lambda subject: {
                "topic": subject["topic"],
                "creator_id": subject["creator_id"],
            },
            self.subjects,
        )

        new_KKW_message = {
            "creator_socket": client_socket,
            "subscribers": [],
            "type": "reject",
            "id": message["id"],
            "topic": "logs",
            "timestamp": message["timestamp"],
            "payload": payload,
        }

        self.messages_to_send.put(new_KKW_message)

    def __find_subject(self, subject_topic):
        try:
            found_subject = next(
                subject for subject in self.subjects if subject.topic == subject_topic
            )

            return found_subject

        except StopIteration:
            return

    def __check_if_can_close_socket(self, client_id):
        for subject in self.subjects:
            if subject["creator_id"] == client_id:
                return False

            if any(
                subscriber["id"] == client_id for subscriber in subject["subscribers"]
            ):
                return False

        return True

    @staticmethod
    def __message_validation(message):
        message_keys = ("type", "id", "topic", "mode", "timestamp", "payload")

        allowed_types = (
            "register",
            "withdraw",
            "message",
            "status",
        )

        allowed_modes = ("producer", "subscriber")

        return (
            isinstance(message, dict)
            and all(key in message for key in message_keys)
            and message["type"] in allowed_types
            and message["mode"] in allowed_modes
        )


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
