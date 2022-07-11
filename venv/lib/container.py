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
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


# Host and port
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

# Thread that responds to incoming peers for information consensus
class ServerThread(threading.Thread):
    def __init__(self, myport, bc, verbose):
        threading.Thread.__init__(self)
        self.myport = myport
        self.bc = bc
        self.verbose = verbose

    def setbc(self, x):
        self.bc = x
    
    def getbc(self):
        return self.bc  
    
    def run(self):
        # Find my host name, usually localhost
        host = socket.gethostname()                                                     
        # Set up socket
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                
        # Taking the port specified and attaching this node to it for requests
        serversocket.bind((host, self.myport))                                          
        # Queue up to 5 requests
        serversocket.listen(5)                                                          
        print("Peer " +  str(self.myport) + ": (Server-thread) Propping up on " + str(host) + ", " + str(self.myport))                  
        while True:
            # Block thread until a client attempts to connect, then accept and open communicatoin line
            clientsocket, addr = serversocket.accept()                                  
            # Expect a message from a client who requests, limiting to 1024 bytes
            recvmsg = clientsocket.recv(4096)                                           
            # The message recieved needs to be decoded
            recvmsg = recvmsg.decode('ascii')                                       
            print("Peer " +  str(self.myport) + ": (Server-thread) Recieved [" + recvmsg + "] from a client connecting to us")
            

            #
            # This is our deterministic protocol logic for incoming requests
            #
            if "Mined" in recvmsg:
                # String manipulation for simplicity of pickiling                                                       
                msgList = recvmsg.split()
                blockNumber = msgList[2]
                blockValue = msgList[4]
                if int(blockNumber) >= len(self.bc):                    
                    reply = "Added block " + blockNumber + ". [Signed by " + str(self.myport) + "]"
                    self.bc[blockNumber] = blockValue
                    print("Peer " +  str(self.myport) + ": (Server-thread) Sending message: [" + reply + "]")
                else:
                    # If a we were told to add a block behind our most recent block, we reject and ask them to skip forward to us
                    reply = "Refused block " + blockNumber + ": Behind state. [Signed by " + str(self.myport) + "]"
                    print("Peer " +  str(self.myport) + ": (Server-thread) Refused block proposal" )
                clientsocket.send(reply.encode('ascii')) 
            elif "Request" in recvmsg:
                reply = json.dumps(self.bc).encode('utf-8')
                print("Peer " +  str(self.myport) + ": (Server-thread) Sending JSON of BC to requesting peer. Hash: " + dict_hash(self.bc))
                clientsocket.send(reply)                                    

            # Encode reply
            # Close the communication line
            clientsocket.close()                                                        


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
        
    def run(self):
        behind = False
        msgrecv = ""
        peer = self.peerList.next() 
        while True:
            
            if(behind == False):
                # Rotate through list of peers
                                                                
                # Temporary delay for output analysis
                
                # Mining / Computing
                rng = np.random.default_rng()
                num = rng.integers(60)
                time.sleep(num)
                msg = "Mined block " + str(len(self.bc)) + " Value " + str(num)
                print("Peer " +  str(self.myport) + ": (Client-thread) " + msg)
                self.bc[str(len(self.bc))] = str(num)
                if verbose:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Full-chain: ")
                    print(self.bc)
                else:
                    print("Peer " +  str(self.myport) + ": (Client-thread) Hash of BC: " + dict_hash(self.bc))
                    
                    
            else:
                msg = "Request blockchain"
                
            try:
                # Prepare socket communication
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                   
                # Socket will timeout after 20 seconds
                s.settimeout(20)                                                        
                # Connect to peer
                s.connect((peer.host, peer.port))                                         
                # Make request to peer
                s.send(msg.encode('ascii'))                                             
                # Expect a reply
                msgrecv = s.recv(4096) 
                # Decode
                if not behind:
                    msgrecv = msgrecv.decode('ascii')                                                 
                # Close socket
                s.close()               
                #print("Peer " +  str(self.myport) + ": (Client-thread) Recieved: " + msgrecv + " from hitting peer at " + str(peer.port))
            except ConnectionRefusedError:
                True
                print("Peer " +  str(self.myport) + ": (Client-thread): Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down (refused)")
                peer = self.peerList.next() 
            except ConnectionAbortedError:
                True
                print("Peer " +  str(self.myport) + ": (Client-thread): Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down (abort)")
                peer = self.peerList.next() 

                
            #
            # This is our deterministic protocol logic for incoming responses
            #            
            
            # A peer may refuse our block number because we are behind in the blockchain. In such a case we accept the higher block chain
            if behind is True:
                self.bc = json.loads(msgrecv.decode('utf-8'))
                print("Peer " +  str(self.myport) + ": JSON Recieved. State updated: " + dict_hash(self.bc))
                if verbose:
                    print(self.bc)
                behind = False
            else:
                if "Refused" in msgrecv:   # Refused: Behind/Disagree                                                    
                    if "Behind" in msgrecv:
                        behind = True
                    print("Peer " +  str(self.myport) + ": Recieved [" + msgrecv + "] from Peer " + str(peer.port))           

class Node:                  
    def __init__(self, myport, port1, port2, verbose):
        bc = {}
        peerList = NodeList(Address(socket.gethostname(), port1), Address(socket.gethostname(), port2))
        server = ServerThread(myport, bc, verbose)
        client = ClientThread(peerList, bc, myport, verbose)
        server.start()
        client.start()
        
        
        
