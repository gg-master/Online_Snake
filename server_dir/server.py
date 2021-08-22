import asyncio
import random
import string
import time

import websockets
import logging
import json

from tools.myexceptions import LobbyNotFound, JoiningFailed

logging.basicConfig(level=logging.INFO)


class Lobby:
    def __init__(self, server):
        self.server = server
        self.code = self.create_code()

        self.connected_players = []
        self.max_connected_users = 5

        server.add_new_lobby(self)
        print(f'Lobby created // code: {self.code}')

    def get_users_data(self, except_user):
        if len(self.connected_players) == 1:
            return None
        return {i.number: i.get_data() for i in
                self.connected_players if i != except_user}

    def set_user_number(self, user):
        used_numbers = [i.number for i in self.connected_players if i != user]
        for number in range(1, self.max_connected_users + 1):
            if number not in used_numbers:
                user.set_number(number)
                break

    def create_code(self):
        symbols = list(string.digits)
        code = ''.join(random.sample(symbols, 6))
        while self.server.check_lobbies_code(code):
            code = ''.join(random.sample(symbols, 6))
        return code

    def get_code(self):
        return self.code

    def join_user(self, user):
        if len(self.connected_players) < self.max_connected_users:
            self.connected_players.append(user)
            user.set_lobby(self)
            self.set_user_number(user)
            print(f'User successful joined to {self}')
            return True
        raise JoiningFailed('Присоединение к лобби невозможно. '
                            'Слишком много игроков')

    def exist_conn_players(self):
        return bool(self.connected_players)

    def remove_user(self, user):
        self.connected_players.remove(user)
        user.disconnect()
        if not self.exist_conn_players():
            self.server.remove_lobby(self)

    def __str__(self):
        return f'Lobby {self.code}'

    def __repr__(self):
        return self.__str__()


class User:
    def __init__(self, socket):
        self.socket = socket
        self.addr = socket.remote_address[:2]

        self.lobby = None

        self.number = None
        self.data = None

    def set_data(self, data):
        # Тестовый вариант
        if data['eat_food']:
            data['eat_food'] = time.time()
        self.data = data

    def get_data(self):
        return self.data

    def get_addr(self):
        return self.addr

    def set_number(self, number):
        self.number = number

    def set_lobby(self, lobby: Lobby):
        self.lobby = lobby

    def disconnect(self):
        self.data = self.lobby = None

    @staticmethod
    def get_received_data(msg):
        return json.loads(msg)

    async def send_data(self, data=None, command=None):
        if data is None and command is not None:
            # Успешное подключение к серверу
            if command == 'success_conn':
                data = {'type': 'conn', 'conn': 'success'}
            # Успешное создание лобби
            elif command == 'lobby_code':
                data = {'type': 'lobby', 'lobby': 'success_created',
                        'lobby_code': self.lobby.get_code()}
            # Успешное подключение к лобби
            elif command == 'success_joining':
                data = {'type': 'lobby', 'lobby': 'joining_success',
                        'lobby_code': self.lobby.get_code(),
                        'number': self.number}
            elif command == 'NoneTypeData':
                data = {'type': 'except', 'except': 'NoneTypeData'}
            elif command == 'debug':
                data = {'type': 'debug', 'debug': 'отправленные данные'}
        await self.socket.send(json.dumps(data))

    def __str__(self):
        return f'User {self.addr}'


class Server:
    def __init__(self):
        self.lobbies = {}  # "code of lobby": lobby_object
        self.users = set()

    def get_lobby_by_code(self, code):
        if code not in self.lobbies:
            raise LobbyNotFound('Лобби не найдено. Лобби или несуществует или '
                                'был неправильно введен пароль')
        return self.lobbies[code]

    def check_lobbies_code(self, code: str) -> bool:
        return code in self.lobbies

    def add_new_lobby(self, lobby):
        self.lobbies[lobby.get_code()] = lobby

    def remove_lobby(self, lobby):
        del self.lobbies[lobby.get_code()]

    def remove_user(self, user):
        self.users.remove(user)
        if user.lobby is not None:
            user.lobby.remove_user(user)

    @staticmethod
    def get_port():
        # return os.getenv('WS_PORT', '8765')
        # return int(os.environ["PORT"])
        return 8080

    @staticmethod
    def get_host():
        # return os.getenv('WS_HOST', 'localhost')
        return ''

    def start(self):
        logging.info('SERVER IS RUNNING')
        return websockets.serve(self.handler, self.get_host(), self.get_port())

    async def handler(self, websocket, path):
        # print(f'Users: {self.users} // Lobbies: {self.lobbies}')
        user = User(websocket)
        self.users.add(user)
        print(f'Connected to: {user.get_addr()}')
        await user.send_data(command='success_conn')
        while True:
            try:
                received_data = user.get_received_data(await websocket.recv())
                print(f"{received_data}")
                if received_data is None:
                    await user.send_data(command='NoneTypeData')
                    continue
                # Если была подана команда на создание лобби, то создаем его
                if received_data['type'] == 'create_lobby':
                    lobby = Lobby(self)
                    lobby.join_user(user)
                    await user.send_data(command='lobby_code')
                elif received_data['type'] == 'join_player':
                    code = received_data['lobby_code']
                    try:
                        lobby = self.get_lobby_by_code(code)
                        lobby.join_user(user)
                        await user.send_data(command='success_joining')
                    except Exception as e:
                        await user.send_data({'type': 'except',
                                              'except': str(e)})
                elif received_data['type'] == 'game_data':
                    if user.lobby is None:
                        await user.send_data({'type': 'except',
                                              'except': 'Лобби не найдено'})
                        continue
                    user.set_data(received_data['data'])
                    await user.send_data(user.lobby.get_users_data(user))
                else:
                    await user.send_data(command='debug')
            except Exception as e:
                print(e)
                break
        print("------ Lost connection ------")
        try:
            self.remove_user(user)
            print(f"{user} вышел")
            # print(f'Users: {self.users} // Lobbies: {self.lobbies}')
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    ws = Server()
    asyncio.get_event_loop().run_until_complete(ws.start())
    asyncio.get_event_loop().run_forever()

# async def hello(websocket, path):
#     while True:
#         data = await websocket.recv()
#         if not data:
#             break
#         print(f"< {data}")
#
#         await websocket.send('отправленные данные')
#
#
# start_server = websockets.serve(hello, "localhost", 8765)
#
# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()
