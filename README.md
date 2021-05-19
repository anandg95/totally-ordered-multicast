# Totally Ordered Multicast Algorithm

FIFO totally ordered multicast protocol using broadcast (no single sequencer)

## Description

This is an implementation of the ISIS Total Order Multicast protocol. This protocol does not rely on a single process to act as a sequencer, but relies on broadcasting acknowledgement from each process to ensure ordering. This is the algorithm in short:
- All processes use Lamport's clock, which ticks once for a local event, and updates itself using the lamport's clock of incoming messages
- A process upon generating a message, will broadcast it to all other nodes (including self)
- When a process receives a message, it is placed in a priority queue based on its clock.
- All processes broadcast the ACK for the message which is at the top of their priority queue
- If the item at the top of the queue has been ACKed by all processes, the message can be delivered

### Shortcomings

- This algorithm assumes the reliable delivery of messages in FIFO order. By using TCP sockets, reliable and FIFO communication can be ensured. But in cases where there are connectivity issues, then a retry mechanism should be integrated into the system
- If one of the nodes go down, progress as a whole is stalled. This is not a shortcoming of this implementation, rather a property of ISIS total order broadcast as a whole.

### Low level details
- The implementation of the basic logic for a `node` in the network is written in `node/core.py:TotallyOrderedNode`
- Under the hood, all `nodes` use TCP sockets to communicate with each other. Each process has a listener socket through which it accpets incoming connections. The interfaces for the communication, such as starting a listener, accepting connections, receiving and sending messages over established connections etc is abstracted in `node/TO_socket.py:TOSocket`
- `TOSocket` uses `select` to detect pending reads on open sockets. If a socket is available for read, then the message is `recv`ed and handled using the `read_handler` callable attribute. The `read_handler` should be implemented in the `TotallyOrderedNode` defining operations when a message is read from a socket. This is passed as a callback to the `TOSocket` object, from where it is invoked.  This happens in a separate thread.
- In the main thread, the `TotallyOrderedNode` processes generate their messages, and broadcast them to all other nodes using the corresponding `TOSocket` object. Message generating is application specific, so it should be implemented by the module that uses `TotallyOrderedNode`. Refer to `tests/test.py` for better understanding.
- How delivered messages are handled are also application specific. So a `handle_delivery` function is to be defined by the user and then passed as an attribute to `TotallyOrderedNode` at the time of instantiation. It is used as a callback.

**Refer `tests/test.py` for better understanding on how the module is to be used**

## Testing the module

- In the test script, the `TotallyOrderedNode` class is imported and 3 (default) nodes are created with unique listener ports. The 3 nodes are then run on different threads (to simulate different processes). Each node-thread generates messages in random intervals and uses the underlying `broadcast` implementation to send it to all nodes.
- The `handle_delivery` callback has been implemented as a simple list that appends messages in the order in which they are delivered. There is a different list for each node-thread, and at the end we compare the delivery orders on all processes to ensure that they are in the same order.
- Now that the idea behind the tests have been conveyed, let us run the tests. From the repo root run `python3 -m tests.test`
- If the test is successful, a `Test successful` message is displayed along with the total order in which messages got delivered.
- Do `Ctrl+c` to stop the test script after it is done running (To kill background threads)