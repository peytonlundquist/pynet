#!/usr/bin/python3           # This is server.py file
import socket
import sys
import threading
import time
import atexit

class Address:
    def __init__(self, host, port):
        self.host = host
        self.port = port

class NodeList:
    def __init__(self, addr1, addr2):
        self.addr1 = addr1
        self.addr2 = addr2
        self.list = [addr1, addr2]
        self.index = 0
        self.current_node = self.list[self.index]

    def next(self):
        self.index = (self.index + 1) % 2
        self.current_node = self.list[self.index]
        return self.current_node


class ServerThread(threading.Thread):
    def __init__(self, myport):
        threading.Thread.__init__(self)
        self.myport = myport

    def run(self):
        host = socket.gethostname()
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind((host, self.myport))
        serversocket.listen(5)
        print("Propping up on " + str(host) + ", " + str(self.myport))
        while True:
            clientsocket, addr = serversocket.accept()
            print("Got a connection from %s" % str(addr))
            msg = 'Peer' + str(host) + ", " + str(self.myport) + ' pinged you' + "\r"
            clientsocket.send(msg.encode('ascii'))
            clientsocket.close()


class ClientThread(threading.Thread):
    def __init__(self, peerList):
        threading.Thread.__init__(self)
        self.peerList = peerList
        
    def run(self):
        while True:
            peer = self.peerList.next()
            time.sleep(1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(20)
                s.connect((peer.host, peer.port))
                msgrecv = s.recv(1024)
                s.close()
                print("Recieved:" + msgrecv.decode('ascii'))
            except ConnectionRefusedError:
                print("Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down")
            except ConnectionAbortedError:
                print("Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down")


class Node:
    def __init__(self, myport, port1, port2):

        peerList = NodeList(Address(socket.gethostname(), port1), Address(socket.gethostname(), port2))
        thread1 = ServerThread(myport)
        thread1.start()
        thread2 = ClientThread(peerList)
        thread2.start()

