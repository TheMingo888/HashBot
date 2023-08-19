#!/usr/bin/python3

from discord.ext import commands
import datetime
import discord
import Token
import re
import requests

"""
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
"""

""" 
class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message: discord.Message):
        if message.author == client.user:
            return

        print('Message from {0.author}: {0.content}'.format(message))
        assert isinstance(message.channel, discord.abc.Messageable)
        await message.channel.send("Hi")

client = MyClient()
client.run(Token.token) """

bot = commands.Bot("//", status=discord.Status.online, intents=discord.Intents.all())
bad_double_quotes = re.compile(r"[“”]")
bad_single_quotes = re.compile(r"[‘’]")
db = None
last_db_update = datetime.datetime(1970, 1, 1)


@bot.event
async def on_ready():
    print("Logged on as {0}!".format(bot.user))
    #await bot.get_channel(357409958922551296).send("Logged on as {0}!".format(bot.user))

@bot.event
async def on_message(message: discord.Message):
    message.content = bad_double_quotes.sub('"', message.content)
    message.content = bad_single_quotes.sub('"', message.content)
    await bot.process_commands(message)

"""
@bot.event
async def on_message_delete(message: discord.Message):
    if (message.author == bot.user):
        await message.channel.send(message.content)
"""

def get_db():
    global db, last_db_update
    if datetime.datetime.now() - last_db_update > datetime.timedelta(minutes=30):
        res = requests.get("https://yum.selb.io/yumdb/players", auth=(Token.yum_db_user, Token.yum_db_pw))
        db = res.json()
    return db

@bot.command(name="hash")
async def hash(ctx: commands.Context, leaderboard: str, lastname: str = None):
    """Find a hash from a leaderboard"""
    print("Finding hash from leaderboard %s %s" % (leaderboard, lastname))
    if lastname:
        full_name = ("%s %s" % (leaderboard, lastname)).title()
        for account in get_db():
            if account["leaderboard_name"] == full_name:
                await ctx.send("`" + account["ehash"] + "`")
                return
    else:
        result = re.search(r"(\?action=leaderboard_detail&id=)?(\d+)", leaderboard)
        if result:
            leaderboard = int(result.group(2))
        else:
            await ctx.send("Invalid leaderboard")
            return
        for account in get_db():
            if account["leaderboard_id"] == leaderboard:
                await ctx.send("`" + account["ehash"] + "`")
                return
    await ctx.send("Account not found")

@bot.command(name="leaderboard")
async def leaderboard(ctx: commands.Context, hash: str):
    """Find a leaderboard from a hash"""
    print("Finding leaderboard from hash %s" % hash)
    for account in get_db():
        if account["ehash"] == hash:
            id = account["leaderboard_id"]
            name = account["leaderboard_name"]
            padding = " " * int((8 - len(str(id))) * 2)
            url = r"https://onehouronelife.com/fitnessServer/server.php?action=leaderboard_detail&id="
            await ctx.send("[%s](%s%s)%s%s" % (id, url, id, padding, name))
            return
    await ctx.send("Account not found")

@hash.error
@leaderboard.error
async def errors(ctx, error):
    if isinstance(error, commands.NotOwner):
        await ctx.send("ERROR: You are not mingo888")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("ERROR: Mising argument")
    elif isinstance(error, commands.UserNotFound):
        await ctx.send("ERROR: User not found")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send("ERROR: Channel not found")
    else:
        await ctx.send("ERROR: Unknown")
        raise error

bot.run(Token.token)
