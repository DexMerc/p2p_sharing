import threading
import socket
import json
import time
import os
import tkinter as tk
import tkinter.ttk as ttk
from sys import getsizeof
from tkinter import messagebox


SIP = "127.0.0.1"
SPORT = 8080
FOLDER = "SharedP2P"
ENCODE = "utf-8"

HEIGHT = 500
WIDTH = 600
MAIN_BG = "#414141"

client = socket.socket()
mutex = threading.Lock()
localfiles = {}


def search(fileList, nameentry, sock):
    try:
        sock.send(bytes("SEARCH: " + nameentry.get(), ENCODE))
    except socket.error as msg:
        fileList.insert("", "end", text=msg)
    fileList.delete(*fileList.get_children())
    mutex.acquire()
    receive = sock.recv(1024).decode(ENCODE)
    mutex.release()
    if "NOT FOUND" in receive:
        fileList.insert("", "end", text="NOT FOUND")
    elif "FOUND:" in receive:
        dit = json.loads(sock.recv(1024).decode(ENCODE))
        for key in dit.keys():
            elem = dit[key]
            fileList.insert("", "end", text=key,
                            values=(elem["type"], elem["size"], elem["ip"] + ":" + str(elem["port"]), elem["modified"]))


def download(fileList):
    filename = fileList.item(fileList.focus())
    TIP = filename['values'][2].split(":")[0]
    TPORT = int(filename['values'][2].split(":")[1])+1
    client_t = socket.socket()
    client_t.connect((TIP, TPORT))
    time.sleep(0.1)
    client_t.send(
        bytes("DOWNLOAD: " + filename['text'] + ',' + filename['values'][0] + "," + filename['values'][1], ENCODE))
    with open(filename['text'] + "." + filename['values'][0], 'a') as file:
        temp = client_t.recv(1024).decode(ENCODE)
        while temp != "end":
            file.write(temp)
            temp = client_t.recv(1024).decode(ENCODE)
    print("Download was successful")
    client_t.close()


def start_socket():
    try:
        client.connect((SIP, SPORT))
        print("Connected ... ")
    except socket.error as msg:
        print("Socket error:", msg)

    client.send(bytes("Hello", ENCODE))
    if client.recv(1024).decode(ENCODE) != "Hi":
        return -1
    print("First connection successful.")
    lst = os.listdir(FOLDER)
    for item in lst:
        path = FOLDER + "/" + item
        name = item.split(".")[0]
        ext = item.split(".")[-1]
        modified = time.ctime(os.path.getmtime(path))[4:10] + time.ctime(os.path.getmtime(path))[-5:]
        if os.stat(path).st_size > 1023:
            size = str(round(os.stat(path).st_size / 1024, 1)) + " Kb"
        else:
            size = str(os.stat(path).st_size) + " B"
        localfiles[name] = {"type": ext, "modified": modified,
                            "size": size, "ip": client.getsockname()[0], "port": client.getsockname()[1]}
        if len(localfiles) == 5:
            break
    # print(client.getsockname())
    # pprint(localfiles)
    client.send(bytes("initial", ENCODE))
    client.send(bytes(str(getsizeof(localfiles)), ENCODE))
    client.send(bytes(json.dumps(localfiles), ENCODE))
    return client


def closing(root, sock):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        print("Exiting...")
        root.destroy()
        sock.send(bytes("Exit", ENCODE))


def App():
    sock = client
    root = tk.Tk()
    root.title("P2P sharing app")
    canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH)
    canvas.pack()

    frame = tk.Frame(root, bg=MAIN_BG)
    frame.place(relwidth=1, relheight=1)

    label = tk.Label(frame, text="Please, enter file name")
    label.place(relx=0.09, rely=0.06)

    nameentry = tk.Entry(frame, bg="grey")
    nameentry.place(relx=0.09, rely=0.11, relheight=0.05, relwidth=0.6)

    fileList = ttk.Treeview(frame)
    fileList["columns"] = ("type", "size", "peer", "modified")
    fileList.column("#0", minwidth=80, width=110)
    fileList.column("type", minwidth=20, width=40)
    fileList.column("size", minwidth=20, width=40)
    fileList.column("peer", minwidth=80, width=100)
    fileList.column("modified", minwidth=100, width=120)
    fileList.heading("#0", text="Files", anchor=tk.W)
    fileList.heading("type", text="Type", anchor=tk.W)
    fileList.heading("size", text="Size", anchor=tk.W)
    fileList.heading("peer", text="Peers", anchor=tk.W)
    fileList.heading("modified", text="Last modified", anchor=tk.W)
    fileList.place(relx=0.09, rely=0.2, relheight=0.5, relwidth=0.75)

    sbutton = tk.Button(frame, text="Search", command=lambda: search(fileList, nameentry, sock))
    sbutton.place(relx=0.75, rely=0.11)

    scroll = tk.Scrollbar(fileList, orient="vertical")
    fileList.config(yscrollcommand=scroll.set)
    scroll.config(command=fileList.yview)
    scroll.pack(side="right", fill="y")

    dbutton = tk.Button(frame, text="Download", command=lambda: download(fileList))
    dbutton.place(relx=0.4, rely=0.76)

    root.protocol("WM_DELETE_WINDOW", lambda: closing(root, sock))
    root.mainloop()


def sender():
    time.sleep(0.2)
    sclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sclient.bind((client.getsockname()[0],client.getsockname()[1]+1))
    sclient.listen()


    while True:
        sconn, saddr = sclient.accept()
        mutex.acquire()
        receive = sconn.recv(1024).decode(ENCODE)
        mutex.release()
        if "DOWNLOAD: " in receive:
            params = receive.split(" ")[1].split(",")
            try:
                file = open(params[0]+"."+params[1], "r")
                temp = file.read(1024)
                while len(temp) > 0:
                    sconn.send(bytes(temp, ENCODE))
                    temp = file.read(1024)
                file.close()
                sconn.send(bytes("end", ENCODE))
                print("File was sent successful")
            except EOFError as msg:
                print(msg)
        sconn.close()


def main():
    print("Homework was done by:")
    print("Sultan Bauyrzhanuly")
    print("Assem Tuleshova")
    print("--------------------------")
    res = start_socket()
    if res == -1:
        print("Unable to connect to the server")
        return
    thread1 = threading.Thread(target=App)
    thread2 = threading.Thread(target=sender)
    thread1.start()
    thread2.daemon = True
    thread2.start()


if __name__ == "__main__":
    main()
