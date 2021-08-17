import os
import socket

import pygame
import random
from menu_cl import MainMenu, ErrorWindow
from network import Network

from tools import resourcePath, get_time


class Client:
    def __init__(self, screen):
        self.screen = screen
        self.menu = MainMenu(self, screen.get_size())
        self.type_game = None
        self.game = None

    def update(self, event=None):
        if event is not None:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.reset_game()
        if self.type_game is None or not self.type_game:
            self.menu.update(event)
        else:
            type_game = list(map(int, self.type_game.split('_')))
            if self.game is None:
                if type_game[0] == 1:
                    self.game = GameOffline(self.screen.get_size())
                if type_game[0] == 2:
                    try:
                        self.game = GameOnline(self.screen.get_size(),
                                               type_game)
                    except (ConnectionRefusedError, socket.gaierror) as e:
                        self.reset_game()
                        self.menu = ErrorWindow(self, self.screen.get_size(),
                                                'Неудалось подключиться к '
                                                'серверу. Проверьте состояние '
                                                'интернета и попробуйте снова')
                    except Exception as e:
                        self.reset_game()
                        self.menu = ErrorWindow(self, self.screen.get_size(),
                                                str(e))
            if self.game is not None:
                self.game.update(event)

    def render(self, screen):
        if self.type_game is None:
            self.menu.draw(screen)
        else:
            if self.game is not None:
                self.game.draw(screen)

    def reset_game(self):
        if self.type_game is not None and self.game is not None:
            if self.type_game.startswith('2'):
                self.game.disconnect()
        self.type_game = self.game = None


