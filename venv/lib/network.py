import random
from container import *
import multiprocessing
import numpy as np
import random

PORT_MIN = 49153
PORT_MAX = 49163

# Create a pool of ports in random order 
portPool = list(range(PORT_MIN, PORT_MAX))
random.shuffle(portPool) 

# Assign random port to self and peers for each node
for index in portPool:
    myport = index
    port1 = random.choice(portPool)
    port2 = random.choice(portPool)
    
    # Reselect peer port if it is also myport
    while myport == port1 or myport == port2: 
        port1 = random.choice(portPool)
        port2 = random.choice(portPool)
            
    # Create a node
    Node(myport, port1, port2, True)

