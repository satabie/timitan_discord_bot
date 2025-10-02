import discord
from discord.ext import commands
import os
import random
from dotenv import load_dotenv
from keep_alive import keep_alive
import asyncio
import datetime
import pytz

# .envファイルから環境変数を読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
command_prefix = '/'
TIMEZONE = 'Asia/Tokyo'
bot = commands.Bot(command_prefix=command_prefix, case_insensitive=True, intents=intents)

# 起動時に動作する処理


@bot.event
async def on_ready():
    print('ログインしました')


# メッセージ受信時に動作する処理
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # 受け取ったメッセージがコマンドである場合の処理
    if message.content.startswith(command_prefix):
        command_text = message.content[1:]
        await bot.process_commands(message)

    print(message.content)
    if 'ちみ' in message.content:
        image_folder = 'images'
        # image_folder内のファイル名をリストで取得
        image_files = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]
        if image_files:
            image_file = random.choice(image_files)
            image_path = os.path.join(image_folder, image_file)
            await message.channel.send(file=discord.File(image_path))
    else:
        for keyword in ['shosei', 'Shosei', 'しょせい', '書生','坂田','さかた']:
            if keyword in message.content:
                await message.channel.send(f"{keyword}は寝ています")
                break


# 機能を説明するヘルプコマンド
@bot.command(name='timi_help')
async def help(ctx):
    embed = discord.Embed(title='ヘルプ', description='ちみたんのコマンド一覧だよ', color=0x00bfff)
    embed.add_field(name='/timi_help', value='このメッセージを表示します', inline=False)
    embed.add_field(name='/del_msg N', value='直近N件のメッセージを削除します(例：/del_msg 5)', inline=False)
    embed.add_field(name='/alarm HH:MM', value='指定した時刻(JST)にメンションを送信します(例：/alarm 17:00)', inline=False)
    embed.add_field(name='/ping', value='pingを送信します', inline=False)
    await ctx.send(embed=embed)


@bot.command(name='alarm')
async def set_alarm(ctx, time: str):
    try:
        # タイムゾーンの設定
        server_timezone = pytz.timezone(TIMEZONE)
        now = datetime.datetime.now(server_timezone)
        today = datetime.date.today()

        # 時刻をバース
        alarm_time = datetime.datetime.strptime(time, '%H:%M')

        # タイムゾーンを設定
        alarm_time = server_timezone.localize(alarm_time.replace(year=today.year, month=today.month, day=today.day))

        # 指定した時刻までの時間差を計算
        time_delta = alarm_time - now

        # 翌日を指定した場合の処理
        if time_delta.total_seconds() < 0:
            tomorrow = today + datetime.timedelta(days=1)
            alarm_time = alarm_time.replace(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
            time_delta = alarm_time - now

        await ctx.send(f"アラームを{time}(JST)にセットしました")
        
        # 指定した時刻まで待機
        while now < alarm_time:
            await asyncio.sleep(60) # 　1分ごとに確認
            now = datetime.datetime.now(server_timezone)

        # タイマーをセットした時刻にメッセージを送信
        await ctx.send(f'{ctx.author.mention} {time}(JST)になりました')
    except ValueError:
        await ctx.send("正しい時刻の形式で指定してください(例：/alarm 17:00) ")


@set_alarm.error
async def set_alarm_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("正しい時刻の形式で指定してください(例：/alarm 17:00) ")


@bot.command(name='del_msg')
async def del_msg(ctx, num: int):
    await ctx.channel.purge(limit=num + 1)
    await ctx.send(f'{num}件のメッセージを削除しました', delete_after=10)


@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('pong')

# ボットを実行
keep_alive()
bot.run(TOKEN)
