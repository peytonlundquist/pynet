import io
from container import *

myPort = int(input("My port: "))
peerPort1 = int(input("Peer port: "))
peerPort2 = int(input("Peer port: "))

Node(myPort, peerPort1, peerPort2)