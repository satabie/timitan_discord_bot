import keyword
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
import logging
import json
from typing import Optional, List
from pathlib import Path

# ロギングの設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# キーワード管理クラス
class KeywordManager:
    """キーワードの永続化と管理を行うクラス"""

    KEYWORDS_FILE: str = "keywords.json"

    @classmethod
    def load_keywords(cls) -> List[str]:
        """JSONファイルからキーワードを読み込む"""
        keywords_path = Path(cls.KEYWORDS_FILE)
        if keywords_path.exists():
            try:
                with open(keywords_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("keywords", [])
            except Exception as e:
                logger.error(f"キーワードの読み込みに失敗しました: {e}")
                return []
        return []

    @classmethod
    def save_keywords(cls, keywords: List[str]) -> bool:
        """キーワードをJSONファイルに保存する"""
        try:
            with open(cls.KEYWORDS_FILE, "w", encoding="utf-8") as f:
                json.dump({"keywords": keywords}, f, ensure_ascii=False, indent=2)
            logger.info(f"キーワードを保存しました: {keywords}")
            return True
        except Exception as e:
            logger.error(f"キーワードの保存に失敗しました: {e}")
            return False

    @classmethod
    def add_keyword(cls, keyword: str) -> bool:
        """キーワードを追加する"""
        keywords = cls.load_keywords()
        if keyword in keywords:
            return False
        keywords.append(keyword)
        return cls.save_keywords(keywords)

    @classmethod
    def remove_keyword(cls, keyword: str) -> bool:
        """キーワードを削除する"""
        keywords = cls.load_keywords()
        if keyword not in keywords:
            return False
        keywords.remove(keyword)
        return cls.save_keywords(keywords)

    @classmethod
    def get_keywords(cls) -> List[str]:
        """現在のキーワードリストを取得する"""
        return cls.load_keywords()


# 設定クラス
class Config:
    """ボットの設定を管理するクラス"""

    load_dotenv()

    TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    COMMAND_PREFIX: str = "/"
    TIMEZONE: str = "Asia/Tokyo"
    GIF_FOLDER: str = "gif"
    ALARM_CHECK_INTERVAL: int = 60  # 秒

    @classmethod
    def validate(cls) -> None:
        """設定の検証"""
        if not cls.TOKEN:
            raise ValueError("DISCORD_BOT_TOKEN が設定されていません")
        if not Path(cls.GIF_FOLDER).exists():
            logger.warning(f"GIFフォルダ {cls.GIF_FOLDER} が見つかりません")


Config.validate()

# Botのセットアップ
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=Config.COMMAND_PREFIX, case_insensitive=True, intents=intents)

# ヘルパー関数


def get_random_gif() -> Optional[Path]:
    """GIFフォルダからランダムにGIFを選択する"""
    gif_folder = Path(Config.GIF_FOLDER)
    if not gif_folder.exists():
        logger.error(f"GIFフォルダ {Config.GIF_FOLDER} が存在しません")
        return None

    gif_files = [f for f in gif_folder.iterdir() if f.is_file()]
    if not gif_files:
        logger.warning(f"GIFフォルダ {Config.GIF_FOLDER} にファイルがありません")
        return None

    return random.choice(gif_files)


async def send_random_gif(channel: discord.TextChannel) -> None:
    """指定されたチャンネルにランダムなGIFを送信する"""
    try:
        gif_path = get_random_gif()
        if gif_path:
            await channel.send(file=discord.File(gif_path))
            logger.info(f"GIFを送信しました: {gif_path.name}")
    except Exception as e:
        logger.error(f"GIFの送信に失敗しました: {e}")


def check_keyword_in_message(message_content: str, keywords: List[str]) -> Optional[str]:
    """メッセージ内にキーワードが含まれているかチェックする"""
    for keyword in keywords:
        if keyword and keyword in message_content:
            return keyword
    return None


