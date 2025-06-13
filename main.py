import asyncio
from dotenv import load_dotenv
import discord
import os
from discord.ext import commands
from games.ask_any import Askany_Game
from games.stand_up import Standup_Game
from games.card_against_humanity import CAH_Game
from games.utils import people_out_of_party


load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


class TaskMaster():
    def __init__(self):
        self.games = {
            "askany": Askany_Game(bot, people_out_of_party),
            "blackpic": Standup_Game(bot),
            "cah": CAH_Game(bot, people_out_of_party)
        }
        self.game_names = {
            "askany": "真心話不冒險", "blackpic": "黑圖撞機", "cah": "黃牌"
        }
        self.people_out_of_party = people_out_of_party


tm = TaskMaster()


@bot.event
async def on_ready():
    print(f'已登入為 {bot.user}')


@bot.command(name="start")
async def start_game(ctx, *arg):
    if len(arg) == 0:
        await ctx.send("Please provide the game.")
        return
    game = arg[0].lower()
    if game not in tm.games:
        await ctx.send(":x: Unknown game. Please enter the correct name.")
        return

    if tm.games[game].is_running():
        await ctx.send(f":x: {game} is already running.")
        return

    await ctx.send(f":video_game: 準備開始遊戲 {tm.game_names[game]}！")
    await asyncio.sleep(1.5)

    game_obj = tm.games[game]
    game_obj.start_game(ctx)
    if game == "blackpic":
        game_obj.task = asyncio.create_task(game_obj.send_random_messages('demo' in arg))
    elif game == "cah":
        game_obj.task = asyncio.create_task(game_obj.card_against_humanity(arg[1:]))


@bot.command(name="end")
async def end_game(ctx, *arg):
    if len(arg) == 0:
        await ctx.send("Please specify which game to end.")
        return

    game = arg[0].lower()
    if game not in tm.games:
        await ctx.send(":x: Unknown game.")
        return

    if not tm.games[game].is_running():
        await ctx.send(f":x: {tm.game_names[game]} is not running.")
        return

    tm.games[game].end_game()
    await ctx.send(f":crying_cat_face: {tm.game_names[game]} has been ended.")


@bot.command(name="ask")
async def ask_question_in_askany(ctx, *arg):
    if tm.games['askany'].is_running():
        tm.games['askany'].task = asyncio.create_task(tm.games['askany'].start_round(*arg))
    else:
        await ctx.send("真心話不冒險 未開始喎！")
    return

bot.run(TOKEN)
