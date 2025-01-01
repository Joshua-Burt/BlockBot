import operator
from itertools import count
from os.path import exists, split
from pathlib import Path
from colorama import Fore
from discord import option
from mutagen.mp3 import MP3

import asyncio
import json
import os
import discord

from bot import bot
from log import log
from json_utils import update_user, get_sound_price, get_user_field, add_sound, add_sound_uses

is_playing = False
sound_queue = []
sound_dict = {}


async def init():
    global sound_dict

    with open('../json_files/item_prices.json', 'r') as file:
        sound_dict = json.load(file)

    if not os.path.exists("../sounds") or \
       not os.path.exists("../sounds/intros") or \
       not os.path.exists("../sounds/shop_sounds"):
        await create_file_structure()


async def create_file_structure():
    await log("Creating sounds directory")
    os.makedirs("../sounds/intros", exist_ok=True)
    os.makedirs("../sounds/shop_sounds", exist_ok=True)


@bot.slash_command(name="shop", description="Display the sounds shop")
async def shop(ctx: discord.ApplicationContext):
    messages = [""]
    messages[0] = "Use **/play *[Sound Name]*** to play the sound\n"
    max_message_length = 2000
    message_count = 0

    for sound_name in sound_dict:
        if len(messages[message_count]) >= max_message_length - 100:
            message_count = message_count + 1
            messages.insert(message_count, "")
        
        sound_price = sound_dict[sound_name]['price']
        messages[message_count] += f"> Name: **{sound_name}** | Price: **{sound_price:,}**\n"
    
    for i in range(len(messages)):
        if i == 0:
            await ctx.respond(messages[i])
        else:
            await ctx.channel.send(messages[i])


async def get_sorted_sound_list(ctx: discord.AutocompleteContext):
    sorted_keys = sorted(sound_dict.items(), key=lambda r: r[1]['times_used'], reverse=True)
    return [sound_name[0] for sound_name in sorted_keys]


@bot.slash_command(name="play", description="Play a sound")
@option(
    "sound_name",
    description="Name of the sound you want to play",
    autocomplete=get_sorted_sound_list,
    required=True,
)
async def pay_to_play(ctx: discord.ApplicationContext, sound_name):
    current_points = await get_user_field(ctx.author.id, "points")
    cost = await get_sound_price(sound_name)

    if ctx.author.voice is None:
        await ctx.respond("You ain't in no channel", ephemeral=True)
        return

    if cost is None:
        await ctx.respond("There's no sound with that name ¯\\_(ツ)_/¯", ephemeral=True)
        return

    if current_points >= cost:
        await ctx.respond(f"Playing {sound_name}.mp3")
        await log(f"Playing {Fore.YELLOW + sound_name}.mp3{Fore.RESET}")
        await add_sound_uses(sound_name)
        await add_to_queue(ctx.author, f"../sounds/shop_sounds/{sound_name}.mp3")

        await update_user(ctx.author.id, "points", current_points - cost)
    else:
        await ctx.respond("Aha you're poor. You're missing {:,} points".format(
            await get_sound_price(sound_name) - await get_user_field(ctx.author.id, "points")), ephemeral=True)


@bot.slash_command(name="air_drop", description="Play a sound in a channel (2x listed price)")
@option(
    "sound_name",
    description="Name of the sound you want to play",
    autocomplete=get_sorted_sound_list,
    required=True,
)
async def air_drop(ctx: discord.ApplicationContext, sound_name, channel: discord.VoiceChannel):
    current_points = await get_user_field(ctx.author.id, "points")
    cost = await get_sound_price(sound_name) * 2

    if channel is None:
        await ctx.respond("That's not a channel", ephemeral=True)
        return

    if cost is None:
        await ctx.respond("There's no sound with that name ¯\\_(ツ)_/¯", ephemeral=True)
        return

    if current_points >= cost:
        await ctx.respond(f"Playing {sound_name}.mp3")
        await log(f"Playing {Fore.YELLOW + sound_name}.mp3{Fore.RESET}")

        await add_sound_uses(sound_name)
        await add_to_queue_channel(ctx.author, channel, f"../sounds/shop_sounds/{sound_name}.mp3")

        await update_user(ctx.author.id, "points", current_points - cost)
    else:
        await ctx.respond("Aha you're poor. You're missing {:,} points".format(
            await get_sound_price(sound_name) - await get_user_field(ctx.author.id, "points")), ephemeral=True)


