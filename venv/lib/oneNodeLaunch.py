import io
from container import *

myPort = int(input("My port: "))
peerPort1 = int(input("Peer port: "))
peerPort2 = int(input("Peer port: "))
if input("Verbose: ") == "True":
    verbose = True
    print(verbose)
else:
    verbose = False

Node(myPort, peerPort1, peerPort2, verbose)