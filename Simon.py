logo = """
 ____ ____ ____ ____ ____ _________ ____ ____ ____ ____
||S |||i |||m |||o |||n |||       |||S |||a |||y |||s ||
||__|||__|||__|||__|||__|||_______|||__|||__|||__|||__||
|/__\|/__\|/__\|/__\|/__\|/_______\|/__\|/__\|/__\|/__\|"""

instructions = """Commands:
• !simon help - repeat this message
• !simon score all - check all scores
• !simon score me - check your score
• !simon score <player> - check another player's score"""

import os
import sys
import time
import random
import asyncio
import platform

try:
    import discord
    from discord.utils import get
    from discord.ext import commands
except ImportError:
    print("Error: no Discord library found!")
    sys.exit(1)

wait = 60
word = ""
taken = []
votes = []
trick = False
special = None
channel = None

bot = discord.Client()
bot = commands.Bot(command_prefix = "!")

def clear():
    if platform.system() == "Windows": os.system("cls")
    else: os.system("clear")

async def start(token): global bot; await bot.start(token)

def error(string): print(f"Error: no {string} found!"); return 1

async def printer(mode, string, display = False):
    tones = 0xea3c50
    image = "https://i.imgur.com/NcjngFw.png"
    embed = discord.Embed(description = string, color = tones)
    if display: embed.set_thumbnail(url = image)
    await mode.send(embed = embed)

def main():
    global bot, wait, logo
    clear()
    try: wait = abs(float(sys.argv[1]))
    except: pass
    name = "Token.txt"
    try: file = open(name, "r")
    except: return error(name)
    token = file.read()
    file.close()
    if not token: return error("token")
    name = "Scores.txt"
    try: file = open(name, "r")
    except: return error(name)
    file.close()
    name = "Random.txt"
    try: file = open(name, "r")
    except: return error(name)
    lines = file.read().splitlines()
    file.close()
    if not lines: return error("words")
    print(logo[1:])
    loop = asyncio.get_event_loop()
    try: loop.run_until_complete(start(token))
    except: clear()
    loop.run_until_complete(on_end())
    loop.run_until_complete(bot.logout())

@bot.event
async def on_ready():
    global channel, instructions
    name = "simon-says"
    guild = bot.guilds[0]
    for text_channel in guild.text_channels:
        if text_channel.name == name: channel = text_channel; break
    if not channel: channel = await guild.create_text_channel(name)
    await channel.purge()
    await printer(channel, "Online :white_check_mark:")
    await asyncio.sleep(1)
    await printer(channel, instructions, True)
    await asyncio.sleep(1)
    await play()

async def on_end():
    global channel
    await channel.purge()
    await printer(channel, "Offline :octagonal_sign:")

async def play():
    global wait, word, trick, taken, channel
    order = ["write", "shuffle"]
    while True:
        string = ""
        delay = 60 * wait
        mode = random.choice(order)
        if random.random() < 0.15: mode = "vote"
        if random.random() < 0.15: mode = "meme"
        file = open("Random.txt", "r")
        lines = file.read().splitlines()
        file.close()
        temp = word = random.choice(lines)
        word = word.upper()
        if mode in order or mode == "meme":
            string = ""
            if mode != "meme":
                if "\\" in word:
                    word = temp.encode().decode("unicode-escape")
                    string = f"Simon says emote {word}"
                elif mode == "write":
                    string = f"Simon says write *{word}*"
                else:
                    shuffled = list(word)
                    random.shuffle(shuffled)
                    shuffled = "".join(shuffled)
                    string = f"Simon says descramble *{shuffled}*"
            else: word = "send a meme"; string = f"Simon says {word}!"
            if random.random() < 0.2:
                string = string.replace("Simon says ", "")
                string = string[0].capitalize() + string[1:]
                trick = True
            await printer(channel, string)
        else:
            word = "vote suggestions"
            await printer(channel, f"Simon says I need you to vote in some new words... start typing!")
        await asyncio.sleep(delay)
        votes = taken = []
        trick = False

