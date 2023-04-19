import asyncio
import json
from os import walk
from os.path import exists
from pathlib import Path

import discord
from colorama import Fore
from discord import option
from mutagen.mp3 import MP3

from bot import bot
from log import log
import json_utils

sound_queue = []
sound_list = []


async def init():
    global sound_list

    with open('../json_files/item_prices.json', 'r') as file:
        sound_list = json.load(file)


@bot.slash_command(name="shop", description="Display the sounds shop")
async def shop(ctx):
    string = "Use **/play *[Sound Name]*** to play the sound\n"

    for sound_name in sound_list:
        string += f"> Name: **{sound_name}** | Price: **{sound_list[sound_name]['price']:,}**\n"

    await ctx.respond(string)


@bot.slash_command(name="play", description="Play a sound")
@option(
    "sound_name",
    description="Name of the sound from the shop",
    required=True,
    default=""
)
async def pay_to_play(ctx, sound_name):
    current_points = json_utils.get_user_field(ctx.author.id, "points")
    cost = json_utils.get_sound_price(sound_name)

    if cost is None:
        await ctx.respond("There's no sound with that name ¯\\_(ツ)_/¯")
        return

    if current_points >= cost:
        await ctx.respond(f"Playing {sound_name}.mp3")
        await log(f"Playing {Fore.YELLOW + sound_name}.mp3{Fore.RESET}")

        await play_sound(ctx.author, f"sounds/pay_to_play/{sound_name}.mp3")

        json_utils.update_user(ctx.author.id, "points", current_points - cost)
    else:
        await ctx.respond("Aha you're poor. You're missing {:,} points".format(
            json_utils.get_sound_price(sound_name) - json_utils.get_user_field(ctx.author.id, "points")))


async def play_sound(member: discord.Member, source_name):
    if exists(source_name):

        channel = member.voice.channel
        sound_queue.append(source_name)

        if channel and bot.user not in channel.members:
            voice = await channel.connect()

            while len(sound_queue) > 0:
                source = sound_queue.pop(0)
                audio_length = MP3(source).info.length
                voice.play(discord.FFmpegPCMAudio(executable="../ffmpeg/bin/ffmpeg.exe", source=source))

                voice.pause()
                await asyncio.sleep(0.5)
                voice.resume()

                await asyncio.sleep(audio_length + 2)

            await voice.disconnect(force=True)