def calculate_alarm_time(time_str: str, timezone_str: str) -> datetime.datetime:
    """指定された時刻文字列からアラーム時刻を計算する"""
    server_timezone = pytz.timezone(timezone_str)
    now = datetime.datetime.now(server_timezone)
    today = datetime.date.today()

    # 時刻をパース
    alarm_time = datetime.datetime.strptime(time_str, "%H:%M")

    # タイムゾーンを設定
    alarm_time = server_timezone.localize(alarm_time.replace(year=today.year, month=today.month, day=today.day))

    # 指定した時刻が過去の場合は翌日に設定
    if alarm_time <= now:
        tomorrow = today + datetime.timedelta(days=1)
        alarm_time = alarm_time.replace(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)

    return alarm_time


# 起動時に動作する処理


@bot.event
async def on_ready() -> None:
    """ボット起動時の処理"""
    try:
        synced = await bot.tree.sync()
        logger.info(f"ログインしました - {len(synced)}個のスラッシュコマンドを同期しました")
    except Exception as e:
        logger.error(f"コマンドの同期に失敗しました: {e}")


# メッセージ受信時に動作する処理


@bot.event
async def on_message(message: discord.Message) -> None:
    """メッセージ受信時の処理"""
    if message.author.bot:
        return

    logger.info(f"メッセージ受信: {message.content}")

    # キーワードに対する返信（GIF送信）
    keywords = KeywordManager.get_keywords()
    keyword = check_keyword_in_message(message.content, keywords)
    if keyword:
        await send_random_gif(message.channel)
        logger.info(f"キーワード '{keyword}' に反応しました")


# コマンド定義


@bot.tree.command(name="timi_help", description="ちみたんのコマンド一覧を表示します")
async def help(interaction: discord.Interaction) -> None:
    """ヘルプコマンド"""
    embed = discord.Embed(title="ヘルプ", description="ちみたんのコマンド一覧だよ", color=0x00BFFF)
    embed.add_field(name="/timi_help", value="このメッセージを表示します", inline=False)
    embed.add_field(name="/del_msg N", value="直近N件のメッセージを削除します(例：/del_msg 5)", inline=False)
    embed.add_field(
        name="/alarm HH:MM", value="指定した時刻(JST)にメンションを送信します(例：/alarm 17:00)", inline=False
    )
    embed.add_field(name="/add_keyword キーワード", value="反応するキーワードを追加します", inline=False)
    embed.add_field(name="/remove_keyword キーワード", value="反応するキーワードを削除します", inline=False)
    embed.add_field(name="/list_keywords", value="登録されているキーワードの一覧を表示します", inline=False)
    await interaction.response.send_message(embed=embed)
    logger.info("ヘルプコマンドが実行されました")


