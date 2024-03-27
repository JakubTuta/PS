import threading
import time

alphabet = "ABCDEFGHIJKLMNOPRSTUVWXYZ"


def printing(thread_id, exit_event):
    alphabet_id = 0
    while not exit_event.is_set():
        if alphabet_id == len(alphabet):
            return

        print(f"{alphabet[alphabet_id]}{thread_id}")
        alphabet_id += 1

        time.sleep(1)


exit_events = [threading.Event() for _ in range(10)]
threads = []

for i in range(10):
    thread = threading.Thread(target=printing, args=(i, exit_events[i]))
    thread.start()
    threads.append(thread)

while True:
    try:
        command = input("Action: ")
    except:
        pass

    try:
        action, number = command.split(" ")
        number = int(number)
    except:
        print("Incorrect command")
        continue

    if action == "stop" and 0 <= number <= 9:
        exit_events[number].set()