class Game:
    def __init__(self, screen_size, player_number):
        self.player_number = player_number - 1
        print(os.getcwd())
        self.font = pygame.font.Font(resourcePath('.fonts/arial.ttf'), 25)
        self.pl_text = None

        self.w, self.h = screen_size
        self.map = pygame.Rect(0, 60, self.w, self.h - 60)

        self.players_pos = [
            (self.map.w // 2, self.map.y + 20),
            (self.map.w // 2, self.map.y + self.map.h - 50),
            (self.map.x + 20, self.map.y + self.map.h // 2),
            (self.map.x + self.map.w - 50, self.map.y + self.map.h // 2),
            (self.map.w // 2, self.map.y + self.map.h // 2)
        ]
        self.players_color = [
            pygame.Color('cyan'), pygame.Color('blue'),
            pygame.Color('purple'), pygame.Color('pink'),
            pygame.Color('turquoise')
        ]

        self.player = Snake(self, self.players_pos[self.player_number],
                            pygame.Color('green'))

        self.food = Food(self.map)

    def update(self, event=None):
        if event is not None:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    eat_food = self.player.eat_food
                    if not self.player.alive():
                        self.player = Snake(
                            self, self.players_pos[self.player_number],
                            pygame.Color('green'))
                    # Устанавливаем игроку флаг о еде.
                    self.player.eat_food = eat_food
        self.pl_text = self.font.render(f'Alive | {self.player.points} points'
                                        if self.player.alive() else
                                        f'Died | {self.player.points} points '
                                        f'| press "R" to restart',
                                        True, pygame.Color('red'))
        self.player.update()

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.map)
        screen.blit(self.pl_text, (self.w // 2 -
                                   self.pl_text.get_rect().w // 2, 30))
        self.player.draw(screen)
        self.food.draw(screen)

    def spawn_new_food(self):
        self.food.respawn()


class GameOffline(Game):
    def __init__(self, screen_size):
        super().__init__(screen_size, 1)

    def update(self, event=None):
        super().update(event)
        if not self.food.alive():
            self.spawn_new_food()

    def draw(self, screen):
        super().draw(screen)


class GameOnline(Game):
    def __init__(self, screen_size, type_game: list):
        self.num_pl = type_game[1]

        code_font = pygame.font.Font(resourcePath('.fonts/arial.ttf'), 20)
        # Создаем класс, который будет общаться с сервером
        self.netw = Network()

        # Получаем ответ об успешном подключении
        while self.netw.get_conn_resp() is None:
            if self.netw.exception is not None:
                raise self.netw.exception
        print(self.netw.get_conn_resp())

        # Если мы являемся хостом (игроком № 1 в лобби) то сервер нам
        # возвращает код лобби, который отображается в правом верхнем углу
        if self.num_pl == 1:
            super().__init__(screen_size, self.num_pl)

            self.netw.set_send_get_recv({'type': 'create_lobby'})
            server_resp = self.netw.wait_received_data('lobby_code')

            self.player.eat_food = True
        # Если игрок является №2 в лобби, то игрок отсылая код лобби,
        # присоединяется к лобби
        else:
            self.netw.set_send_get_recv({'type': 'join_player',
                                         'lobby_code': str(type_game[-1])})

            server_resp = self.netw.wait_received_data('lobby_code',
                                                       'number')
            super().__init__(screen_size, server_resp['number'])

            # Убиваем еду, чтобы установить новое значение от хоста
            self.food.kill()
        print(server_resp)
        self.code = code_font.render(f'{server_resp["lobby_code"]}', True,
                                     pygame.Color('white'))

        self.other_players = {}

    def draw(self, screen):
        super().draw(screen)
        screen.blit(self.code, (self.w - self.code.get_rect().w - 10, 10))
        for player in self.other_players.values():
            player.draw(screen)

    def update(self, event=None):
        super().update(event)
        # Если мы съели еду, то респавним ее
        if not self.food.alive() and self.player.eat_food:
            self.spawn_new_food()
        # Создаем данные, которые отправятся на сервер
        data = {'type': 'game_data', 'data': self.create_data()}
        self.set_data(self.netw.set_send_get_recv(data))

    def create_data(self):
        # Создаем данные для отправки на сервер
        data = self.player.get_data()
        # Если наш игрок съел еду, то добавляем в словарь данные о еде
        if self.player.eat_food:
            data.update(self.food.get_data())
        return data

    def set_data(self, data):
        # Из полученных данных с сервера истанавливаем состояния
        # для еды и игрока
        if data is not None and 'type' not in data:
            self.create_players(data)
            for k, v in data.items():
                self.other_players[k].set_data(v)
            print(
                f'1 {self.player} // {"/".join([f"{k}: {v}" for k, v in self.other_players.items()])}')
            # Если игрок съел еду и другой игрок съел еду, а также если
            # другой игрок сигнализирует, что он сел еду недавно, то мы
            # изменяем состояние себя и начинаем считать, что наш игрок не
            # ел последнюю еду
            if self.player.eat_food and any(
                    map(lambda player:
                        player.eat_food and player.callbacks['eat_callback'],
                        self.other_players.values())):
                if self.player.callbacks['eat_callback'] and (
                        self.player.callbacks['eat_callback'] <
                        self.get_pl_by_lambda(
                                lambda p: p.eat_food and p.callbacks[
                                    'eat_callback']).callbacks[
                            'eat_callback']):
                    self.player.set_callbacks(eat_callback=False)
                    self.player.eat_food = False
                elif not self.player.callbacks['eat_callback']:
                    self.player.eat_food = False
            # Если мы с сервера получили онформацию, что другой игрок
            # изменил свое состояние
            # (т.е получил наше сообщение о том, что мы съели еду),
            # то выключаем коллбэк
            if self.player.eat_food and all(map(lambda pl: not pl.eat_food,
                                                self.other_players.values())):
                self.player.set_callbacks(eat_callback=False)
            # Если наш игрок не ел еду, то мы устанавливаем ему
            # значения принятые из сервера
            if not self.player.eat_food and any(
                    map(lambda pl: pl.eat_food, self.other_players.values())):
                arr = sorted(self.other_players,
                             key=lambda x:
                             (x.callbacks['eat_callback'], int(x.eat_food)),
                             reverse=True)
                if arr:
                    self.food.set_data(arr[0])
            print(
                f'2 {self.player} // {"/".join([f"{k}: {v}" for k, v in self.other_players.items()])}')

        # Если игрок еще жив(отрисовывается на карте), а данные с сервера не
        # поступают, то мы убиваем этого игрока.
        # Т.е считаем его за отключившегося
        self.check_disc_players(data)

    def get_pl_by_lambda(self, func):
        for i in self.other_players.values():
            if func(i):
                return i

    def check_disc_players(self, data):
        if data is None:
            self.other_players = {}
        else:
            self.other_players = {
                i: self.other_players[i] for i in
                filter(lambda k: self.other_players[k].alive() and k in data,
                       self.other_players.keys())}
        if not self.other_players and self.netw.is_get_first_msg:
            self.player.eat_food = True

    def disconnect(self):
        self.netw.disconnect()

    def create_players(self, data):
        for i in data.keys():
            if i not in self.other_players:
                num_pl = int(i) - 1
                snake = Snake(
                    self, self.players_pos[num_pl],
                    self.players_color[num_pl])
                snake.kill()
                self.other_players[i] = snake


class Snake:
    def __init__(self, game, pos, color):
        available_side = {0: 'right', 1: 'right', 2: 'down',
                          3: 'up', 4: 'right'}
        self.game = game
        self.side = available_side[game.player_number]
        self.speed = self.w = self.h = 15

        self.head = pygame.Rect(pos, (self.w, self.h))
        self.parts = [pygame.Rect((pos[0] - (self.w * (i + 2)), pos[1]),
                                  (self.w, self.h))
                      for i in range(2)]

        self.color = color
        self.killed = False

        self.eat_food = False
        self.callbacks = {'eat_callback': False}

        self.difficult_delta = 2
        self.points = 0

        self.delay = 150
        self.start_timer = pygame.time.get_ticks()

    def get_data(self):
        data = {
            'killed_sn': self.killed,
            'eat_food': self.eat_food
        }
        data.update(self.callbacks)
        if not self.killed:
            data.update(
                {
                    'head': (self.head.x, self.head.y),
                    'parts': [[i.x, i.y] for i in self.parts]
                })
        return data

    def set_data(self, data):
        if data is None:
            return None
        self.killed = data['killed_sn']
        self.eat_food = data['eat_food']
        self.set_callbacks(eat_callback=data['eat_callback'])
        if not self.killed:
            self.head.x, self.head.y = data['head']
            self.parts = [pygame.Rect((i[0], i[1]), (self.w, self.h))
                          for i in data['parts']]

    def draw(self, screen):
        if not self.killed:
            pygame.draw.rect(screen, pygame.Color('red'), self.head)
            for part in self.parts:
                pygame.draw.rect(screen, self.color, part)

    def move(self):
        for i in range(len(self.parts) - 1, 0, -1):
            part = self.parts[i]
            part.x, part.y = self.parts[i - 1].x, self.parts[i - 1].y
        self.parts[0].x, self.parts[0].y = self.head.x, self.head.y

        if self.side == 'right':
            self.head = self.head.move(self.speed, 0)
        elif self.side == 'left':
            self.head = self.head.move(-self.speed, 0)
        elif self.side == 'up':
            self.head = self.head.move(0, -self.speed)
        elif self.side == 'down':
            self.head = self.head.move(0, self.speed)
        # print(self.head, self.parts)
        self.check_collide()

    def check_collide(self):
        if self.head.left < self.game.map.left:
            self.head.right = self.game.map.right
        if self.head.right > self.game.map.right:
            self.head.left = self.game.map.left
        if self.head.top < self.game.map.top:
            self.head.bottom = self.game.map.bottom
        if self.head.bottom > self.game.map.bottom:
            self.head.top = self.game.map.top
        if any(map(lambda x: self.head.colliderect(x), self.parts)):
            self.kill()
        if self.head.colliderect(self.game.food.rect):
            self.eating_food(self.game.food)

    def eating_food(self, food):
        self.eat_food = True
        # Устанавливаем коллбэк, чтобы сигнализировать другим игрокам о том,
        # что мы съели еду
        self.set_callbacks(eat_callback=get_time())
        food.kill()
        self.points += 1
        self.delay -= self.difficult_delta
        self.parts.append(self.parts[-1].copy())

    def update(self):
        now = pygame.time.get_ticks()

        if self.alive():
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and self.side != 'right':
                self.side = 'left'
            elif keys[pygame.K_RIGHT] and self.side != 'left':
                self.side = 'right'
            elif keys[pygame.K_UP] and self.side != 'down':
                self.side = 'up'
            elif keys[pygame.K_DOWN] and self.side != 'up':
                self.side = 'down'
            if now - self.start_timer > self.delay:
                # self.delay = max(0, self.delay - 5)
                self.start_timer = now
                self.move()

    def kill(self):
        self.killed = True

    def alive(self):
        return not self.killed

    def set_callbacks(self, **kwargs):
        self.callbacks.update(**kwargs)

    def __str__(self):
        return f'Snake {self.eat_food} - {self.callbacks["eat_callback"]}'

    def __repr__(self):
        return self.__str__()


class Food:
    def __init__(self, map_size):
        self.map = map_size
        self.pos = self.create_pos()
        self.w = self.h = 10
        self.rect = pygame.Rect(self.pos, (self.w, self.h))
        self.killed = False

    def get_data(self):
        return {
            'food': (self.rect.x, self.rect.y),
            'killed_fd': self.killed
        }

    def set_data(self, data):
        self.rect.x, self.rect.y = data['food']
        self.killed = data['killed_fd']

    def create_pos(self):
        return (random.randrange(self.map.left + 50, self.map.right - 50),
                random.randrange(self.map.top + 50, self.map.bottom - 100))

    def draw(self, screen):
        if self.alive():
            pygame.draw.circle(screen, pygame.Color('orange'),
                               self.rect.center, self.w)

    def kill(self):
        self.killed = True

    def alive(self):
        return not self.killed

    def respawn(self):
        self.pos = self.create_pos()
        self.rect = pygame.Rect(self.pos, (self.w, self.h))
        self.killed = False
