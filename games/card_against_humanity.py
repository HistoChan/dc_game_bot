import asyncio
from discord import DMChannel
import random
from .utils import NAMES_ID_MAP
from .Game import Player, Game

MAX_CARDS_IN_HAND = 14
WINNING_POINT = 5
QUESTION_CHOICES = 4


class CAH_Player(Player):
    def __init__(self, name):
        super().__init__(name)
        self.cards = []
        self.point = WINNING_POINT
        self.chosen_cards = []
        self.spare_card = None

    def add_cards(self, cards):
        self.cards += cards

    def clear_chosen_cards(self):
        self.chosen_cards = []

    def reset(self):
        self.cards = []
        self.point = WINNING_POINT
        self.chosen_cards = []

    def reset_to_normal_num_of_cards(self):
        self.chosen_cards = self.chosen_cards[:MAX_CARDS_IN_HAND - 1]

    async def choose_questions(self, bot, questions):
        dc_user = await bot.fetch_user(self.id)
        dm = await dc_user.create_dm()

        msg = ":thinking: 請選擇問題:\n"
        msg += '\n'.join([f'{i}. {q}' for i, q in enumerate(questions)])
        msg += f"\n請輸入對應數字（`1`-`{len(questions)}`）來選擇問題。"
        await dm.send(msg)

        def check(m):
            return m.author.id == self.id and isinstance(m.channel, DMChannel)

        chosen_question_idx = 0
        try:
            while True:
                msg = await bot.wait_for("message", check=check, timeout=300)
                answer = msg.content.strip()
                if answer.isdigit():
                    answer = int(answer)
                    if 1 <= answer <= len(questions):
                        break
                    else:
                        await dm.send(f":anger: 你答咩「{answer}」啊？再答過啦！")
                else:
                    await dm.send(f":anger: 你答咩「{answer}」啊？再答過啦！")
            chosen_question_idx = answer - 1
            await dm.send(f":wink: OK 收到你！")
        except Exception as e:
            print(e)
            await dm.send(":warning: 超時或錯誤，預設選擇第一題。")
        return questions[chosen_question_idx]

    async def answer_question(self, bot, question, questioner):
        dc_user = await bot.fetch_user(self.id)
        dm = await dc_user.create_dm()

        one_blank = "[答案 2]" not in question
        max_cards = 1 if one_blank else 2
        swap_used = False

        info_msg = f":thinking: {questioner}揀嘅問題係「{question}」\n"
        if one_blank:
            info_msg += ("此題有一個空格。請輸入對應數字（1-13）來回答問題。\n")
        else:
            info_msg += ("此題有兩個空格。請輸入兩個數字（1-14）代表兩張卡，逐個輸入。輸入 `undo` 以回上一步。\n")
        info_msg += (":black_joker: 你的卡牌：\n" + "\n".join([f'{i + 1}: {c}' for i, c in enumerate(self.cards)]))
        info_msg += "\n你可以揀第一張卡前用 `swap X` 交換其中一張卡，每一題限用一次。"
        await dm.send(info_msg)

        selected_indices = []

        async def change_card(idx):
            if len(self.cards) == 0:
                await dm.send(":warning: 無卡換啦，冇得 swap。")
                return False
            if idx < 0 or idx >= len(self.cards):
                await dm.send(":warning: swap 數字唔啱，再試過啦。")
                return False
            old_card = self.cards[idx]
            new_card = self.spare_card
            self.cards[idx] = new_card
            await dm.send(f":white_check_mark: 已用 swap：{old_card} :arrow_forward: {new_card}")
            print(f'{old_card} is wasted')
            self.spare_card = None
            info_msg = ":black_joker: 你的卡牌：\n" + \
                "\n".join([f'{i + 1}: {c} {':sparkles:' if i == idx else ''}' for i, c in enumerate(self.cards)])
            await dm.send(info_msg)
            return True

        def check(m):
            return m.author.id == self.id and isinstance(m.channel, DMChannel)

        while len(selected_indices) < max_cards:
            try:
                msg = await bot.wait_for("message", check=check, timeout=600)
                content = msg.content.strip().lower()

                # handle swap
                if content.startswith("swap "):
                    if len(selected_indices) > 0:
                        await dm.send(":warning: 你已經入咗張卡啦！ 你先 `undo` 再 `swap` 過啦！")
                        continue

                    if swap_used:
                        await dm.send(":warning: 你已經用過一次 swap 喇！")
                        continue
                    else:
                        parts = content.split()
                        if len(parts) == 2 and parts[1].isdigit():
                            idx = int(parts[1]) - 1
                            success = await change_card(idx)
                            if success:
                                swap_used = True
                            continue
                        else:
                            await dm.send(":warning: swap 指令格式係 `swap` 數字，再入過啦！")
                            continue

                if content == "undo":
                    if selected_indices:
                        selected_indices.pop()
                        await dm.send(f":white_check_mark: 已回上一步，請重新輸入。")
                    else:
                        await dm.send(":warning: 沒有可回復的步驟。")
                    continue

                if not content.isdigit():
                    await dm.send(f":anger: 你答咩「{content}」啊？再答過啦！")
                    continue
                choice = int(content) - 1
                if choice < 0 or choice >= len(self.cards):
                    await dm.send(f":anger: 你答咩「{content}」啊？再答過啦！")
                    continue

                if choice in selected_indices:
                    await dm.send(f":anger: 你答返同一張卡做乜啊？再答過啦！")
                    continue

                selected_indices.append(choice)
                await dm.send(f":white_check_mark: 你揀咗 [答案 {len(selected_indices)}] = {self.cards[choice]}。")
            except asyncio.TimeoutError:
                await dm.send(":alarm_clock: 時間到，我幫你求其答啦！")
                return list(range(0, max_cards))
            except Exception as e:
                await dm.send(f":warning: Unexpected error: {e}")

        # Lock-in
        selected_cards = [self.cards[i] for i in selected_indices]
        await dm.send(f":white_check_mark: 已提交卡牌：{' / '.join(selected_cards)}！")
        self.chosen_cards = selected_cards

        # delete cards
        selected_indices = sorted(selected_indices, reverse=True)
        for i in selected_indices:
            self.cards.pop(i)

    async def pick_least_favourite(self, bot, ctx, num_answers: int):
        await ctx.send(f"<@{self.id}>，請選出你最唔鍾意嘅答案，輸入數字 1 至 {num_answers}。")

        def check(m):
            return (m.author.id == self.id and m.channel == ctx.channel)

        selection = None
        while selection is None:
            try:
                while True:
                    msg = await bot.wait_for("message", check=check, timeout=300)
                    answer = msg.content.strip()
                    if answer.isdigit():
                        answer = int(answer)
                        if 1 <= answer <= num_answers:
                            break
                        else:
                            await ctx.send(f":anger: 你答咩「{answer}」啊？再答過啦！")
                    else:
                        await ctx.send(f":anger: 你答咩「{answer}」啊？再答過啦！")
                chosen_question_idx = answer - 1
                await ctx.send(f":wink: OK 收到你！你揀咗第 {answer} 個！")
                return chosen_question_idx
            except Exception:
                await ctx.send("超時或錯誤。")
                return None


