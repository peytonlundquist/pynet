import json
from re import S
import socket
import sys
import threading
import time
import atexit
import numpy as np

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
    def __init__(self, myport, bc):
        threading.Thread.__init__(self)
        self.myport = myport
        self.bc = bc

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
            recvmsg = clientsocket.recv(1024)                                           
            # The message recieved needs to be decoded
            recvmsg = recvmsg.decode('ascii')                                       
            print("Peer " +  str(self.myport) + ": (Server-thread) Recieved " + recvmsg + " from a client connecting to us")
            
            
            
            
            
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
                    print(reply)
                else:
                    # If a we were told to add a block behind our most recent block, we reject and ask them to skip forward to us
                    reply = "Refused block " + blockNumber + ": Behind state. [Signed by " + str(self.myport) + "]"
                    print("Peer " +  str(self.myport) + ": (Server-thread) Refused block proposal" )
                clientsocket.send(reply.encode('ascii')) 
            elif "Request" in recvmsg:
                reply = json.dumps(self.bc).encode('utf-8')
                print(reply)
                clientsocket.send(reply)                                    

            # Encode reply
            # Close the communication line
            clientsocket.close()                                                        








# Thread that seeks out other peers for information consensus
class ClientThread(threading.Thread):
    def __init__(self, peerList, bc, myport):
        threading.Thread.__init__(self)
        self.peerList = peerList
        self.bc = bc
        self.myport = myport
    
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
                num = rng.integers(15)
                time.sleep(num)
                msg = "Mined block " + str(len(self.bc)) + " Value " + str(num)
                print(msg)
                self.bc[str(len(self.bc))] = str(num)
                print("BC: ")
                print(self.bc)
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
                msgrecv = s.recv(1024) 
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
                print("JSON Recieved")
                self.bc = json.loads(msgrecv.decode('utf-8'))
                print(self.bc)
                behind = False
            else:
                if "Refused" in msgrecv:   # Refused: Behind/Disagree                                                    
                    if "Behind" in msgrecv:
                        behind = True
            print(msgrecv)

                    

                   
                
                
class MonitorThread(threading.Thread):
        def __init__(self, serverThread, clientThread):
            threading.Thread.__init__(self)
            self.serverThread = serverThread
            self.clientThread = clientThread
        
        def run(self):
            True
            # Thread which holds a light consensus
            # while True:
                # if(self.serverThread.getbc() > self.clientThread.getbc()):
                #     self.clientThread.setbc(self.serverThread.getbc())
                    
                # if(self.serverThread.getbc() < self.clientThread.getbc()):
                #     self.serverThread.setbc(self.clientThread.getbc())             
            
class Node:                  
    def __init__(self, myport, port1, port2):
        bc = {}
        peerList = NodeList(Address(socket.gethostname(), port1), Address(socket.gethostname(), port2))
        server = ServerThread(myport, bc)
        client = ClientThread(peerList, bc, myport)
        monitor = MonitorThread(server, client)
        server.start()
        client.start()
        monitor.start()
        
        
        
