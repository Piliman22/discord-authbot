from dotenv import load_dotenv
import os
import discord
import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))  # サーバーIDを環境変数から取得
VERIFICATION_CHANNEL_ID = int(os.getenv('VERIFICATION_CHANNEL_ID'))  # 認証専用チャンネルID
ROLE_NAME = "メンバー"

intents = discord.Intents.default()
intents.members = True  # メンバー関連イベントの取得
intents.guilds = True
intents.message_content = True  # メッセージの内容を取得可能にする
client = discord.Client(intents=intents)

# 認証コードを保存する辞書
verification_codes = {}

@client.event
async def on_member_join(member):
    """ ユーザーがサーバーに参加したときの処理 """
    code = str(random.randint(100000, 999999))  # 6桁のランダムコード生成
    verification_codes[member.id] = code

    try:
        await member.send(f"ようこそ！認証コード: `{code}` をサーバー内の指定されたチャンネルで送信してください。")
    except discord.Forbidden:
        print(f"{member.name} にDMを送信できませんでした。")

@client.event
async def on_message(message):
    if message.author == client.user or message.guild is None:
        return
    
    if message.channel.id != VERIFICATION_CHANNEL_ID:
        return

    member = message.author
    code = verification_codes.get(member.id)

    print(f"DEBUG: 保存されたコード: {code}, ユーザー入力: {message.content.strip()}")  # デバッグ用出力

    if code and message.content.strip().isdigit() and int(message.content.strip()) == int(code):
        guild = discord.utils.get(client.guilds, id=GUILD_ID)
        role = discord.utils.get(guild.roles, name=ROLE_NAME)
        if role:
            await member.add_roles(role)
            await message.channel.send(f"{member.mention} 認証完了しました！")
            del verification_codes[member.id]
        else:
            await message.channel.send("エラー: 認証ロールが見つかりませんでした。")
    else:
        await message.channel.send("認証コードが違います。もう一度試してください。")

client.run(TOKEN)
