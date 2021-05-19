from node import TotallyOrderedNode
from concurrent.futures import ThreadPoolExecutor
import time
import random
import sys
from itertools import groupby

n_nodes = 3
addr_map = {i: ("localhost", 1233 + i) for i in range(1, n_nodes + 1)}


def delivery_handler(obj, msg):
    delivered[obj.id].append(msg)


nodes = {i: TotallyOrderedNode(i, addr_map, delivery_handler) for i in addr_map}
delivered = {i: [] for i in addr_map}


def exit_gracefully():
    for node in nodes.values():
        try:
            node.to_socket.close()
        except Exception as e:
            pass
    sys.exit(0)


def run(node_id):
    for i in range(1, 11):
        time.sleep(random.uniform(1, 5))
        msg = f"message-{i} from node-{node_id}"
        nodes[node_id].broadcast_message(msg)


def test_ordered_delivery():
    with ThreadPoolExecutor(max_workers=n_nodes) as executor:
        tasks = [executor.submit(run, node_id=node) for node in nodes]
    for task in tasks:
        task.result()

    time.sleep(5)

    # check if all values in delivered dict are equal
    g = groupby(delivered.values())
    assert next(g) and not next(g, False), "The order of delivery is different"
    print("-" * 40)
    print("Test successful. Total order is : ")
    # for ms in zip(delivered[1], delivered[2], delivered[3]):
    #     print(*ms)
    for msg in delivered[1]:
        print(msg)
    print("-" * 40)


if __name__ == "__main__":
    test_ordered_delivery()
    exit_gracefully()