async def sort_scores(id, points = 0):
    name = "Scores.txt"
    file = open(name, "r")
    lines = file.read().splitlines()
    file.close()
    new = points
    found = False
    for i in range(0, len(lines)):
        line = lines[i].split("|")
        if id == int(line[0]):
            new = int(line[1]) + points
            lines[i] = f"{line[0]}|{new}"
            found = True; break
        else: lines[i] = lines[i] = "|".join(line)
    if not found: lines.append(f"{id}|{points}")
    lines = sorted(lines, key = lambda line: int(line.split("|")[1]), reverse = True)
    file = open(name, "w")
    file.write("\n".join(lines))
    file.close()
    return new

async def check_scores(ctx, arg, mode):
    count = 0
    string = ""
    await sort_scores(ctx.message.author.id)
    file = open("Scores.txt", "r")
    lines = file.read().splitlines()
    file.close()
    for i in range(0, len(lines)):
        line = lines[i].split("|")
        id = int(line[0])
        name = await bot.fetch_user(id)
        name = str(name.name).lower()
        if mode == "me" and arg == id:
            string = f"You: {line[1]}"; break
        elif mode == "name" and arg in name or mode == "all":
            text = fr"{name.capitalize()}: {line[1]}"
            if count == 0: string = f"{text}"
            if count == 1: string = f"\n• {string}\n"
            if count >= 1: string += f"• {text}\n"
            count += 1
    if not string and mode == "name": string = "Error: no players found!"
    await printer(ctx.author, string)

async def update_scores(author, won):
    global taken
    id = author.id
    if id not in taken:
        string = ""
        if taken or won < 0:
            total = await sort_scores(id, won)
            if won > 0:
                string = f"Congrats! You won *{won}* points. You now have *{total}* points total."
            else:
                string = f"I did not say 'Simon says' so you lost *{abs(won)}* points. You now have *{total}* points total."
        elif not taken:
            won += 10
            total = await sort_scores(id, won)
            string = f"Woah! You won first so you get *{won}* points. You now have *{total}* points total."
        taken.append(id)
        await printer(author, string)
    else: await printer(author, f"You already got your points!")

@bot.event
async def on_reaction_add(reaction, user):
    global word, trick, votes, special
    if user != bot.user:
        message = reaction.message
        if special == message and reaction.emoji == word:
            if not trick: await update_scores(user, 10)
            else: await update_scores(user, -5)
        elif (word == "vote suggestions" and reaction.emoji == "\u2705"
        and message in votes):
            react = get(message.reactions, emoji = reaction.emoji)
            if react and react.count >= 5:
                votes.remove(message)
                await update_scores(message.author, 20)
                await message.add_reaction("\U0001f31f")
                raw = message.content.lower()
                raw = raw.encode("unicode-escape").decode("ascii")
                file = open("Random.txt", "r+")
                lines = file.read().splitlines()
                if raw not in lines: file.write(f"\n{raw}")
                file.close()

@bot.command(pass_context = True)
async def simon(ctx, *arg):
    global channel, instructions
    message = ctx.message
    author = message.author
    if message.channel == channel or not message.guild:
        if len(arg) == 0 or (arg[0] == "help" and len(arg) == 1):
            await printer(author, instructions)
        elif arg[0] == "score" and len(arg) <= 2:
            mode = ""
            if len(arg) == 2: mode = arg[1].lower()
            if len(arg) == 1 or mode == "me":
                await check_scores(ctx, message.author.id, "me")
            elif mode == "all":
                await check_scores(ctx, mode, "all")
            else:
                await check_scores(ctx, mode, "name")
        else: await printer(author, "Error: incorrect arguments!")

@bot.event
async def on_message(message):
    global word, votes, trick, special, channel
    author = message.author
    raw = message.content
    raw = raw.replace("_", "").replace("*", "")
    raw = raw.replace("|", "").replace("/spoiler message:", "")
    raw = raw.upper()
    if author != bot.user and message.channel == channel and "!" not in raw:
        plain = raw.encode("unicode-escape").decode("ascii")
        if word != "vote suggestions":
            won = 0
            if word == "send a meme" and message.attachments: won = 15
            elif raw == word: won = 10
            if won != 0 and trick: won = -5
            if won != 0: await update_scores(author, won)
        elif (plain.isascii() and " " not in plain and plain.count("\\") <= 1
        and not message.attachments):
            votes.append(message)
            await message.add_reaction("\u2705")
    elif author == bot.user and message.guild: special = message
    await bot.process_commands(message)

sys.exit(main())
