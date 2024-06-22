import datetime
import json
import queue
import socket
import threading
import time
import typing

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
    creator_socket: optional[socket]
    subscribers: list[socket]
    type: str
    id: str
    topic: str
    timestamp: datetime
    payload:
    {
        timestamp_of_message: datetime
        topic_of_message: str
        success: bool
        message: str
    }
}
"""


config: typing.Dict[str, typing.Any] = {}


class Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((config["ListenAddress"], config["ListenPort"]))
        self.server_socket.settimeout(config["TimeOut"])

        self.clients: typing.Dict[str, socket.socket] = {}
        self.received_messages = queue.Queue()
        self.messages_to_send = queue.Queue()
        self.subjects: typing.List[typing.Dict[str, typing.Any]] = []

        self.stop_server = False
        self.stop_messages = False

    def start_server(self):
        self.create_listening_thread()
        self.create_messages_thread()
        self.user_interface()

    def close_server(self):
        self.stop_listening_thread()
        self.stop_messages_thread()

    def create_listening_thread(self):
        print("Creating user listening thread")

        thread = threading.Thread(target=self.__listening_thread)
        thread.daemon = True
        thread.start()

    def stop_listening_thread(self):
        print("Closing user listening thread")

        self.stop_server = True

    def create_client_handle_thread(self, client_socket: socket.socket, client_ip: str):
        print(f"Creating user thread for {client_ip}")

        self.clients[client_ip] = client_socket

        thread = threading.Thread(target=self.__client_handle, args=(client_socket,))
        thread.daemon = True
        thread.start()

    def create_messages_thread(self):
        print("Creating KKO and KKW listening threads")

        thread_KKO = threading.Thread(target=self.__messages_KKO_thread)
        thread_KKW = threading.Thread(target=self.__messages_KKW_thread)

        thread_KKO.daemon = True
        thread_KKW.daemon = True

        thread_KKO.start()
        thread_KKW.start()

    def stop_messages_thread(self):
        print("Closing messaging thread")

        self.stop_messages = True

    def user_interface(self):
        while not self.stop_server:
            print(
                "Available commands: (quit, users/clients, subjects, server info, stop server)"
            )
            user_command = input("Enter command: ")

            match user_command.lower():
                case "quit" | "stop_server":
                    break
                case "users" | "clients":
                    self.__print_clients()
                case "subjects":
                    self.__print_subjects()
                case "server info":
                    self.__print_server_info()
                case _:
                    print("Invalid command")

        self.close_server()

    def __print_clients(self):
        if not self.clients:
            print("No clients connected")
            return

        print("Currently active users:")

        for client_ip in self.clients.keys():
            print(f"\t{client_ip}")

        print()

    def __print_subjects(self):
        if not self.subjects:
            print("No subjects available")
            return

        print("Current subjects:")
        for subject in self.subjects:
            print(f"\tSubject: {subject['topic']}")
            print("\tSubscribers:")

            if subject["subscribers"]:
                for subscriber in subject["subscribers"]:
                    print(f'\t\t{subscriber["id"]}')

            print()

    def __print_server_info(self):
        server_info = json.dumps(
            {"Host": config["ListenAddress"], "Port": config["ListenPort"]}, indent=4
        )

        print(server_info)

    def __listening_thread(self):
        self.server_socket.listen(1)

        while not self.stop_server:
            try:
                client_socket, client_address = self.server_socket.accept()
                guest_ip = client_address[0]
                self.create_client_handle_thread(client_socket, guest_ip)

            except socket.timeout:
                pass

            except Exception as e:
                print(f"Error in listening thread: {e}")
                self.stop_server = True

    def __client_handle(self, client_socket: socket.socket):
        client_socket.settimeout(config["TimeOut"])

        while not self.stop_server:
            try:
                if len(client_socket.recv(1, socket.MSG_PEEK)):
                    serialized_data = client_socket.recv(1024).decode()
                    data = json.loads(serialized_data)

                    self.received_messages.put(
                        {"socket": client_socket, "message": data}
                    )

            except socket.timeout:
                pass

            except Exception as e:
                print(f"Error in client handle: {e}")
                break

        client_socket.close()

    def __messages_KKO_thread(self):
        while not self.stop_messages:
            if self.received_messages.empty():
                time.sleep(0.001)
                continue

            data = self.received_messages.get()
            client_socket = data["socket"]
            message = data["message"]

            if Server.__message_validation(message):
                self.__handle_KOM(client_socket, message)

            else:
                self.__reject_message(client_socket, message, "Invalid message format")

    def __messages_KKW_thread(self):
        while not self.stop_messages:
            if self.messages_to_send.empty():
                time.sleep(0.001)
                continue

            message = self.messages_to_send.get()
            creator_socket = message.pop("creator_socket", None)
            subscribers = message.pop("subscribers", [])

            if creator_socket:
                creator_socket.send(Server.__prepare_send_data(message))

            for subscriber in subscribers:
                subscriber.send(Server.__prepare_send_data(message))

    def __handle_KOM(
        self, client_socket: socket.socket, message: typing.Dict[str, typing.Any]
    ):
        match message["type"]:
            case "register":
                self.__handle_KOM_register(client_socket, message)
            case "withdraw":
                self.__handle_KOM_withdraw(message)
            case "message":
                self.__handle_KOM_message(client_socket, message)
            case "status":
                self.__handle_KOM_status(client_socket, message)
            case "config":
                self.__handle_KOM_config(client_socket, message)

    def __handle_KOM_register(
        self, client_socket: socket.socket, message: typing.Dict[str, typing.Any]
    ):
        found_subject = self.__find_subject(message["topic"])

        if message["mode"] == "subscriber":
            if found_subject:
                found_subject["subscribers"].append(
                    {
                        "id": message["id"],
                        "socket": client_socket,
                    }
                )

            else:
                self.__reject_message(client_socket, message, "Subject not found")

        elif message["mode"] == "producer" and (
            not found_subject or found_subject["creator_id"] != message["id"]
        ):
            self.subjects.append(
                {
                    "topic": message["topic"],
                    "creator_id": message["id"],
                    "creator_socket": client_socket,
                    "subscribers": [],
                }
            )

    def __handle_KOM_withdraw(self, message: typing.Dict[str, typing.Any]):
        found_subject = self.__find_subject(message["topic"])

        if not found_subject:
            return

        if message["mode"] == "producer":
            if self.__check_if_can_close_socket(found_subject["creator_id"]):
                print("Closing subject")
                found_subject["creator_socket"].close()

            for id, subscriber in enumerate(found_subject["subscribers"]):
                self.__reject_message(subscriber["socket"], message, "Subject closed")

                if self.__check_if_can_close_socket(subscriber["id"]):
                    subscriber["socket"].close()
                    del found_subject["subscribers"][id]

            self.__delete_subject(message["topic"])

        else:
            for id, subscriber in enumerate(found_subject["subscribers"]):
                self.__reject_message(subscriber["socket"], message, "Subject closed")

                if subscriber["id"] == message["id"]:
                    del found_subject["subscribers"][id]
                    return

    def __handle_KOM_message(
        self, client_socket: socket.socket, message: typing.Dict[str, typing.Any]
    ):
        found_subject = self.__find_subject(message["topic"])

        if not found_subject:
            return

        new_KKW_message = {
            "subscribers": [
                subscriber["socket"] for subscriber in found_subject["subscribers"]
            ],
            **message,
        }

        self.messages_to_send.put(new_KKW_message)

        self.__acknowledge_message(
            client_socket, message, acknowledge_message="Message sent"
        )

    def __handle_KOM_status(
        self, client_socket: socket.socket, message: typing.Dict[str, typing.Any]
    ):
        payload = [
            {
                "topic": subject["topic"],
                "creator_id": subject["creator_id"],
            }
            for subject in self.subjects
        ]

        new_KKW_message = {
            "creator_socket": client_socket,
            "type": "status",
            "id": config["ServerID"],
            "topic": "logs",
            "timestamp": message["timestamp"],
            "payload": payload,
        }

        self.messages_to_send.put(new_KKW_message)

    def __handle_KOM_config(
        self, client_socket: socket.socket, message: typing.Dict[str, typing.Any]
    ):
        new_KKW_message = {
            "creator_socket": client_socket,
            "type": "config",
            "id": message["id"],
            "topic": "logs",
            "timestamp": message["timestamp"],
            "payload": config,
        }

        self.messages_to_send.put(new_KKW_message)

    def __find_subject(
        self, subject_topic: str
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        return next(
            (subject for subject in self.subjects if subject["topic"] == subject_topic),
            None,
        )

    def __delete_subject(self, subject_topic: str):
        self.subjects = [
            subject for subject in self.subjects if subject["topic"] != subject_topic
        ]

    def __check_if_can_close_socket(self, client_id: str) -> bool:
        for subject in self.subjects:
            if subject["creator_id"] == client_id or any(
                subscriber["id"] == client_id for subscriber in subject["subscribers"]
            ):
                return False
        return True

    def __reject_message(
        self,
        client_socket: socket.socket,
        message: typing.Dict[str, typing.Any],
        reject_message: str,
    ):
        new_KKW_message = {
            "creator_socket": client_socket,
            "type": "reject",
            "id": message["id"],
            "topic": "logs",
            "timestamp": message["timestamp"],
            "payload": {
                "timestamp_of_message": message["timestamp"],
                "topic_of_message": message["topic"],
                "success": False,
                "message": reject_message,
            },
        }

        self.messages_to_send.put(new_KKW_message)

    def __acknowledge_message(
        self,
        client_socket: socket.socket,
        message: typing.Dict[str, typing.Any],
        acknowledge_message: str,
    ):
        new_KKW_message = {
            "creator_socket": client_socket,
            "type": "acknowledge",
            "id": message["id"],
            "topic": "logs",
            "timestamp": message["timestamp"],
            "payload": {
                "timestamp_of_message": message["timestamp"],
                "topic_of_message": message["topic"],
                "success": True,
                "message": acknowledge_message,
            },
        }

        self.messages_to_send.put(new_KKW_message)

    @staticmethod
    def __message_validation(message: typing.Dict[str, typing.Any]) -> bool:
        message_keys = ("type", "id", "topic", "mode", "timestamp", "payload")
        allowed_types = (
            "register",
            "withdraw",
            "reject",
            "acknowledge" "message",
            "status",
            "config",
        )
        allowed_modes = ("producer", "subscriber")
        allowed_payload_keys = (
            "timestamp_of_message",
            "topic_of_message",
            "success",
            "message",
        )

        if message["type"] in ["reject", "acknowledge"]:
            return (
                isinstance(message, dict)
                and all(key in message for key in message_keys)
                and message["type"] in allowed_types
                and message["mode"] in allowed_modes
                and isinstance(message["timestamp"], str)
                and Server.__is_iso_date(message["timestamp"])
                and isinstance(message["payload"], dict)
                and all(key in message["payload"] for key in allowed_payload_keys)
            )

        else:
            return (
                isinstance(message, dict)
                and all(key in message for key in message_keys)
                and message["type"] in allowed_types
                and message["mode"] in allowed_modes
                and isinstance(message["timestamp"], str)
                and Server.__is_iso_date(message["timestamp"])
            )

    @staticmethod
    def __is_iso_date(date_string: str) -> bool:
        try:
            datetime.datetime.fromisoformat(date_string)
            return True
        except ValueError:
            return False

    @staticmethod
    def __prepare_send_data(data: typing.Dict[str, typing.Any]) -> bytes:
        json_data = json.dumps(data, default=Server.__json_serial)
        return json_data.encode()

    @staticmethod
    def __json_serial(data: typing.Any) -> str:
        if isinstance(data, (datetime.datetime, datetime.date)):
            return data.isoformat()
        raise TypeError(f"Type {type(data)} not serializable")


def load_config():
    with open("config.json", "r") as file:
        data = json.load(file)
        config.update(data)


def main():
    load_config()
    server = Server()
    server.start_server()


if __name__ == "__main__":
    main()
