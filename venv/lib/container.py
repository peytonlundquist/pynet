import json
from re import S
import socket
import sys
from tabnanny import verbose
import threading
import time
import atexit
import numpy as np
from typing import Dict, Any
import hashlib
import json

# https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
def dict_hash(dictionary: Dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


# Host and port
class Address:
    def __init__(self, host, port):
        self.host = host
        self.port = port

# Circular list to rotate through peer's addresses 
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


# Thread that responds to incoming peers for information consensus
class ServerThread(threading.Thread):
    def __init__(self, myport, bc, clientThread, verbose):
        threading.Thread.__init__(self)
        self.myport = myport
        self.bc = bc
        self.verbose = verbose
        self.clientThread = clientThread

    def setbc(self, x):
        self.bc = x
    
    def getbc(self):
        return self.bc  
    
    #
    # The server-thread will begin to deterministicly respond to the incoming client's message.
    # If the server thread recieves a message declaring a client mined a block, it determines 
    # the client's state view of the block chain, compares that to its own state view, and
    # responds back with the consequent action or determination decided.
    #
    def run(self):
        host = socket.gethostname()                                                     
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                
        serversocket.bind((host, self.myport))                                          
        serversocket.listen(5)                                                          
        if self.verbose:
            print("Peer " +  str(self.myport) + ": (Server-thread) Propping up on " + str(host) + ", " + str(self.myport))                  
           
        while True: 
            try:
            
                # We accept a client and decode their message
                clientsocket, addr = serversocket.accept()          
                recvmsg = clientsocket.recv(4096)                                           
                recvmsg = recvmsg.decode('ascii')                                       

                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Server-thread) Recieved [" + recvmsg + "] from a client connecting to us")

                if "Mined" in recvmsg:
                    msgList = recvmsg.split()
                    blockNumber = msgList[2]
                    blockValue = msgList[4]
                    chainHash = msgList[6]

                    if int(blockNumber) == len(self.bc):
                        gossipMessage = recvmsg + " [Signed by " + str(self.myport) + "]" 
                        
                        if chainHash != dict_hash(self.bc):
                            reply = "Refused block " + blockNumber + ": Disagreed chain hashcode. Deffering... [Signed by " + str(self.myport) + "]"
                            clientsocket.send(reply.encode('ascii'))
                            
                            recvmsg = clientsocket.recv(4096)                        
                            self.bc = json.loads(recvmsg.decode('utf-8'))        
                            if self.verbose:
                                print("Peer " +  str(self.myport) + ": (Server-thread) Refused block proposal: Disagreed hashcode")
                                print("Peer " +  str(self.myport) + ": (Server-thread) JSON Recieved. State updated: " + dict_hash(self.bc))
                                print("Peer " +  str(self.myport) + ": " + str(self.bc))

                        else:
                            reply = "Added block " + blockNumber + ". [Signed by " + str(self.myport) + "]"
                            self.bc[blockNumber] = blockValue 
                            clientsocket.send(reply.encode('ascii'))
                            if self.verbose:
                                print("Peer " +  str(self.myport) + ": (Server-thread) Sending message: [" + reply + "]. Hash: " + dict_hash(self.bc))

                        for i in range(0, 1):
                            self.clientThread.gossip(gossipMessage, addr)
                            if self.verbose:
                                print("Peer " +  str(self.myport) + ": (Server-thread) Gossip block")
                                  
                    elif int(blockNumber) < len(self.bc):
                        reply = "Refused block " + blockNumber + ": Behind state. [Signed by " + str(self.myport) + "]"
                        if self.verbose:
                            print("Peer " +  str(self.myport) + ": (Server-thread) Refused block proposal: Peer is behind state." )

                    else:
                        reply = "Refused block " + blockNumber + ": Disagreed State. Our block state = " + str(len(self.bc)) + ". Deffering... [Signed by " + str(self.myport) + "]"
                        clientsocket.send(reply.encode('ascii'))
                        recvmsg = clientsocket.recv(4096)
                        self.bc = json.loads(recvmsg.decode('utf-8'))    
                        if self.verbose:
                            print("Peer " +  str(self.myport) + ": (Server-thread) Refused block proposal: Disagreed state. ") 
                            print("Peer " +  str(self.myport) + ": " + str(self.bc))
                        
                elif "Request" in recvmsg:
                    reply = json.dumps(self.bc).encode('utf-8')
                    clientsocket.send(reply)
                    if self.verbose:
                        print("Peer " +  str(self.myport) + ": (Server-thread) Sending JSON of BC to requesting peer. Hash: " + dict_hash(self.bc))                                    
                clientsocket.close()  
                
            except json.JSONDecodeError:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Server-thread) JSON Decoding Error")   
            except ConnectionResetError:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Peer reset")
            except KeyboardInterrupt:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Killed")

              
