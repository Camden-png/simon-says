logo = """
 ____ ____ ____ ____ ____ _________ ____ ____ ____ ____
||S |||i |||m |||o |||n |||       |||S |||a |||y |||s ||
||__|||__|||__|||__|||__|||_______|||__|||__|||__|||__||
|/__\|/__\|/__\|/__\|/__\|/_______\|/__\|/__\|/__\|/__\|"""

instructions = """Commands:
• !simon score all - check all scores
• !simon score me - check your score
• !simon score name - check other players' score"""

import os
import sys
import time
import json
import random
import asyncio
import platform
import unicodedata

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("Error: no Discord library found!")
    sys.exit(1)

wait = 0.5
word = ""
words = []
taken = []
channel = None

bot = discord.Client()
bot = commands.Bot(command_prefix = "!")

def clear():
    if platform.system() == "Windows": os.system("cls")
    else: os.system("clear")

async def start(token): global bot; await bot.start(token)

def printer_1(string): print(f"Error: no {string} found!")

async def printer_2(mode, string, display = False):
    global image
    tone = 0xea3c50; image = "https://i.imgur.com/NcjngFw.png"
    embed = discord.Embed(description = string, color = tone)
    if display: embed.set_thumbnail(url = image)
    await mode.send(embed = embed)

def open_file(name_1, name_2 = None):
    try: file = open(name_1, "r")
    except: printer_1(name_1)
    line = file.read()
    if name_2 and not line: printer_1(name_2)
    file.close()
    if name_2: return line
    else: return "Start"

def main():
    global bot; global logo; global words; clear()
    token = open_file("Token.txt", "token")
    if not token: return 1
    if not open_file("Scores.txt"): return 1
    lines = open_file("Random.txt", "words")
    if not lines: return 1
    words = lines.split("\n")
    print(logo)
    loop = asyncio.get_event_loop()
    try: loop.run_until_complete(start(token))
    except: clear()
    loop.run_until_complete(on_end())
    loop.run_until_complete(bot.logout())

async def play():
    global wait; global word; global words; global taken; global channel
    order = ["meme", "write", "shuffle"]
    random.shuffle(words)
    i = 0
    while True:
        string = ""
        delay = 60 * wait
        random.shuffle(order)
        mode = order[0]
        if mode != "meme":
            word = words[i].upper()
            try: string = f"Simon says emote  {unicodedata.lookup(word)}"
            except: pass
            if not string and mode == "write": string = f"Simon Says write *{word}*."
            elif not string and mode == "shuffle":
                shuffled = list(word)
                random.shuffle(shuffled)
                string = f"Simon Says descramble *{''.join(shuffled)}*."
            await printer_2(channel, string)
            if i == len(words) - 1: i = 0
            else: i += 1
        else: word = "send a meme"; await printer_2(channel, f"Simon Says {word}!")
        await asyncio.sleep(delay)
        taken = []

@bot.event
async def on_ready():
    global bot; global channel; global instructions
    name = "simon-says"
    guild = bot.guilds[0]
    for text_channel in guild.text_channels:
        if text_channel.name == name: channel = text_channel; break
    if not channel: channel = await guild.create_text_channel(name)
    await channel.purge()
    await printer_2(channel, "Online  :white_check_mark:")
    await asyncio.sleep(1)
    await printer_2(channel, instructions, True)
    await asyncio.sleep(1)
    await play()

async def on_end():
    global bot; global channel
    await channel.purge()
    await printer_2(channel, "Offline  :octagonal_sign:")

async def sort_scores(name, id, points = 0):
    file = open(name, "r")
    lines = file.readlines()
    file.close()
    file = open(name, "w")
    found = False; temp_1 = points
    for i in range(0, len(lines)):
        line = lines[i].strip()
        temp_2 = line
        line = line.split("-")
        temp_1 = str(int(line[1]) + points)
        if id == int(line[0]):
            lines[i] = f"{line[0]}-{temp_1}"
            found = True
        else: lines[i] = temp_2
    if not found: lines.append(f"{id}-{points}")
    lines = sorted(lines, key = lambda line: int(line.split("-")[1]), reverse = True)
    file.write("\n".join(lines))
    file.close()
    if points == 0: return lines
    else: return temp_1

async def check_scores(ctx, arg):
    count = 0
    mode = arg
    id_1 = ctx.message.author.id
    string = ""; name = "Scores.txt"
    lines = await sort_scores(name, id_1)
    file = open(name, "r+")
    if type(arg) == int: mode = "id"
    elif arg != "all": mode = "name"
    if mode in ["id", "name", "all"]:
        for i in range(0, len(lines)):
            line = lines[i].split("-")
            id_2 = int(line[0])
            name = await bot.fetch_user(id_2)
            name = str(name.display_name)
            if mode == "id" and id_1 == id_2:
                string = f"You: {line[1]}"; break
            elif mode != "id" and arg in name.lower() or mode == "all":
                name = json.dumps(name.capitalize())[1:-1]
                text = f"{name}: {line[1]}"
                if count == 0: string = f"{text}"
                if count == 1: string = f"\n• {string}\n"
                if count >= 1: string += f"• {text}\n"
                count += 1
    else: string = "Error: incorrect arguments!"
    if not string and mode == "name": string = "Error: no players found!"
    await printer_2(ctx, string)
    file.close()

@bot.command(pass_context = True)
async def simon(ctx, *arg):
    global bot; global channel
    message = ctx.message
    if message.channel == channel:
        if arg[0] == "score" and len(arg) <= 2:
            if len(arg) == 1 or arg[1].lower() == "me":
                await check_scores(ctx, int(message.author.id))
            else: await check_scores(ctx, arg[1].lower())
        else: await printer_2(ctx, "Error: incorrect arguments!")

@bot.event
async def on_message(message):
    global bot; global word; global taken; global channel
    author = message.author; id = author.id
    if author != bot.user and message.channel == channel:
        points_1 = 0
        raw = message.content.upper()
        try: raw = unicodedata.name(raw)
        except: pass
        if word == "send a meme":
            try: meme = message.attachments[0].url; points_1 = 5
            except: pass
        elif raw == word: points_1 = 10
        if points_1 != 0 and id not in taken:
            taken.append(id)
            points_2 = await sort_scores("Scores.txt", author.id, points_1)
            await printer_2(author, f"Congrats! You won *{points_1}* points. You now have *{points_2}* points total.")
        elif points_1 != 0 and id in taken: await printer_2(author, f"You already got your points!")
    await bot.process_commands(message)

sys.exit(main())
