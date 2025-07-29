# network.py
import socket
import threading
import json
from config import PORT

class P2PNode:
    def __init__(self, name, is_host, host_ip=None):
        self.name = name
        self.is_host = is_host
        self.peers = []
        self.messages = []
        self.running = True

        if is_host:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(("", PORT))
            self.server.listen(4)
            threading.Thread(target=self.accept_connections, daemon=True).start()
        else:
            self.server = None
            self.connect_to_host(host_ip)

    def accept_connections(self):
        while self.running:
            conn, _ = self.server.accept()
            self.peers.append(conn)
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def connect_to_host(self, host_ip):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((host_ip, PORT))
        self.peers.append(conn)
        threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def handle_client(self, conn):
        while self.running:
            try:
                data = conn.recv(4096)
                if data:
                    mensajes = data.decode().split("\n")
                    for mensaje in mensajes:
                        if mensaje.strip():
                            self.messages.append(json.loads(mensaje))
            except:
                break

    def send_to_all(self, data_dict):
        data = json.dumps(data_dict) + "\n"
        for p in self.peers:
            try:
                p.sendall(data.encode())
            except:
                pass

    def get_messages(self):
        msgs = self.messages[:]
        self.messages = []
        return msgs
