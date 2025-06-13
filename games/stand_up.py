import asyncio
import copy
import random
from .Game import Game
from .utils import NAMES_ID_MAP

# Set random messages parameters
TOTAL_DURATION = 2 * 60 * 60
MIN_NUM_MESSAGES = 8
MIN_INTERVAL = 5 * 60
RESPONSE_TIME = 130
NAMES = list(NAMES_ID_MAP.keys())


def generate_lucky_time_and_people():  # is_demo=False
    # total_duration = 450 if is_demo else TOTAL_DURATION
    # min_msg = 2 if is_demo else MIN_NUM_MESSAGES
    # min_interval = 5 if is_demo else MIN_INTERVAL
    total_duration = TOTAL_DURATION
    min_msg = MIN_NUM_MESSAGES
    min_interval = MIN_INTERVAL

    intervals = [(0, total_duration)]
    timestamps = []
    while intervals:
        (start, end) = intervals.pop()
        offset = random.randint(start + min_interval, end - min_interval)
        timestamps.append(offset)
        if offset - start >= min_interval * 2 + 1:
            intervals.append((start, offset))
        if end - offset >= min_interval * 2 + 1:
            intervals.append((offset, end))

    actual_msg_num = random.randint(min_msg, min_msg + 2)
    random.shuffle(timestamps)
    actual_offsets = sorted(timestamps[:actual_msg_num])

    lucky_people = copy.deepcopy(NAMES)
    random.shuffle(lucky_people)
    lucky_people = lucky_people[:min_msg - 1]

    more_lucky_people = copy.deepcopy(NAMES)
    random.shuffle(more_lucky_people)
    more_lucky_people = more_lucky_people[:actual_msg_num - min_msg + 1]

    lucky_people.extend(more_lucky_people)
    random.shuffle(lucky_people)
    return actual_offsets, lucky_people


class Standup_Game(Game):
    def __init__(self, bot):
        super().__init__(bot)

    async def send_random_messages(self, is_demo=False):
        while self.is_running():
            prev = 0
            try:
                offsets, peoples = generate_lucky_time_and_people()
                for offset, person in zip(offsets, peoples):
                    wait_time = max(0, offset - prev)
                    await asyncio.sleep(wait_time)
                    if not self.running:
                        break
                    if is_demo:
                        await self.ctx.send(f":warning: @everyone 黑圖時間： 一齊些牙大家嘅黑圖上黎啦！")
                    else:
                        await self.ctx.send(f":warning: @everyone 黑圖時間： 一齊些牙 {person} 嘅黑圖上黎啦！")
                    if not self.running:
                        break
                    await asyncio.sleep(RESPONSE_TIME)
                    if not self.running:
                        break
                    if is_demo:
                        await self.ctx.send(f"好啦夠啦，唔好再send大家嘅黑圖上黎啦！")
                    else:
                        await self.ctx.send(f"好啦夠啦，唔好再send {person} 嘅黑圖上黎啦！")
                    if not self.running:
                        break
                    prev = offset + RESPONSE_TIME
            except Exception as e:
                print(e)
            await self.ctx.send("黑圖些牙大賽完成！多謝大家參與！")
            self.end_game()
