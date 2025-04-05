from dotenv import load_dotenv
import os
import discord
import random
import aiohttp
import datetime
from discord import app_commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
VERIFICATION_CHANNEL_ID = int(os.getenv('VERIFICATION_CHANNEL_ID'))
ROLE_NAME = "メンバー"
WEBHOOK_URL = str(os.getenv('WEBHOOK_URL'))

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True
client = discord.Client(intents=intents)

tree = discord.app_commands.CommandTree(client)

verification_codes = {}

@client.event
async def on_ready():
    """Botが起動したときの処理"""
    print(f'Logged in as {client.user}')
    try:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
        print("スラッシュコマンドを同期しました。")
    except Exception as e:
        print(f"スラッシュコマンドの同期に失敗: {e}")

@client.event
async def on_member_join(member):
    """ ユーザーがサーバーに参加したときの処理 """
    code = str(random.randint(100000, 999999))
    verification_codes[member.id] = code

    try:
        await member.send(f"ようこそ！認証コード: `{code}` をauthチャンネルで送信してください。")
        await member.send(f"Welcome! Please send the verification code: `{code}` in the auth channel.")
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

    print(f"DEBUG: 保存されたコード: {code}, ユーザー入力: {message.content.strip()}")

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

@tree.command(name="notification", description="ウェブアプリに通知を送る", guild=discord.Object(id=GUILD_ID))
async def notification(interaction: discord.Interaction, message: str):
    """ /notification <メッセージ> を実行したときの処理 """
    allowed_roles = ["管理者", "モデレーター"]  # 実行を許可するロール名
    user_roles = [role.name for role in interaction.user.roles]

    if not any(role in user_roles for role in allowed_roles):
        await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "content": message,
        "author": interaction.user.name,
        "timestamp": now
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(WEBHOOK_URL, json=data) as response:
            print(f"DEBUG: Webhook response status = {response.status}")
            response_text = await response.text()
            print(f"DEBUG: Response text = {response_text}")

            if response.status == 200:
                await interaction.followup.send("通知を送信しました！", ephemeral=True)
            else:
                await interaction.followup.send(f"通知の送信に失敗しました… (ステータスコード: {response.status})", ephemeral=True)

client.run(TOKEN)