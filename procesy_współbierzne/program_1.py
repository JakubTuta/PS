import threading


def hello_world():
    print("hello world")


function = threading.Thread(target=hello_world)
function.start()
function.join()