@bot.slash_command(name="add_to_shop", description="Adds a new sound to the shop", )
@option(
    "attachment",
    discord.Attachment,
    description="An .mp3 file to add to the shop",
    required=True,
)
async def add_to_shop(ctx: discord.ApplicationContext, attachment: discord.Attachment, cost, name: discord.Option(str) = ""):
    if not cost.isnumeric():
        await ctx.respond("The cost must be a number", ephemeral=True)

    if int(cost) < 0:
        await ctx.respond("The cost cannot be negative", ephemeral=True)

    if attachment.content_type != "audio/mpeg":
        await ctx.respond("Please upload an .mp3 file", ephemeral=True)

    file = await attachment.to_file()

    if name != "":
        file_name = name
    else:
        file_name = os.path.splitext(file.filename)[0]

    await attachment.save(Path(str(Path.cwd()) + f"/../sounds/shop_sounds/{str(file_name)}.mp3"))
    await add_sound(file_name, int(cost))

    await ctx.respond(f"Sound {file_name} has been added", ephemeral=True)
    await log(f"Added sound {Fore.YELLOW + file_name + Fore.RESET} to shop")


@bot.slash_command(name="de", description="Stomp your way out")
async def dramatic_exit(ctx: discord.ApplicationContext):
    if ctx.author.voice is not None:
        await ctx.respond("Dramatic.", ephemeral=True)
        await add_to_queue(ctx.author, "../sounds/slam.mp3")
    else:
        await ctx.respond("How can you exit that which you are not in?", ephemeral=True)


async def dramatic_exit_kick(author):
    await asyncio.sleep(3.5)
    await author.move_to(None)


async def play_queue():
    global is_playing
    is_playing = True

    while len(sound_queue) > 0:
        sound_dict = sound_queue.pop(0)
        voice = await play_sound(sound_dict)

        # Disconnect from the voice channel is there are no more sounds to play
        if len(sound_queue) == 0:
            await voice.disconnect()
            break

        # Disconnect from the voice channel if the next sound isn't in the same channel
        if sound_dict["channel"] != sound_queue[0]["channel"]:
            await voice.disconnect()

    is_playing = False


async def play_sound(sound_dict):
    path = sound_dict["path"]
    if not exists(path):
        return

    voice_channel = sound_dict["channel"]
    if not voice_channel:
        return

    # Prevents an error where the bot is sometimes still in a voice channel
    try:
        voice = await sound_dict["channel"].connect()
    except discord.ClientException:
        for x in bot.voice_clients:
            if x.guild == sound_dict["member"].guild:
                await x.disconnect()
                break

        voice = await sound_dict["channel"].connect()

    # Stay in this channel as long as the next sound is in the same channel
    while True:
        audio_length = MP3(path).info.length
        voice.play(discord.FFmpegPCMAudio(source=path, options="-loglevel panic"))

        voice.pause()
        await asyncio.sleep(0.5)
        voice.resume()

        if sound_dict["path"] == "../sounds/slam.mp3":
            await dramatic_exit_kick(sound_dict["member"])
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(audio_length + 2)

        # Break from the loop if there's no sounds
        if len(sound_queue) == 0:
            break

        # Change the path to the next sound if they are contained within the same channel
        if sound_queue[0]["channel"] == sound_dict["channel"]:
            path = sound_queue.pop()["path"]
        else:
            break

    return voice


async def add_to_queue_channel(member: discord.Interaction.user, channel: discord.VoiceChannel, sound_path):
    sound_queue.append({"channel": channel, "path": sound_path, "member": member})
    if not is_playing:
        await play_queue()


async def add_to_queue(member: discord.Interaction.user, sound_path):
    sound_queue.append({"channel": member.voice.channel, "path": sound_path, "member": member})
    if not is_playing:
        await play_queue()
