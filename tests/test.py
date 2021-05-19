from node import TotallyOrderedNode
from concurrent.futures import ThreadPoolExecutor
import time
import random
import sys
from signal import signal, SIGINT
from node import TotallyOrderedNode

n_nodes = 3
addr_map = {i: ("localhost", 1233+i) for i in range(1, n_nodes + 1)}

def delivery_handler(obj, msg):
    delivered[obj.id].append(f"{msg.msg_text}")

nodes = {i:TotallyOrderedNode(i, addr_map, delivery_handler) for i in addr_map}
delivered = {i: [] for i in addr_map}


def sig_handler(signal_received, frame):
    for node in nodes.values():
        try:
            node.to_socket.close()
        except Exception as e:
            pass
    sys.exit(0)

signal(SIGINT, sig_handler)


def run(node_id):
    for i in range(1, 11):
        time.sleep(random.randint(1, 5))
        msg = f"message-{i} from node-{node_id}"
        nodes[node_id].broadcast_message(msg)
        
def test_ordered_delivery():
    with ThreadPoolExecutor(max_workers=n_nodes) as executor:
        tasks = [executor.submit(run, node_id=node) for node in nodes]
    for task in tasks:
        task.result()
    
    time.sleep(5)
    for node, d in delivered.items():
        print(node)
        for m in d:
            print(m)


if __name__ == "__main__":
    test_ordered_delivery()