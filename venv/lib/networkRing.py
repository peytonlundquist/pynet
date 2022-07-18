import copy
import itertools
import random
from container import *
import multiprocessing
import numpy as np
import random

# https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
def dict_hash(dictionary: Dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()

node_list = []

def print_chains():
    print("====================================================================")
    for i in range(len(node_list)):      
        node = node_list[i]
        if(len(node.get_bc()) < 12):
            print("Node " + str(node.get_port()) + " blockchain: " + str(node.get_bc()))
        else:
            bc_copy = copy.deepcopy(node.get_bc())
            dict(itertools.islice(bc_copy.items(), 12))
            print("Node " + str(node.get_port()) + " blockchain hash (first 12 blocks): " + dict_hash(dict(itertools.islice(bc_copy.items(), 12))))

for i in range(8000, 8006):
    print("My port: " + str(i) + ". Peers: " + str(i+2) + ", " + str(i+1) + ", " + str(i-1))
    node_list.append(Node(i, i+2, i+1, i-1, False))
node_list.append(Node(8006, 8001, 8000, 8005, False))
print("My port: " + str(8005) + ". Peers: " + str(8000) + ", " + str(8001) + ", " + str(8004))

while True:
    time.sleep(1)
    print_chains()

