import asyncio
import random
import string

import websockets
import logging
import json

from tools.myexceptions import LobbyNotFound, JoiningFailed

logging.basicConfig(level=logging.INFO)


class Lobby:
    def __init__(self, server, host):
        self.server = server
        self.host_user = host
        self.code = self.create_code()

        self.send_data = None
        self.received_data = None

        self.connected_players = []
        self.max_connected_users = 1

        print(f'Lobby created // code: {self.code}')

    def set_send_data(self, data):
        self.send_data = data

    def set_received_data(self, data):
        self.received_data = data

    def get_send_data(self):
        return self.send_data

    def get_received_data(self):
        return self.received_data

    def ishost(self, user):
        return user == self.host_user

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
            return True
        raise JoiningFailed('Joining is not possible. Too many players')

    def remove_user(self, user):
        self.connected_players.remove(user)


class User:
    def __init__(self, socket):
        self.socket = socket
        self.addr = socket.remote_address[:2]

        self.lobby = None

    def get_addr(self):
        return self.addr

    def set_lobby(self, lobby: Lobby):
        self.lobby = lobby

    @staticmethod
    def get_received_data(msg):
        return json.loads(msg)

    async def send_data(self, data=None, command=None):
        if data is None and command is not None:
            if command == 'lobby_code':
                data = {'type': 'sys', 'lobby': 'success',
                        'lobby_code': self.lobby.get_code()}
            elif command == 'debug':
                data = {'type': 'sys', 'debug_inf': 'отправленные данные'}
            elif command == 'success_conn':
                data = {'type': 'sys', 'connection': 'success'}
            elif command == 'success_joining':
                data = {'type': 'sys', 'joining': 'success'}
        await self.socket.send(json.dumps(data))

    def __str__(self):
        return f'User {self.addr}'


class Server:
    def __init__(self):
        self.lobbies = {}  # "code of lobby": lobby_object
        self.users = set()

    def get_lobby_by_code(self, code):
        if code not in self.lobbies:
            raise LobbyNotFound('Лобби не было найдено')
        return self.lobbies[code]

    def check_lobbies_code(self, code: str) -> bool:
        if code in self.lobbies:
            return True
        return False

    def add_new_lobby(self, lobby):
        self.lobbies[lobby.get_code()] = lobby

    def remove_user(self, user):
        self.users.remove(user)
        if user.lobby is not None:
            # TODO Доработать если отключается хост
            if user.lobby.ishost(user):
                del self.lobbies[user.lobby.get_code()]
            else:
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
        user = User(websocket)
        self.users.add(user)
        print(f'Connected to: {user.get_addr()}')
        await user.send_data(command='success_conn')
        while True:
            try:
                received_data = user.get_received_data(await websocket.recv())
                print(f"{received_data}")
                # Если была подана команда на создание лобби, то создаем его
                if received_data['type'] == 'create_lobby':
                    lobby = Lobby(host=user, server=self)
                    self.add_new_lobby(lobby)
                    user.set_lobby(lobby)
                    await user.send_data(command='lobby_code')
                elif received_data['type'] == 'join_player':
                    # TODO добавить проверку является ли
                    #  пользователь уже хостом лобби
                    code = received_data['lobby_code']
                    try:
                        lobby = self.get_lobby_by_code(code)
                        user.lobby = lobby if lobby.join_user(user) else None
                        await user.send_data(command='success_joining')
                    except Exception as e:
                        await user.send_data({'type': 'sys',
                                              'joining': str(e)})
                elif received_data['type'] == 'game_data':
                    if user.lobby is None:
                        await user.send_data({'type': 'sys',
                                              'lobby': 'Lobby not found'})
                        continue
                    # Если пользователь является хостом, то он устанавливает
                    # отсылаемые данные и получает received данные
                    if user.lobby.ishost(user):
                        user.lobby.set_send_data(received_data['data'])
                        await user.send_data(user.lobby.get_received_data())
                    # Если пользователь не является хостом, то от устанавливает
                    # received данные и получает send данные
                    else:
                        user.lobby.set_received_data(received_data['data'])
                        await user.send_data(user.lobby.get_send_data())
                else:
                    await user.send_data(command='debug')
            except Exception as e:
                print(e)
                break
        print("------ Lost connection ------")
        try:
            self.remove_user(user)
            print(f"{user} вышел")
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
