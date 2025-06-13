from .utils import NAMES_ID_MAP


class Player:
    def __init__(self, name):
        self.name = name
        self.id = NAMES_ID_MAP[name]


class Game:
    def __init__(self, bot):
        self.bot = bot
        self.ctx = None
        self.running = False
        self.players = []
        self.task = None

    def start_game(self, ctx):
        self.running = True
        self.ctx = ctx

    def end_game(self):
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()

    def is_running(self):
        return self.running
