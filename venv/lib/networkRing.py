import random
from container import *
import multiprocessing
import numpy as np
import random

node_list = []

def print_chains():
    print("====================================================================")
    for i in range(len(node_list)):      
        node = node_list[i]
        print("Node " + str(node.get_port()) + " blockchain: " + str(node.get_bc()))

for i in range(8000, 8005):
    print("My port: " + str(i) + ". Peers: " + str(i+2) + ", " + str(i+1))
    node_list.append(Node(i, i+2, i+1, False))
node_list.append(Node(8005, 8001, 8000, False))
print("My port: " + str(8005) + ". Peers: " + str(8000) + ", " + str(8001))

while True:
    time.sleep(1)
    print_chains()

