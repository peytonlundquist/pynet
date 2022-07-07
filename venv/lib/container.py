from re import S
import socket
import sys
import threading
import time
import atexit

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
            if "newBlock" in recvmsg:
                # String manipulation for simplicity of pickiling                                                       
                msgList = recvmsg.split()
                blockNumber = msgList[1]
                if int(blockNumber) >= self.bc:                    
                    reply = "Added block " + blockNumber + ". [Signed by " + str(self.myport) + "]"
                    self.bc = int(blockNumber) + 1
                else:
                    # If a we were told to add a block behind our most recent block, we reject and ask them to skip forward to us
                    reply = "Refused block " + blockNumber + ". My state: " + str(self.bc) + " [Signed by " + str(self.myport) + "]"
                    print("Peer " +  str(self.myport) + ": (Server-thread) Refused block proposal" )
            else:
                reply = "idk"        
                
            # Encode reply
            clientsocket.send(reply.encode('ascii'))                                    
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
        while True:
            # Rotate through list of peers
            peer = self.peerList.next()                                                 
            # Temporary delay for output analysis
            time.sleep(1)                                                               
            try:
                # Prepare socket communication
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                   
                # Socket will timeout after 20 seconds
                s.settimeout(20)                                                        
                # Connect to peer
                s.connect((peer.host, peer.port))                                       
                msg = "newBlock " + str(self.bc)    
                # Make request to peer
                s.send(msg.encode('ascii'))                                             
                # Expect a reply
                msgrecv = s.recv(1024) 
                # Decode
                msgrecv = msgrecv.decode('ascii')                                                 
                # Close socket
                s.close()
                
                #
                # This is our deterministic protocol logic for incoming responses
                #            
                
                # A peer may refuse our block number because we are behind in the blockchain. In such a case we accept the higher block chain
                if "Refused " in msgrecv:                                                       
                    msgList = msgrecv.split()
                    self.bc = int(msgList[5])                  
                print("Peer " +  str(self.myport) + ": (Client-thread) Recieved: " + msgrecv + " from hitting peer at " + str(peer.port))
            except ConnectionRefusedError:
                print("Peer " +  str(self.myport) + ": (Client-thread): Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down (refused)")
            except ConnectionAbortedError:
                print("Peer " +  str(self.myport) + ": (Client-thread): Peer at " + str(peer.host) + ", " + str(peer.port) + " appears down (abort)")
    
class Node:
    def __init__(self, myport, port1, port2):
        bc = 0
        peerList = NodeList(Address(socket.gethostname(), port1), Address(socket.gethostname(), port2))
        server = ServerThread(myport, bc)
        server.start()
        client = ClientThread(peerList, bc, myport)
        client.start()
        
        # Main thread which holds a light consensus
        while True:
            if(server.getbc() > client.getbc()):
                client.setbc(server.getbc())
                
            if(client.getbc() > server.getbc()):
                server.setbc(client.getbc())
