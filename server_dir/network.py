import json
import random
import string
import websockets
import asyncio
from _thread import *


class Network:
    def __init__(self):
        super().__init__()
        self.addr = "ws://localhost:8080"
        # self.addr = "ws://my-server-on-websockets.herokuapp.com"

        self.send_data = None
        self.received_data = None

        self.last_vcode = ''
        self.conn_resp = None
        # Запускаем новый поток, т.к asyncio.run() является
        # блокирующей функцией
        start_new_thread(self.start_async, ())

    def wait_received_data(self, *params):
        # Ожидаем нужные данные от сервера
        # Прокручиваем полученную с сервера инфу пока не увидим нужным
        # нам в нем параметр
        # ВВЕДЕНО Для иммитирования блокировки во время подключения к серверу
        while self.received_data is None \
                or any(map(lambda x: x not in self.received_data, params)):
            pass
        return self.received_data

    def get_received_data(self):
        return self.received_data

    def get_conn_resp(self):
        return self.conn_resp

    def set_send_get_recv(self, data):
        # Генерируем уникальный код, который будет отвечает за определенную
        # версию
        # ВВЕДЕНО Чтобы отслеживать изменения данных, которые необходимо
        # отправить на сервер
        self.send_data = self.generate_version_code(data)
        return self.received_data

    @staticmethod
    def generate_version_code(data):
        symbols = list(string.ascii_uppercase + string.digits)
        data.update({'vcode': ''.join(random.sample(symbols, 6))})
        return data

    def start_async(self):
        # Запускаем асинхронную функцию, которая будет получать
        # данные с сервера
        asyncio.run(self.server_listen())

    async def server_listen(self):
        async with websockets.connect(self.addr) as socket:
            # Ответ после подключения
            self.conn_resp = json.loads(await socket.recv())
            # Начинаем отправлять данные
            while True:
                # Если изменились данные, то их необходимо отправить на сервер
                if self.send_data is not None and \
                        self.last_vcode != self.send_data['vcode']:
                    self.last_vcode = self.send_data['vcode']
                    await socket.send(json.dumps(self.send_data))
                    self.received_data = json.loads(await socket.recv())
                    # print(self.received_data)
