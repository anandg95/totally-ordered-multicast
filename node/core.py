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
    
    def update_lc(self, new_value: Optional[float]=None):
        self.lc = max(int(self.lc), int(new_value or 0)) + 1 + float(f"0.{self.id}")

    def _broadcast(self, msg):
        for node_id in self.all_nodes:
            self.to_socket.send_message_to_node(node_id, msg)    
    
    def broadcast_message(self, msg, is_ack:bool=False):
        with self.lc_lock:
            self.update_lc()
            msg = str(Message(lc=self.lc, sender=self.id, msg_type=MessageType.MESSAGE, msg_text=msg))
            print(f"node-{self.id} : Broadcasting msg with LC : {self.lc}")
            self._broadcast(msg)
            
    def _acknowledge_message(self, lc_msg):
        msg = str(Message(lc=lc_msg, sender=self.id, msg_type=MessageType.ACK))
        self._broadcast(msg)


    def _handle_message(self, msg):
        "Place the message in your priority queue, and ack the head if not already done"
        existing_entry = self.priority_queue.find_by_lc(msg.lc)
        if existing_entry:
            existing_entry.msg_text = msg.msg_text
        else:
            self.priority_queue.push(msg)
        
        if self.id not in self.priority_queue.top.acks:
            self._acknowledge_message(msg.lc)


    def _handle_ack_message(self, msg):
        """
        Find the ack in your corresponding queue entry. If all acked, then **deliver** and pop
        If popped, broadcast ACK for the next top. If all acked, then **deliver** and pop
        continue same till break
        """
        msg_entry = self.priority_queue.find_by_lc(msg.lc)
        if not msg_entry: # received ACK for a message not reached yet
            self.priority_queue.push(msg)
            msg_entry = msg
        msg_entry.acks.add(msg.sender)
        
        keep_going = True
        while keep_going:
            if self.priority_queue.top and len(self.priority_queue.top.acks) == len(self.all_nodes):
                msg = self.priority_queue.pop() # debug: check in first run, msg_entry == msg
                print(f"node-{self.id} : Delivering message with LC : {msg.lc}")
                self.delivery_handler(self, msg)
            else:
                keep_going = False

    # Used as callback. Pass this function to TOSocket object as the read_handler
    def receive_message(self, msg_str):
        with self.lc_lock:
            msg = Message.from_string(msg_str)
            self.update_lc(new_value=msg.lc)
            if msg.msg_type == MessageType.ACK:
                print(f"node-{self.id} : Received ACK from {msg.sender} with LC : {msg.lc}")
                self._handle_ack_message(msg)
            else:
                print(f"node-{self.id} : Received MESSAGE with LC : {msg.lc}")
                self._handle_message(msg)        

