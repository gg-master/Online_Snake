import json
import websocket


class Network(websocket.WebSocket):
    def __init__(self):
        super().__init__()
        # self.addr = "ws://localhost:8080"
        self.addr = "ws://my-server-on-websockets.herokuapp.com"

        self.conn_resp = self.connect_to_server()

    def get_conn_resp(self):
        return self.conn_resp

    def connect_to_server(self):
        try:
            self.connect(self.addr)
            return self.recv()
        except Exception as e:
            print(e)

    def send_get(self, data):
        try:
            self.send(json.dumps(data))
            data = json.loads(self.recv())
            print(data)
            return data
        except Exception as e:
            print(e)
