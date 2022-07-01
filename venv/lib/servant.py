#!/usr/bin/python3           # This is server.py file
import socket
import sys
import threading
import time
import atexit

myport = int(input("my port: "))
peer1 = int(input("peer1 port: "))
peer2 = int(input("peer2 port: "))

host = socket.gethostname()


class NodeList:
    def __init__(self, addr1, addr2):
        self.addr1 = addr1
        self.addr2 = addr2
        self.list = [addr1, addr2]
        self.index = 0
        self.current_node = self.list[self.index]

    def deep_copy(self, idx):
        return Node(self.list[idx].value)

    def next(self):
        self.index = (self.index + 1) % 2
        self.current_node = self.list[self.index]
        return self.current_node


peerList = NodeList(peer1, peer2)


class ServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind((host, myport))
        serversocket.listen(5)
        print("Propping up on " + str(host) + ", " + str(myport))
        while True:
            print("Waiting for incoming connections")
            clientsocket, addr = serversocket.accept()
            print("Got a connection from %s" % str(addr))
            msg = 'Peer' + str(host) + ", " + str(myport) + ' pinged you' + "\r"
            clientsocket.send(msg.encode('ascii'))
            clientsocket.close()


class ClientThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            peer = peerList.next()
            time.sleep(1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(20)
                s.connect((host, peer))
                msgrecv = s.recv(1024)
                s.close()
                print("Recieved:" + msgrecv.decode('ascii'))
            except ConnectionRefusedError:
                print("Peer at" + str(host) + ", " + str(peer) + " appears down")
            except ConnectionAbortedError:
                print("Peer at" + str(host) + ", " + str(peer) + " appears down")


thread1 = ServerThread()
thread1.start()
thread2 = ClientThread()
thread2.start()