# Thread that seeks out other peers for information consensus
class ClientThread(threading.Thread):
    def __init__(self, peerList, bc, myport, verbose):
        threading.Thread.__init__(self)
        self.peerList = peerList
        self.bc = bc
        self.myport = myport
        self.verbose = verbose
    
    def setbc(self, x):
        self.bc = x
        
    def getbc(self):
        return self.bc  
    
    # Propagate a message, with disregard for a response
    def gossip(self, msg, sender):
        try:
            peer = self.peerList.next() 
            if(sender != peer.port):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                   
                s.settimeout(20)                                                        
                s.connect((peer.host, peer.port))                                         
                s.send(msg.encode('ascii'))
                s.close
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Sent gossip")
        except ConnectionRefusedError:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread): Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down (refused)")
        except ConnectionAbortedError:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread): Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down (abort)")
    
    #
    # The client-thread will perform a pseudo-mining to generate blocks to be proposed. The thread is also 
    # responsible for updating the state view if a peer's server thread determines this node's view is
    # behind by more than 1 block. On a succesful mining (a peer's server thread accepts), we began to gossip
    # this block to our neighbors
    #

    def run(self):
        behind = False
        msgrecv = ""
        peer = self.peerList.next() 
        while True:          
            if(behind == False):
                rng = np.random.default_rng()
                num = rng.integers(10)
                time.sleep(num)
                msg = "Mined block " + str(len(self.bc)) + " Value " + str(num) + " Hash: " + dict_hash(self.bc) +" [Signed by " + str(self.myport) + "]"      
                self.bc[str(len(self.bc))] = str(num)
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) " + msg)
                    print("Peer " +  str(self.myport) + ": (Client-thread) Full-chain: " + dict_hash(self.bc))
                    print("Peer " +  str(self.myport) + ": " + str(self.bc))
            else:
                msg = "Request blockchain"                
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                   
                s.settimeout(20)                                                        
                s.connect((peer.host, peer.port))                                         
                s.send(msg.encode('ascii'))                                             
                msgrecv = s.recv(4096) 
                if not behind:
                    msgrecv = msgrecv.decode('ascii')                                                                
                if behind is True:
                    self.bc = json.loads(msgrecv.decode('utf-8'))                
                    if self.verbose:
                        print("Peer " +  str(self.myport) + ": (Client-thread) JSON Recieved. State updated: " + dict_hash(self.bc))
                        print("Peer " +  str(self.myport) + ": " + str(self.bc))
                    behind = False
                else:
                    if "Refused" in msgrecv:   # Refused: Behind/Disagree  
                        if self.verbose:
                            print("Peer " +  str(self.myport) + ": (Client-thread) Recieved [" + msgrecv + "] from Peer " + str(peer.port))                                                  
                        if "Behind" in msgrecv:
                            behind = True                      
                        if "Disagreed" in msgrecv:
                            reply = json.dumps(self.bc).encode('utf-8')
                            s.send(reply)
                            if self.verbose:
                                print("Peer " +  str(self.myport) + ": (Client-thread) Sending JSON of BC to requesting peer. Hash: " + dict_hash(self.bc))
                                print("Peer " +  str(self.myport) + ": " + str(self.bc))

                    s.close() 
                    if "Agreed" in msgrecv:
                        self.gossip(msg, peer.port)                  
            except TypeError:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Lost connection during process with Peer " + str(peer.port))
                behind = False
            except BrokenPipeError:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Broken connection during process with Peer " + str(peer.port))
                behind = False
            except ConnectionRefusedError:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down (refused)")
                peer = self.peerList.next() 
            except ConnectionAbortedError:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down (abort)")
                peer = self.peerList.next() 
            except socket.timeout:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Peer at " + str(peer.host) + ", " + str(peer.port) + " timed out")
                peer = self.peerList.next() 

            except ConnectionResetError:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Peer at " + str(peer.host) + ", " + str(peer.port) + " reset")
                peer = self.peerList.next()
            except KeyboardInterrupt:
                if self.verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Killed")


#
# The monitor-thread observes both the server-thread's and the client-thread's view of the 
# the world state, within a single container or node. It's purpose is to maintain a consistent
# internal view, blindly favoring the biggest chain if there is a difference 
#
class MonitorThread(threading.Thread):
        def __init__(self, serverThread, clientThread):
            threading.Thread.__init__(self)
            self.serverThread = serverThread
            self.clientThread = clientThread
        
        def run(self):
            True
            while True:
                if(len(self.serverThread.getbc()) > len(self.clientThread.getbc())):
                    self.clientThread.setbc(self.serverThread.getbc())
                    
                if(len(self.serverThread.getbc()) < len(self.clientThread.getbc())):
                    self.serverThread.setbc(self.clientThread.getbc())     


class Node:                  
    def __init__(self, myport, port1, port2, verbose):
        bc = {}
        peerList = NodeList(Address(socket.gethostname(), port1), Address(socket.gethostname(), port2))
        client = ClientThread(peerList, bc, myport, verbose)
        server = ServerThread(myport, bc, client, verbose)
        monitor = MonitorThread(server, client)
        client.start()
        server.start()
        monitor.start()

    def get_bc(self):
        return self.bc
        
        
        
