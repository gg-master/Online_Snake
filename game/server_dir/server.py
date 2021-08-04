import os
import re
import socket
from _thread import *
import pickle
from pyngrok import ngrok, conf
from tools.files import check_config_file

"""
На данный момент код сервера находится в состоянии разработки и тестирования 
и расчитан на подключение не более чем одного (1) человека.
"""


class Server(socket.socket):
    def __init__(self, host='0.0.0.0', port=9090):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        # Данные, которые необходимо будет отправлять подключившемуся игроку
        self.send_data = None
        # Данные, которые прислал подключившийся игрок
        self.received_data = None
        # Запоминаем IP подключившегося игрока для дальнейшей работы с ним
        # В данный момент игра будет для 2 игроков,
        # поэтому подключившийся игрок может быть лишь 1
        self.connected_users = {}
        self.max_connected_users = 1

        # {'r': (rhost, rport), 'c': (addr)}
        self.last_connected_user = {'r': [], 'c': ()}

        host = socket.gethostname()
        print(host)
        self.bind((host, port))
        # self.tunnel = self.create_tunnel(port)
        self.tunnel = None
        self.listen(1)

        # self.code = self.create_code()
        self.code = '123'
        print('\nSERVER IS RUNNING\n')
        print(self.tunnel)
        start_new_thread(self.start_listening, ())

    def create_tunnel(self, port):
        try:
            config_file_path = 'game\\server_dir\\.config\\config.yml'
            check_config_file(config_file_path)
            conf.get_default().config_path = config_file_path
            conf.get_default().log_event_callback = self.log_callback
            return ngrok.connect(port, 'tcp')
        except Exception as e:
            raise e

    def get_code(self):
        return self.code if str(self.code).isdigit() else None

    def create_code(self):
        pub_url = self.tunnel.public_url.split(':')
        return pub_url[1][2] + pub_url[-1]

    def log_callback(self, log):
        regex = re.compile(r"\b(\w+)\s*=\s*([^=]*)(?=\s+\w+\s*=|$)")
        log = dict(regex.findall(str(log)))
        self.ger_rngrok_data(log)

    def ger_rngrok_data(self, log):
        """
        Получение ip с которго было произведено подключение и номер порта
        :param log: логи ngrok
        :return:
        """
        r = log.get('r')
        if r is not None:
            rhost, rport = r.strip('"').split(':')
            self.last_connected_user['r'] = [rhost, int(rport)]

    def set_send_data(self, data):
        self.send_data = data

    def get_received_data(self):
        return self.received_data

    def isready(self):
        """
        Подключился ли второй игрок и можно ли начинать игру
        :return:
        """
        if len(self.connected_users) == 1:
            return True
        return False

    def disconnect(self):
        self.close()

    def start_listening(self):
        while True:
            conn, addr = self.accept()
            self.last_connected_user['c'] = addr
            print(f'Connected to: {addr} // '
                  f'{self.last_connected_user["r"]}')
            # Запоминаем игрока с которым шла игра
            if len(self.connected_users) < self.max_connected_users:
                self.connected_users[conn] = self.last_connected_user

            start_new_thread(self.threaded_client, (conn,))

    def threaded_client(self, conn):
        conn.send(str.encode('Успешное подключение\n'))
        while True:
            try:
                # self.received_data = conn.recv(2048).decode()
                self.received_data = pickle.loads(conn.recv(2048))
                if not self.received_data:
                    break
                else:
                    # print(self.received_data)
                    # conn.sendall(str.encode('отправленные данные\n'))
                    conn.sendall(pickle.dumps(self.send_data))
            except Exception as e:
                print(e)
                break
        print("------ Lost connection ------")
        try:
            pl = self.connected_users.pop(conn)
            print(f"Игрок {pl['r']} вышел")
        except Exception as e:
            print(e)
            pass

        conn.close()
