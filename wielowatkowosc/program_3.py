import threading
import time

alphabet = "ABCDEFGHIJKLMNOPRSTUVWXYZ"
lock = threading.Lock()


def printing(thread_id):
    alphabet_id = 0
    while True:
        with lock:
            if alphabet_id == len(alphabet):
                return

            print(f"{alphabet[alphabet_id]}{thread_id}")
            alphabet_id += 1

            time.sleep(1)


threads = []

for i in range(10):
    thread = threading.Thread(target=printing, args=(i,))
    thread.start()
    threads.append(thread)
