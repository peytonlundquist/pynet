#!/usr/bin/python3           # This is server.py file
from re import S
import socket
import sys
import threading
import time
import atexit


class Address:
    def __init__(self, host, port):
        self.host = host
        self.port = port

# Circular list in order to rotate through peer's addresses 
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

# Thread that responds to peer's requests
class ServerThread(threading.Thread):
    def __init__(self, myport):
        threading.Thread.__init__(self)
        self.myport = myport

    def run(self):
        host = socket.gethostname()                                                     # Find my host name, usually localhost
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                # Set up socket
        serversocket.bind((host, self.myport))                                          # Taking the port specified and attaching this node to it for requests
        serversocket.listen(5)                                                          # Queue up to 5 requests
        print("Propping up on " + str(host) + ", " + str(self.myport))                  
        while True:                                                                     # Enter communication loop
            clientsocket, addr = serversocket.accept()                                  # Block thread until a client attempts to connect, then accept and open communicatoin line
            recvmsg = clientsocket.recv(1024)                                           # Expect a message from a client who requests, limiting to 1024 bytes
            recvmsg = recvmsg.decode('ascii')                                           # The message recieved needs to be decoded
            print("Server: Recieved " + recvmsg + " from a client connecting to us")
            if recvmsg == "ping":                                                       # If-else reply block
                reply = "pong"
            else:
                reply = "idk"         
            clientsocket.send(reply.encode('ascii'))                                    # Encode reply
            clientsocket.close()                                                        # Close the communication line

# Thread that requests for information from peers
class ClientThread(threading.Thread):
    def __init__(self, peerList):
        threading.Thread.__init__(self)
        self.peerList = peerList
        
    def run(self):
        while True:
            peer = self.peerList.next()                                                 # Rotate through list of peers
            time.sleep(1)                                                               # Temporary delay for output analysis
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                   # Prepare socket communication
                s.settimeout(20)                                                        # Socket will timeout after 20 seconds
                s.connect((peer.host, peer.port))                                       # Connect to peer
                msg = "ping"    
                s.send(msg.encode('ascii'))                                             # Make request to peer
                msgrecv = s.recv(1024)                                                  # Expect a reply
                s.close()                                                               # Close socket
                print("Client: Recieved " + msgrecv.decode('ascii') + " from hitting peer at " + str(peer.port))
            except ConnectionRefusedError:
                print("Client: Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down")
            except ConnectionAbortedError:
                print("Client: Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down")


class Node:
    def __init__(self, myport, port1, port2):
        peerList = NodeList(Address(socket.gethostname(), port1), Address(socket.gethostname(), port2))
        thread1 = ServerThread(myport)
        thread1.start()
        thread2 = ClientThread(peerList)
        thread2.start()

