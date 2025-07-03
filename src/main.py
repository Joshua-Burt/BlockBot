import discord
from colorama import Fore

import initialize
# Local Files
import json_utils
import gamble
import wordle

from log import log, log_error
from bot import bot


@bot.event
async def on_ready():
    # Startup printing, username, etc.
    await log(f'Logged in as {bot.user}' + Fore.YELLOW + '\nPowered on [o.o]' + Fore.RESET)
    print("---------------------------------")

    await initialize.init_all()

    await start_points_loop()

    if not wordle.wordle_loop.is_running():
        wordle.wordle_loop.start()


@bot.event
async def on_member_join(member: discord.Member):
    if member.bot:
        return

    await log(f"Adding member {Fore.YELLOW + member.name + Fore.RESET}")
    await json_utils.add_user(member.id)


@bot.slash_command(name="say", description="Repeat the inputted message")
async def say(ctx: discord.ApplicationContext, message: str):
    await ctx.send(message)
    await ctx.respond("Said the words", ephemeral=True)


@bot.message_command(name="mock_message", description="Mock the selected message")
async def mock_message(ctx: discord.ApplicationContext, message: discord.Message):
    if message.author == bot.user:
        await ctx.respond('no')
    else:
        message_text = message.content

        if len(message_text) > 0:
            await ctx.respond(await mockify(message_text))
        else:
            await ctx.respond("There wasn't any text to mock", ephemeral=True)


@bot.slash_command(name="mock", description="Mock the last message sent")
async def mock(ctx: discord.ApplicationContext):
    logs = await ctx.channel.history(limit=1).flatten()

    if logs[0].author == bot.user:
        await ctx.respond('no')
    else:
        message_text = logs[0].content

        if len(message_text) > 0:
            await ctx.respond(await mockify(message_text))
        else:
            await ctx.respond("There wasn't any text to mock", ephemeral=True)


@bot.slash_command(name="pyramid", description="M MA MAK MAKE A P PY PYR PYRA PYRAM PYRAMI PYRAMID")
async def pyramid(ctx: discord.ApplicationContext, word: str):
    if len(word) < 45:
        await ctx.respond(await word_pyramid(word))
    else:
        await ctx.respond("Due to Discord's 2000 character limit for messages, 44 characters is the maximum length for a pyramid :(", ephemeral=True)


@bot.slash_command(name="pay", description="Pay amount of points to another user")
async def pay(ctx: discord.ApplicationContext, payee: str, amount: int):
    if len(payee) > 0 and amount > 0:
        if await json_utils.get_user_field(ctx.author.id, "points") > amount:

            payee_id = payee.strip("<@!>")
            payee_member = await json_utils.get_user_from_id(payee_id)

            if payee_member is None or await json_utils.get_user_field(payee_id, "points") is None:
                await ctx.respond(f"User '{payee}' does not exist in the system")
                return

            await gamble.pay_points(ctx.author.id, payee_id, amount)

            await ctx.respond("**{}** paid **{}** - **{:,}** points".format(
                await json_utils.get_user_from_id(str(ctx.author.id)),
                payee_member, amount))
    else:
        await ctx.respond("You must provide a valid @username and payment amount")


@bot.slash_command(name="nick", description="Change the nickname of a user")
async def nick(ctx: discord.ApplicationContext, username: str, new_nick: str):
    if len(username) > 0 and len(new_nick) > 0:
        if len(new_nick) > 32:
            await ctx.respond("Nicknames cannot be longer than 32 characters", ephemeral=True)
            return

        try:
            user = await ctx.guild.fetch_member(int(username.strip("<@!>")))

        # Intercepts an exception when a user does not provide a snowflake.
        except discord.errors.HTTPException:
            await ctx.respond("Please include the '@' at the start of the name of the user you wish to change",
                              ephemeral=True)

        else:
            await user.edit(nick=new_nick)
            await ctx.respond(f"Changed {user.name}'s nickname to {new_nick}", ephemeral=True)


@bot.slash_command(name="change_activity", description="Change the bot's current activity")
async def change_activity(ctx: discord.ApplicationContext, new_activity: str):
    game = discord.Game(new_activity)
    await bot.change_presence(status=discord.Status.online, activity=game)
    await ctx.respond(f"Changed activity to \"{new_activity}\"", ephemeral=True)


@bot.event
async def on_message(message: discord.Message):
    # Don't respond to bot messages, that spells disaster
    if message.author.bot:
        return

    saying = await json_utils.get_saying_from_trigger(message)
    if saying:
        response = await json_utils.get_random_response(saying)

        # Prevent a blank message from being sent
        if len(response) > 0:
            await message.channel.send(response)
        else:
            await log_error("on_message - Responses must be longer than 0 characters")


# Helper functions

async def start_points_loop():
    guilds = bot.guilds
    voice_channels = []
    afk_channels = []

    # Find all voice channels that the bot connects to, then add that to the respective list
    for guild in guilds:
        # Get all non-afk channels
        for channel in guild.voice_channels:
            voice_channels.append(channel.id)

        # Add the afk channel, if it exists
        if guild.afk_channel:
            afk_channels.append(guild.afk_channel.id)

    if not gamble.points_loop.is_running():
        gamble.points_loop.start(voice_channels, afk_channels)


# Transforms a word into a pyramid:
# H
# HE
# HEL
# HELL
# HELLO
# HELL
# HEL
# HE
# H
async def word_pyramid(word: str):
    final_str = ""
    for i in range(len(word) + 1):
        for j in range(i):
            final_str += word[j]
        final_str += "\n"

    for i in range(len(word)):
        for j in range(len(word) - i - 1):
            final_str += word[j]
        final_str += "\n"

    return final_str


# Transforms a string into a mocked string
# e.g. "Spongebob" -> "SpOnGeBoB"
async def mockify(in_str: str):
    new_string = ""
    case = True  # true = uppercase, false = lowercase

    for i in in_str:
        if case:
            new_string += i.upper()
        else:
            new_string += i.lower()
        if i != ' ':
            case = not case
    return new_string


class Error(Exception):
    def __init__(self, message):
        super().__init__(Fore.RED + message)


def main():
    config = initialize.get_config()
    bot.run(config["token"])


if __name__ == "__main__":
    main()
