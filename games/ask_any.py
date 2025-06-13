import asyncio
import discord
import random
from .utils import NAMES_ID_MAP
from .Game import Player, Game


class Askany_Player(Player):
    def __init__(self, name):
        super().__init__(name)
        self.response = None  # stores 'Y' or 'N'
        self.guess = None     # stores their guess of total Y

    def clean_answers(self):
        self.response = None
        self.guess = None


class Askany_Game(Game):
    def __init__(self, bot, people_out_of_party):
        super().__init__(bot)
        self.players = [Askany_Player(m) for m in NAMES_ID_MAP.keys() if m not in people_out_of_party]
        self.total_players = len(self.players)
        self.default_questions = None

    def start_game(self, ctx):
        super().start_game(ctx)
        self.default_questions = self._load_default_questions()

    def end_game(self):
        super().end_game()
        self.default_questions = None

    def _load_default_questions(self):
        with open(f'./games/any_questions/question_bank.txt', encoding='UTF-8') as f:
            questions = [line.strip() for line in f]
        random.shuffle(questions)
        return questions

    def load_question(self, *arg):
        if len(arg) > 0:
            question = ' '.join(arg)
            question = question.strip()
        else:
            question = self.default_questions.pop(0) if self.default_questions else None
        return question

    async def dm_all_players_question(self, question: str):
        async def ask_and_wait(player, question):
            try:
                user = await self.bot.fetch_user(player.id)
                dm = await user.create_dm()
                question += '\n如果同意/做過，答 Y ；反之答 N'
                await dm.send(question)

                def check(m):
                    return m.author.id == player.id and isinstance(m.channel, discord.DMChannel)

                while True:
                    msg = await self.bot.wait_for("message", check=check, timeout=120)
                    answer = msg.content.strip().upper()
                    if answer in ["Y", "N"]:
                        break
                    else:
                        await dm.send(f"你答咩「{answer}」啊？再答過啦！")
                player.response = answer
                await dm.send(f"OK 收到你！")
            except Exception:
                player.response = "Y"
                await self.ctx.send(f"{player.name} 炒車！我當佢答 Y 啦！")

        await asyncio.gather(*(ask_and_wait(p, question) for p in self.players))

    async def collect_player_guesses(self):
        async def ask_guess(player):
            try:
                user = await self.bot.fetch_user(player.id)
                dm = await user.create_dm()
                await dm.send(f"你覺得有幾多人答 Y? (答 0 至 {self.total_players})")

                def check(m):
                    return m.author.id == player.id and isinstance(m.channel, discord.DMChannel)

                while True:
                    msg = await self.bot.wait_for("message", check=check, timeout=120)
                    answer = msg.content.strip()
                    if answer.isdigit():
                        answer = int(answer)
                        if 0 <= answer <= self.total_players:
                            break
                    else:
                        await dm.send(f"你答咩「{answer}」啊？再答過啦！")
                player.guess = answer
                await dm.send(f"OK 收到你！")
            except Exception:
                player.guess = 1
                await self.ctx.send(f"{player.name} 炒車！我當佢求其答啦！")

        await asyncio.gather(*(ask_guess(p) for p in self.players))

    async def reveal_answers(self):
        answers = [p.response for p in self.players]
        yess = sum([1 if ans == 'Y' else 0 for ans in answers])
        random.shuffle(answers)

        await self.ctx.send("🧾 Here are the responses:")
        for idx, answer in enumerate(answers):
            await self.ctx.send(f"玩家 {idx + 1} 答 {answer} ！")
            await asyncio.sleep(0.5)

        await self.ctx.send(f"一同有 **{yess}** 個 Y！")

        guesses = "\n".join([f"{p.name} guessed: {p.guess}{" :white_check_mark:" if p.guess == yess else ""}"
                             for p in self.players])
        await self.ctx.send("Players guesses:\n" + guesses)

    def clean_answers(self):
        for player in self.players:
            player.clean_answers()

    async def start_round(self, *arg):
        question = self.load_question(*arg)
        await self.dm_all_players_question(question)
        await self.collect_player_guesses()
        await self.reveal_answers()
        await self.clean_answers()
