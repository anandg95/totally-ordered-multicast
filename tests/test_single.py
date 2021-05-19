from node import TotallyOrderedNode
import time
import random
import sys
from node import TotallyOrderedNode

n_nodes = 3
addr_map = {i: ("localhost", 1233+i) for i in range(1, n_nodes + 1)}

def run(node_id):
    node = TotallyOrderedNode(node_id, addr_map)
    time.sleep(5)
    for i in range(1, 11):
        time.sleep(random.randint(1, 3))
        msg = f"message-{i} from node-{node_id}"
        node.broadcast_message(msg)
        
      
if __name__ == "__main__":
    node_id = int(sys.argv[1])
    run(node_id)