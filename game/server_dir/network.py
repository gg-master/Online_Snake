import socket
import pickle


class Network:
    def __init__(self, server_code: str):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server = f"{server_code[0]}.tcp.ngrok.io"
        self.server = 'DESKTOP-2BJGC44'

        # self.port = int(server_code[1:])
        self.port = 9090
        self.addr = (self.server, self.port)
        self.conn_resp = self.connect()

    def get_coon(self):
        return self.conn_resp

    def connect(self):
        try:
            self.client.connect(self.addr)
            return self.client.recv(1024).decode()
        except Exception as e:
            print(e)

    def send_get(self, data):
        try:
            self.client.send(pickle.dumps(data))
            # return self.client.recv(4096).decode()
            data = self.client.recv(2048)
            print(data)
            return pickle.loads(data)
        except socket.error as e:
            # print(e)
            pass
