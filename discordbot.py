import discord
from discord.ext import commands
import os
import random
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# 画像フォルダから画像ファイルを読み込む
image_folder = 'images'
image_files = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='ちみ')
async def send_random_stamp(ctx):
    # ランダムに画像を選択
    selected_stamp = random.choice(image_files)

    # 画像を送信
    with open(os.path.join(image_folder, selected_stamp), 'rb') as file:
        picture = discord.File(file)
        await ctx.send(file=picture)

# ボットを実行
bot.run(TOKEN)
