from typing import Callable, Optional
from .TO_socket import TOSocket
from .utils import MessageType, Message, PriorityQueue
from threading import Lock


class TotallyOrderedNode:
    def __init__(self, id, addr_map, delivery_handler: Callable):
        self.id = id
        self.all_nodes = list(addr_map.keys())
        self.delivery_handler = delivery_handler
        self.to_socket = TOSocket(id, addr_map, handle_read=self.receive_message)

        self.lc = float(f"0.{id}")
        self.lc_lock = Lock()

        self.priority_queue = PriorityQueue()
        self.to_socket.run()

    @property
    def other_nodes(self):
        return [node_id for node_id in self.all_nodes if node_id != self.id]

    def update_lc(self, new_value: Optional[float] = None):
        with self.lc_lock:
            self.lc = max(int(self.lc), int(new_value or 0)) + 1 + float(f"0.{self.id}")
            return self.lc

    def _broadcast(self, msg):
        # broadcast, excluding self
        for node_id in self.other_nodes:
            self.to_socket.send_message_to_node(node_id, msg)

    def broadcast_message(self, msg, is_ack: bool = False):
        new_lc = self.update_lc()
        msg = Message(
            lc=new_lc,
            sender=self.id,
            msg_type=MessageType.MESSAGE,
            msg_text=msg,
        )
        # push local messages to PQ as soon as generated
        self.priority_queue.push(msg)

        print(f"node-{self.id} : Broadcasting msg with LC : {new_lc}")
        self._broadcast(str(msg))
       
    def _ack_and_deliver_if_possible(self):
        "Call this function whenever there is a change is made to the PQ"
        keep_going = True
        while keep_going:
            top = self.priority_queue.top
            if top:
                if self.id not in top.acks:
                    msg = str(Message(lc=top.lc, sender=self.id, msg_type=MessageType.ACK))
                    top.acks.add(self.id)
                    self._broadcast(msg)
                
                if len(top.acks) == len(self.all_nodes):
                    msg = self.priority_queue.pop()
                    print(f"node-{self.id} : Delivering message with LC : {msg.lc}")
                    self.delivery_handler(self, msg.msg_text)
                else:
                    keep_going = False
            else:
                keep_going = False

    def _handle_message(self, msg):
        "Place the message in your priority queue, and ack the head if not already done"
        existing_entry = self.priority_queue.find_by_lc(msg.lc)
        if existing_entry:
            existing_entry.msg_text = msg.msg_text
        else:
            self.priority_queue.push(msg)

        self._ack_and_deliver_if_possible()

    def _handle_ack_message(self, msg):
        """
        Find the msg in the priority queue and add the ack. If all acked, then **deliver** and pop
        If popped, broadcast ACK for the next top. If all acked, then **deliver** and pop
        continue same till break
        """
        msg_entry = self.priority_queue.find_by_lc(msg.lc)
        if not msg_entry:  # received ACK for a message not in the PQ (not received / already delivered)
            self.priority_queue.push(msg)
            msg_entry = msg
        msg_entry.acks.add(msg.sender)

        self._ack_and_deliver_if_possible()

    # Used as callback. Pass this function to TOSocket object as the read_handler
    def receive_message(self, msg_str):
        msg = Message.from_string(msg_str)
        self.update_lc(new_value=msg.lc)

        if msg.msg_type == MessageType.ACK:
            print(f"node-{self.id} : Received ACK from {msg.sender} with LC : {msg.lc}")
            self._handle_ack_message(msg)
        else:
            print(f"node-{self.id} : Received MESSAGE with LC : {msg.lc}")
            self._handle_message(msg)
        
        print(f"node-{self.id} : ", self.priority_queue.get_stats())
