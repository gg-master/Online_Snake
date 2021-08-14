import pygame_gui
import pygame


class Menu:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.manager = pygame_gui.UIManager(screen_size)
        self.clock = pygame.time.Clock()
        self.btn_h = 150
        self.btn_w = 50

    def update(self, event=None):
        time_delta = self.clock.tick(60) / 1000.0
        if event is not None:
            self.manager.process_events(event)
        self.manager.update(time_delta)

    def draw(self, screen):
        self.manager.draw_ui(screen)


class MainMenu(Menu):
    def __init__(self, client, screen_size):
        super().__init__(screen_size)
        self.client = client
        self.ch_menu = None

        self.offline_game_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((screen_size[0] // 2 - self.btn_h // 2,
                                       screen_size[1] // 2.5 - self.btn_w // 2)
                                      , (self.btn_h, self.btn_w)),
            text='Offline game',
            manager=self.manager)

        self.online_game_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((screen_size[0] // 2 - self.btn_h // 2,
                                       screen_size[1] // 2 + self.btn_w // 2),
                                      (self.btn_h, self.btn_w)),
            text='Online game',
            manager=self.manager)

    def update(self, event=None):
        if event is not None:
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.offline_game_btn:
                        self.client.type_game = '1_1'
                    if event.ui_element == self.online_game_btn:
                        self.ch_menu = ChoiceMenu(
                            self.client, self.screen_size, self)
        if self.ch_menu is not None:
            self.ch_menu.update(event)
        else:
            super().update(event)

    def draw(self, screen):
        if self.ch_menu is not None:
            self.ch_menu.draw(screen)
        else:
            super().draw(screen)


class ChoiceMenu(Menu):
    def __init__(self, client, screen_size, parent):
        super().__init__(screen_size)
        self.client = client
        self.parent = parent
        self.ce_menu = None

        self.create_server_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((screen_size[0] // 2 - self.btn_h // 2,
                                       screen_size[1] // 2.5 - self.btn_w // 2)
                                      , (self.btn_h, self.btn_w)),
            text='Create server',
            manager=self.manager)

        self.join_server_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((screen_size[0] // 2 - self.btn_h // 2,
                                       screen_size[1] // 2 + self.btn_w // 2),
                                      (self.btn_h, self.btn_w)),
            text='Join server',
            manager=self.manager)

    def update(self, event=None):
        if event is not None:
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.create_server_btn:
                        self.client.type_game = '2_1'
                    if event.ui_element == self.join_server_btn:
                        self.ce_menu = CodeEntryMenu(
                            self.client, self.screen_size, self)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.parent.ch_menu = None
        if self.ce_menu is not None:
            self.ce_menu.update(event)
        else:
            super().update(event)

    def draw(self, screen):
        if self.ce_menu is not None:
            self.ce_menu.draw(screen)
        else:
            super().draw(screen)


class CodeEntryMenu(Menu):
    def __init__(self, client, screen_size, parent):
        super().__init__(screen_size)
        self.client = client
        self.parent = parent

        self.line_h = 200
        self.line_w = 50

        self.line = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((screen_size[0] // 2 - self.line_h // 2,
                                       screen_size[1] // 2 - self.line_w // 2),
                                      (self.line_h, self.line_w)),
            manager=self.manager)

        self.line.set_text('Ведите код сервера')
        self.line.set_allowed_characters(['1', '2', '3', '4', '5',
                                          '6', '7', '8', '9', '0'])

        self.join_server_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((screen_size[0] // 2 - self.btn_h // 2,
                                       screen_size[1] // 2 + self.btn_w // 2),
                                      (self.btn_h, self.btn_w)),
            text='Start',
            manager=self.manager)

    def update(self, event=None):
        if event is not None:
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.join_server_btn:
                        text = self.line.get_text()
                        if self.line.validate_text_string(text):
                            self.client.type_game = f'2_2_{text}'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.parent.ce_menu = None
        super().update(event)


class ErrorWindow(Menu):
    def __init__(self, client, screen_size, text):
        super().__init__(screen_size)
        self.client = client

        self.line_h = 200
        self.line_w = 50

        self.label = pygame_gui.elements.ui_label.UILabel(
            relative_rect=pygame.Rect((0, 0),
                                      (screen_size[0], self.line_h)),
            text=text,
            manager=self.manager)

        self.back_to_menu_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((screen_size[0] // 2 - self.btn_h // 2,
                                       screen_size[1] // 2 + self.btn_w // 2),
                                      (self.btn_h, self.btn_w)),
            text='В меню',
            manager=self.manager)

    def update(self, event=None):
        if event is not None:
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.back_to_menu_btn:
                        self.client.menu = MainMenu(self.client,
                                                    self.screen_size)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.client.menu = MainMenu(self.client,
                                                self.screen_size)
        super().update(event)
