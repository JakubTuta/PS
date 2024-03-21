import threading
import time

alphabet = "ABCDEFGHIJKLMNOPRSTUVWXYZ"


def printing(thread_id, stop_event, exit_event):
    alphabet_id = 0
    while not exit_event.is_set():
        if not stop_event.is_set():
            continue

        if alphabet_id == len(alphabet):
            return

        print(f"{alphabet[alphabet_id]}{thread_id}")
        alphabet_id += 1

        time.sleep(1)


stop_events = [threading.Event() for _ in range(10)]
exit_events = [threading.Event() for _ in range(10)]
threads = []

for i in range(10):
    thread = threading.Thread(target=printing, args=(i, stop_events[i], exit_events[i]))
    thread.start()
    threads.append(thread)

while True:
    command = input("Action: ")

    if command == "end":
        for i, exit_event in enumerate(exit_events):
            exit_event.set()
            threads[i].join()
        break

    try:
        action, number = command.split(" ")
        number = int(number)
    except:
        print("Incorrect command")
        continue

    if action == "start" and 0 <= number <= 9:
        stop_events[number].set()

    elif action == "stop" and 0 <= number <= 9:
        stop_events[number].clear()
