from dataclasses import dataclass, field
from enum import EnumMeta


class MessageType(EnumMeta):
    MESSAGE = "MESSAGE"
    ACK = "ACK"

@dataclass
class Message:
    lc: int # identifier
    msg_type : MessageType
    sender: int
    msg_text: str = None
    acks: list = field(default_factory=set) # internal use, for queue

    def __repr__(self) -> str:
        return f"{self.lc};{self.msg_type};{self.sender};{self.msg_text}"

    @classmethod
    def from_string(cls, msg_str):
        lc, msg_type, sender, msg_text = msg_str.split(";")
        return cls(lc=float(lc), msg_type=msg_type, sender=sender, msg_text=msg_text)


class PriorityQueue:
    # using list
    def __init__(self, max_size=100):
        self.heap = []
    
    def find_by_lc(self, lc):
        # find a message by its Lamport Clock
        for msg in self.heap:
            if msg.lc == lc:
                return msg

   
    def push(self, msg: Message):
        self.heap.append(msg)
        self.heap.sort(key=lambda x: x.lc, reverse=True) # smallest at the end
    
    def pop(self):
        msg = self.heap.pop()
        return msg
    
    def get_stats(self):
        # list of (lc, acks)
        return [(msg.lc, msg.acks) for msg in self.heap]
    
    @property
    def top(self):
        return self.heap[-1] if self.heap else None