class CAH_Game(Game):
    def __init__(self, bot, people_out_of_party):
        super().__init__(bot)
        self.players = [CAH_Player(m) for m in NAMES_ID_MAP.keys() if m not in people_out_of_party]
        self.total_players = len(self.players)
        self.default_questions = None

    def _load_cards(self, dlc=[]):
        basic_packs = ['basic', 'pop', 'sex']
        yellow_cards = []
        for pack_filename in basic_packs + dlc:
            with open(f'./games/cah_cards/{pack_filename}.txt', encoding='UTF-8') as f:
                lines = [line.strip() for line in f]
                lines = [line for line in lines if not line.startswith('#')]
                yellow_cards.extend(lines)

        with open(f'./games/cah_cards/questions.txt', encoding='UTF-8') as f:
            purple_cards = [line.strip() for line in f]
            purple_cards = [line for line in purple_cards if not line.startswith('#')]
        return yellow_cards, purple_cards

    async def set_up(self, dlc=[]):
        random.shuffle(self.players)
        await self.ctx.send(f':loudspeaker: 出題者次序如下： {' > '.join([f'<@{m.id}>' for m in self.players])}')
        yellow_cards, purple_cards = self._load_cards(dlc)
        random.shuffle(yellow_cards)
        random.shuffle(purple_cards)
        init_card_num = MAX_CARDS_IN_HAND - 1
        for idx, m in enumerate(self.players):
            m.add_cards(yellow_cards[idx * init_card_num: idx * init_card_num + init_card_num])
        self.yellow_cards = yellow_cards[self.total_players * init_card_num:]
        for m in self.players:
            m.spare_card = self.yellow_cards.pop(-1)
        self.purple_cards = purple_cards
        self.player_ptr = -1
        self.discard_yellow_cards = []
        self.discard_purple_cards = []

    async def send_score_board(self):
        board = ':loudspeaker: 目前大家個分如下：\n'
        board += "\n".join([f"<@{p.id}>: {p.point} 分" for p in self.players])
        await self.ctx.send(board)

    def _fill_question_person(self, options: list[Player], question: str):
        if '@person' in question:
            lucky_person = random.choice(options)
            question = question.replace('@person', lucky_person.name)
        question = question.replace('_', '**[答案 1]**', 1).replace('_', '**[答案 2]**', 1)
        return question

    def _fill_question_answers(self, answers: list[str], question: str):
        question = question.replace("[答案 1]", answers[0])
        if "[答案 2]" in question:
            question = question.replace("[答案 2]", answers[1])
        return question

    async def play_one_turn(self):
        try:
            self.player_ptr = (self.player_ptr + 1) % self.total_players
            questions = self.purple_cards[:QUESTION_CHOICES]
            self.purple_cards = self.purple_cards[QUESTION_CHOICES:]
            self.discard_purple_cards += questions

            questioner = self.players[self.player_ptr]
            questionees = [p for i, p in enumerate(self.players) if i != self.player_ptr]
            random.shuffle(questionees)
            await self.ctx.send(f':drum: 依家到 <@{questioner.id}> 揀問題！')
            filled_qs = [self._fill_question_person(questionees, q) for q in questions]
            selected_q = await questioner.choose_questions(self.bot, filled_qs)
            await self.ctx.send(f':thinking: <@{questioner.id}> 揀咗問題「{selected_q}」啦，大家開始揀答案啦！')

            for p in questionees:
                extra_yellow_card = self.yellow_cards.pop(0)
                p.add_cards([extra_yellow_card])
            if "[答案 2]" in selected_q:
                for p in questionees:
                    extra_yellow_card = self.yellow_cards.pop(0)
                    p.add_cards([extra_yellow_card])
            for m in self.players:
                if m.spare_card is None:
                    m.spare_card = self.yellow_cards.pop(-1)
            await asyncio.gather(*(p.answer_question(self.bot, selected_q, questioner.name) for p in questionees))

            answers = [self._fill_question_answers(p.chosen_cards, selected_q) for p in questionees]
            read_skill = random.choice(['大聲', '用特別嘅朗誦技巧', '笑住咁', '無乜情緒咁', '用心靈感應嘅方式'])
            await self.ctx.send(f":loud_sound:請 <@{questioner.id}> {read_skill}朗讀:")
            for idx, answer in enumerate(answers):
                await self.ctx.send(f"玩家 {idx + 1} ： 「{answer}」 ！")
                await asyncio.sleep(2)

            pick = await questioner.pick_least_favourite(self.bot, self.ctx, self.total_players - 1)
            if pick is None:
                await self.ctx.send(f":yellow_square: <@{questioner.id}> 收皮啦，一個答案都揀唔到㗎！")
            await self.ctx.send(f":yellow_square: <@{questioner.id}> 叫 <@{questionees[pick].id}> 收皮啦，咩答案黎㗎！")
            questionees[pick].point -= 1
            for p in questionees:
                self.discard_yellow_cards += p.chosen_cards
                p.clear_chosen_cards()
            await self.send_score_board()
        except Exception as e:
            print(f'Error when running a round: {e}')
            await self.ctx.send(f":broken_heart: 我個野壞咗啊！呢round打和 super！")
            for p in self.players:
                p.reset_to_normal_num_of_cards()
            await self.send_score_board()

    async def end_game_wrap_up(self):
        loser = [m for m in self.players if m.point == 0][0]
        await self.ctx.send(f":checkered_flag: 遊戲結束！ <@{loser.id}> 黃牌出局！")
        await self.send_score_board()
        for player in self.players:
            player.reset()
        self.end_game()

    async def card_against_humanity(self, *arg):
        while self.is_running():
            try:
                await self.set_up(dlc=list(arg[0]))

                game_ended = False
                while not game_ended:
                    if not self.running:
                        break
                    await self.play_one_turn()
                    game_ended = any(m.point == 0 for m in self.players)
                    if game_ended:
                        await self.ctx.send(f':bangbang: 噢！有人零分啦喎！')
                    if not self.running:
                        break
                await self.end_game_wrap_up()
            except Exception as e:
                print(e)
