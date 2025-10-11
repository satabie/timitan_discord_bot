import discord
from discord.ext import commands
from discord import app_commands
import os
import random
from dotenv import load_dotenv

from keep_alive import keep_alive
import asyncio
import datetime
import pytz

# .envファイルから環境変数を読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
REPLY_KEYWORDS = os.getenv("REPLY_KEYWORDS", "").split(",")

intents = discord.Intents.default()
intents.message_content = True
command_prefix = "/"
TIMEZONE = "Asia/Tokyo"
bot = commands.Bot(command_prefix=command_prefix, case_insensitive=True, intents=intents)

# 起動時に動作する処理


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"ログインしました - {len(synced)}個のスラッシュコマンドを同期しました")
    except Exception as e:
        print(f"コマンドの同期に失敗しました: {e}")


# メッセージ受信時に動作する処理
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    print(message.content)
    for keyword in REPLY_KEYWORDS:
        if keyword in message.content:
            gif_folder = "gif"
            # gif_folder内のファイル名をリストで取得
            gif_files = [f for f in os.listdir(gif_folder) if os.path.isfile(os.path.join(gif_folder, f))]
            if gif_files:
                gif_file = random.choice(gif_files)
                gif_path = os.path.join(gif_folder, gif_file)
                await message.channel.send(file=discord.File(gif_path))
            break


# 機能を説明するヘルプコマンド
@bot.tree.command(name="timi_help", description="ちみたんのコマンド一覧を表示します")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="ヘルプ", description="ちみたんのコマンド一覧だよ", color=0x00BFFF)
    embed.add_field(name="/timi_help", value="このメッセージを表示します", inline=False)
    embed.add_field(name="/del_msg N", value="直近N件のメッセージを削除します(例：/del_msg 5)", inline=False)
    embed.add_field(
        name="/alarm HH:MM", value="指定した時刻(JST)にメンションを送信します(例：/alarm 17:00)", inline=False
    )
    embed.add_field(name="/ping", value="pingを送信します", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="alarm", description="指定した時刻(JST)にメンションを送信します")
@app_commands.describe(time="時刻を指定してください (例: 17:00)")
async def set_alarm(interaction: discord.Interaction, time: str):
    try:
        # タイムゾーンの設定
        server_timezone = pytz.timezone(TIMEZONE)
        now = datetime.datetime.now(server_timezone)
        today = datetime.date.today()

        # 時刻をバース
        alarm_time = datetime.datetime.strptime(time, "%H:%M")

        # タイムゾーンを設定
        alarm_time = server_timezone.localize(alarm_time.replace(year=today.year, month=today.month, day=today.day))

        # 指定した時刻までの時間差を計算
        time_delta = alarm_time - now

        # 翌日を指定した場合の処理
        if time_delta.total_seconds() < 0:
            tomorrow = today + datetime.timedelta(days=1)
            alarm_time = alarm_time.replace(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
            time_delta = alarm_time - now

        await interaction.response.send_message(f"アラームを{time}(JST)にセットしました")

        # 指定した時刻まで待機
        while now < alarm_time:
            await asyncio.sleep(60)  # 　1分ごとに確認
            now = datetime.datetime.now(server_timezone)

        # タイマーをセットした時刻にメッセージを送信
        await interaction.channel.send(f"{interaction.user.mention} {time}(JST)になりました")
    except ValueError:
        await interaction.response.send_message("正しい時刻の形式で指定してください(例：/alarm 17:00) ")


@bot.tree.command(name="del_msg", description="直近N件のメッセージを削除します")
@app_commands.describe(num="削除するメッセージの件数")
async def del_msg(interaction: discord.Interaction, num: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=num)
    await interaction.followup.send(f"{num}件のメッセージを削除しました", ephemeral=True)


@bot.tree.command(name="ping", description="pingを送信します")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong")


# ボットを実行
keep_alive()
bot.run(TOKEN)