@bot.tree.command(name="alarm", description="指定した時刻(JST)にメンションを送信します")
@app_commands.describe(time="時刻を指定してください (例: 17:00)")
async def set_alarm(interaction: discord.Interaction, time: str) -> None:
    """アラームコマンド"""
    try:
        # アラーム時刻を計算
        alarm_time = calculate_alarm_time(time, Config.TIMEZONE)
        server_timezone = pytz.timezone(Config.TIMEZONE)

        await interaction.response.send_message(f"アラームを{time}(JST)にセットしました")
        logger.info(f"アラームを{time}(JST)にセットしました（ユーザー: {interaction.user.name}）")

        # 指定した時刻まで待機
        while datetime.datetime.now(server_timezone) < alarm_time:
            await asyncio.sleep(Config.ALARM_CHECK_INTERVAL)

        # タイマーをセットした時刻にメッセージを送信
        await interaction.channel.send(f"{interaction.user.mention} {time}(JST)になりました")
        logger.info(f"アラーム通知を送信しました: {time}(JST)")

    except ValueError as e:
        error_message = "正しい時刻の形式で指定してください(例：/alarm 17:00)"
        await interaction.response.send_message(error_message)
        logger.warning(f"アラームコマンドのエラー: {e}")
    except Exception as e:
        logger.error(f"アラームコマンドで予期しないエラー: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("アラームの設定中にエラーが発生しました")


@bot.tree.command(name="del_msg", description="直近N件のメッセージを削除します")
@app_commands.describe(num="削除するメッセージの件数")
async def del_msg(interaction: discord.Interaction, num: int) -> None:
    """メッセージ削除コマンド"""
    try:
        await interaction.response.defer(ephemeral=True)
        deleted_messages = await interaction.channel.purge(limit=num)
        await interaction.followup.send(f"{len(deleted_messages)}件のメッセージを削除しました", ephemeral=True)
        logger.info(f"{len(deleted_messages)}件のメッセージを削除しました（ユーザー: {interaction.user.name}）")
    except discord.Forbidden:
        await interaction.followup.send("メッセージを削除する権限がありません", ephemeral=True)
        logger.warning(f"メッセージ削除の権限エラー（ユーザー: {interaction.user.name}）")
    except Exception as e:
        logger.error(f"メッセージ削除中にエラー: {e}")
        await interaction.followup.send("メッセージの削除中にエラーが発生しました", ephemeral=True)


@bot.tree.command(name="add_keyword", description="反応するキーワードを追加します")
@app_commands.describe(keyword="追加するキーワード")
async def add_keyword(interaction: discord.Interaction, keyword: str) -> None:
    """キーワード追加コマンド"""
    try:
        if KeywordManager.add_keyword(keyword):
            await interaction.response.send_message(f"キーワード「{keyword}」を追加しました", ephemeral=True)
            logger.info(f"キーワードを追加しました: {keyword}（ユーザー: {interaction.user.name}）")
        else:
            await interaction.response.send_message(f"キーワード「{keyword}」は既に登録されています", ephemeral=True)
            logger.info(f"重複したキーワードの追加を試みました: {keyword}（ユーザー: {interaction.user.name}）")
    except Exception as e:
        logger.error(f"キーワード追加中にエラー: {e}")
        await interaction.response.send_message("キーワードの追加中にエラーが発生しました", ephemeral=True)


@bot.tree.command(name="remove_keyword", description="反応するキーワードを削除します")
@app_commands.describe(keyword="削除するキーワード")
async def remove_keyword(interaction: discord.Interaction, keyword: str) -> None:
    """キーワード削除コマンド"""
    try:
        if KeywordManager.remove_keyword(keyword):
            await interaction.response.send_message(f"キーワード「{keyword}」を削除しました", ephemeral=True)
            logger.info(f"キーワードを削除しました: {keyword}（ユーザー: {interaction.user.name}）")
        else:
            await interaction.response.send_message(f"キーワード「{keyword}」は登録されていません", ephemeral=True)
            logger.info(f"存在しないキーワードの削除を試みました: {keyword}（ユーザー: {interaction.user.name}）")
    except Exception as e:
        logger.error(f"キーワード削除中にエラー: {e}")
        await interaction.response.send_message("キーワードの削除中にエラーが発生しました", ephemeral=True)


@bot.tree.command(name="list_keywords", description="登録されているキーワードの一覧を表示します")
async def list_keywords(interaction: discord.Interaction) -> None:
    """キーワード一覧表示コマンド"""
    try:
        keywords = KeywordManager.get_keywords()
        if keywords:
            keyword_list = "、".join(keywords)
            embed = discord.Embed(
                title="登録キーワード一覧", description=f"現在のキーワード: {keyword_list}", color=0x00BFFF
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("現在、キーワードは登録されていません", ephemeral=True)
        logger.info(f"キーワード一覧を表示しました（ユーザー: {interaction.user.name}）")
    except Exception as e:
        logger.error(f"キーワード一覧表示中にエラー: {e}")
        await interaction.response.send_message("キーワード一覧の取得中にエラーが発生しました", ephemeral=True)


# ボットを実行
if __name__ == "__main__":
    try:
        keep_alive()
        logger.info("ボットを起動します...")
        bot.run(Config.TOKEN)
    except Exception as e:
        logger.error(f"ボットの起動に失敗しました: {e}")
