import os
import subprocess
import discord
from bot import bot
from log import log

process = None
server_path = ""
default_activity = ""
error_messages = {"1": "There is no server currently configured.",
                  "2": "The server file defined in config.json does not exit."}


async def init(minecraft_server_path, bot_default_activity):
    global server_path, default_activity
    
    server_path = minecraft_server_path
    default_activity = bot_default_activity


async def verify_server_path():
    if server_path == "":
        return 1
    elif not os.path.exists(server_path):
        return 2


@bot.slash_command(name="start", description="Start the Minecraft Server")
async def start_server(ctx):
    verify_server_path_rc = await verify_server_path()
    if verify_server_path_rc != 0:
        await ctx.respond(error_messages.get(str(verify_server_path_rc)), ephemeral=True)
        return

    await log("Starting server...")
    await start(ctx, server_path)

    game = discord.Game("Minecraft")
    await bot.change_presence(status=discord.Status.online, activity=game)


@bot.slash_command(name="stop", description="Stop the Minecraft Server")
async def stop_server(ctx):
    verify_server_path_rc = await verify_server_path()
    if verify_server_path_rc != 0:
        await ctx.respond(error_messages.get(str(verify_server_path_rc)), ephemeral=True)
        return

    await log("Stopped the server")
    await stop(ctx)

    game = discord.Game(default_activity)
    await bot.change_presence(status=discord.Status.online, activity=game)


@bot.slash_command(name="command", description="Send a Minecraft server command")
async def server_command(ctx, command):
    verify_server_path_rc = await verify_server_path()
    if verify_server_path_rc != 0:
        await ctx.respond(error_messages.get(str(verify_server_path_rc)), ephemeral=True)
        return

    global process
    if process is None:
        await ctx.respond("The server is not running", ephemeral=True)
    else:
        output = process.communicate(command, timeout=10)[0]
        await ctx.respond("Command sent, " + output, ephemeral=True)


async def start(ctx, minecraft_server_path):
    global process

    if process:
        await ctx.respond("The server is already running")
    else:
        await ctx.respond("Starting server...")

        # Find and assign the current directory
        working_directory = os.getcwd()

        # Go to the Server's directory and start the server using the run.sh file
        os.chdir(minecraft_server_path)
        process = subprocess.Popen(['run.sh'], stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_CONSOLE,
                                   encoding='utf8')

        # Return to the original directory
        os.chdir(working_directory)

        # TODO: Check for server being online


async def stop(ctx):
    global process
    if process:
        await server_command(ctx, "stop")
        await ctx.respond("Stopped the server")
        process = None
    else:
        await ctx.respond("The server isn't running")


async def ping_ip(ip, port):
    raise NotImplementedError
