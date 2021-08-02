import socket
import pickle


class Network:
    def __init__(self, server_code: str):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = f"{server_code[0]}.tcp.ngrok.io"
        self.port = int(server_code[1:])
        self.addr = (self.server, self.port)
        self.conn_resp = self.connect()

    def get_coon(self):
        return self.conn_resp

    def connect(self):
        try:
            self.client.connect(self.addr)
            return self.client.recv(2048).decode()
        except Exception as e:
            print(e)

    def send_get(self, data):
        try:
            self.client.send(pickle.dumps(data))
            # return self.client.recv(4096).decode()
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            print(e)
