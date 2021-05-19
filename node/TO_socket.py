"""
Implementation of asynchronous sockets using `select`. 
select is a system call and application programming interface in Unix-like and POSIX-compliant operating systems for examining the status of file descriptors of open input/output channels.
Python asyncore (standard library) also implements async sockets using `select`
Reference : https://github.com/python/cpython/blob/3.9/Lib/asyncore.py

Note that there is no async-await pattern here.
"""

import socket
import select
from typing import Callable
from threading import Thread

class TOSocket:
    def __init__(self, id, addr_map, handle_read: Callable, timeout:float=1.0) -> None:
        self.addr_map = addr_map
        self.id = id
        self.timeout = timeout # TODO : unused
        self.handle_read = handle_read
        
        # server socket
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # allow reuse
        self.server_socket.bind(addr_map[id])
        self.server_socket.listen(5)

        self.read_sockets = [] # list
        self.write_sockets = {} # dict from node_id to socket

        self.trailing_msg = ""
    

    @property
    def all_read_sockets(self):
        return list(self.read_sockets)+[self.server_socket]

    def _run(self):
        while 1:
            try:
                ready_to_read, _, __ = select.select(self.all_read_sockets, [], [], 0)
            except ValueError:
                for i, sock in enumerate(self.read_sockets):
                    if sock.fileno() == -1: # closed
                        print("popping socket ", sock)
                        self.read_sockets.pop(i)

            for sock in ready_to_read:
                if sock == self.server_socket:
                    cs, _ = self.server_socket.accept()
                    self.read_sockets.append(cs)
                else:
                    try:
                        self.receive_messages_from_socket(sock)
                    except Exception as e:
                        print("woah ", e)
                        

    def run(self):
        t = Thread(target=self._run)
        t.daemon = False
        t.start()
            

    def _connect_to_node(self, node_id):
        cs = socket.socket()
        cs.connect(self.addr_map[node_id])            
        print(f"connect successful to peer-{node_id}", cs)
        self.write_sockets[node_id] = cs    


    def send_message_to_node(self, node_id, msg: str):
        msg += "\n" # End Of Message
        existing_sock = self.write_sockets.get(node_id)
        if not existing_sock:
            try:
                self._connect_to_node(node_id)
            except ConnectionRefusedError:
                print(f"Peer-{node_id} not accepting connections")
                return 0

        self.write_sockets[node_id].send(msg.encode())
    

    def receive_messages_from_socket(self, sock, buff_size=1024):
        msgs = sock.recv(buff_size).decode()
        if not msgs:
            sock.close()
        else:
            *list_of_msgs, temp = msgs.split("\n")
            list_of_msgs[0] = self.trailing_msg + list_of_msgs[0]
            self.trailing_msg = temp
            for msg in list_of_msgs:
                self.handle_read(msg)


    def close(self):
        self.server_socket.close()
        for ws in self.write_sockets.values():
            ws.close()
        for cs in self.read_sockets:
            cs.close()
        