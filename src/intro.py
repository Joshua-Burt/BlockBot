from pathlib import Path

import discord
from colorama import Fore
from discord import option
from mutagen.mp3 import MP3

from bot import bot
import json_utils
import sounds
from log import log

max_length = 0


async def init(max_intro_length):
    global max_length
    max_length = max_intro_length


@bot.slash_command(name="intro", description="Toggle your intro when joining a voice call")
async def intro(ctx):
    new_play_on_enter = not await json_utils.get_user_field(ctx.author.id, "play_on_enter")
    await json_utils.update_user(ctx.author.id, "play_on_enter", new_play_on_enter)

    await ctx.respond("Your intro is now " + ("ON" if new_play_on_enter else "OFF"), ephemeral=True)


@bot.slash_command(name="upload_other", description="Upload an .mp3 file to change someone else's intro")
@option(
    "attachment",
    discord.Attachment,
    description=f"An .mp3 file to be used as given user's intro. Max {str(max_length)} seconds.",
    required=True,
)
async def upload_others_intro(ctx: discord.ApplicationContext, attachment: discord.Attachment, username):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("You must have the administrator permission to change other members' intros", ephemeral=True)
        return

    if len(username) > 0:
        try:
            user = await ctx.guild.fetch_member(username.strip("<@!>"))

        # Intercepts an exception when a user does not provide a snowflake.
        except discord.errors.HTTPException:
            await ctx.respond("Please include the '@' at the start of the name of the user you wish to change",
                              ephemeral=True)
        else:
            await change_intro(ctx, attachment, user)


@bot.slash_command(name="upload", description="Upload an .mp3 file to change your intro")
@option(
    "attachment",
    discord.Attachment,
    description=f"An .mp3 file to be used as your intro. Max {str(max_length)} seconds.",
    required=True,
)
async def upload_intro(ctx: discord.ApplicationContext, attachment: discord.Attachment):
    await change_intro(ctx, attachment, ctx.author)


async def change_intro(ctx, attachment, user):
    if attachment.content_type == "audio/mpeg":
        file = await attachment.to_file()

        # Verify the length is less than the max
        if MP3(file.fp).info.length > max_length:
            await ctx.respond(f"Intros must be less than {str(max_length)} seconds", ephemeral=True)
            return

        # Apply the new file
        file_name = await json_utils.get_user_field(user.id, "file_name")

        await attachment.save(Path(str(Path.cwd()) + f"/../sounds/intros/{str(file_name)}"))

        await ctx.respond(f"{user.name}'s intro has been changed", ephemeral=True)
        await log(f"Changed {Fore.YELLOW + str(user.name) + Fore.RESET}'s intro")
    else:
        await ctx.respond("Please upload an .mp3 file", ephemeral=True)


@bot.event
async def on_voice_state_update(member: discord.Member, before, after):
    if member.bot:
        return

    if not await json_utils.get_user_field(member.id, 'play_on_enter'):
        return

    if not before.channel and after.channel:
        filename = await json_utils.get_user_field(user.id, 'file_name')
        file_path = Path("../sounds/intros/" + filename)
        
        if file_path.exists():
            await log(f"Playing {Fore.YELLOW + member.display_name + Fore.RESET}'s intro in {Fore.YELLOW + member.voice.channel.name + Fore.RESET}")
            await sounds.add_to_queue(member, file_path.absolute())
