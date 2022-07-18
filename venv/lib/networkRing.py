import random
from container import *
import multiprocessing
import numpy as np
import random

node_list = []

# Create a node
for i in range(8000, 8010):
    print("My port: " + str(i) + ". Peers: " + str(i+2) + ", " + str(i+1))
    node_list.append(Node(i, i+2, i+1, False))
Node(8010, 8000, 8005, False)
print("My port: " + str(8010) + ". Peers: " + str(8000) + ", " + str(8005))



