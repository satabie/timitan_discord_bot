import discord
from discord.ext import commands
import os
import random
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', case_insensitive=True, intents=intents)

# 起動時に動作する処理
@bot.event
async def on_ready():
    print('ログインしました')

# メッセージ受信時に動作する処理
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    print(message.content)
    if 'ちみ' in message.content:
        image_folder = 'images'
        # image_folder内のファイル名をリストで取得
        image_files = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]
        if image_files:
            image_file = random.choice(image_files)
            image_path = os.path.join(image_folder, image_file)
            await message.channel.send(file=discord.File(image_path))
    elif 'shosei' or "Shosei" or "書生" in message.content:
        await message.channel.send("shoseiは寝ています")



# ボットを実行
bot.run(TOKEN)
