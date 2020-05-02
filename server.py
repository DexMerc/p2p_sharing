import socket
import threading
import json

# Homework was done by:
# Sultan Bauyrzhanuly
# Assem Tuleshova
IP = "127.0.0.1"
PORT = 8080
ENCODE = "utf-8"
online_clients = []
listOfRecords = {}
mutex = threading.Lock()


def find(filename):
    temp = {}
    if filename.strip() is not None:
        for key in listOfRecords.keys():
            if filename.lower() in key.lower() and temp.get(key) is None:
                temp[key] = listOfRecords.get(key)
    return temp


def client_handler(conn, addr):
    if conn.recv(1024).decode(ENCODE) != "Hello":
        print("Hello not received")
        conn.close()
        return
    conn.send(bytes("Hi", ENCODE))
    print("Client running on", conn.fileno())
    # a little safety measure
    if conn.recv(1024).decode(ENCODE) != "initial":
        conn.close()
        return
    # In case of file data from client is >1024
    size = int(conn.recv(1024).decode(ENCODE))
    if size < 1024:
        size = 1024
    dit = json.loads(conn.recv(size).decode(ENCODE))
    mutex.acquire()
    listOfRecords.update(dit)
    mutex.release()
    while True:
        if conn.fileno() < 0:
            print(addr, "- closed")
            conn.close()
            return
        temp = conn.recv(1024).decode(ENCODE)
        if "SEARCH: " in temp:
            print("Searched for", temp.split(" ")[1])
            dit = find(temp.split(" ")[1])
            # print(dit)
            if dit:
                conn.send(bytes("FOUND: ", ENCODE))
                conn.send(bytes(json.dumps(dit), ENCODE))
            else:
                conn.send(bytes("NOT FOUND", ENCODE))
        if "Exit" == temp:
            online_clients.remove(addr)
            print("Online clients:", online_clients)
            conn.close()
            return


def main():
    server_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_s.bind((IP, PORT))
    server_s.listen()
    print("Homework was done by:")
    print("Sultan Bauyrzhanuly")
    print("Assem Tuleshova")
    print("--------------------------")
    print("Running on", IP, ":", PORT)
    print("Waiting for any incoming connections ... ")

    while True:
        conn, addr = server_s.accept()
        cThread = threading.Thread(target=client_handler, args=(conn, addr))
        cThread.daemon = True
        cThread.start()
        mutex.acquire()
        online_clients.append(addr)
        print("Online clients:", online_clients)
        mutex.release()


if __name__ == "__main__":
    main()
