import discord
import json
import sys
from colorama import Fore


# Local files
import roll
import poll
import gamble
import intro
import json_utils
import server
import sounds
import wordle
from log import log, log_error
from bot import bot


async def init_all():
    config = get_config()
    await init_components(config)
    await set_default_activity(config["default_activity"])


def get_config():
    # Will exit if config.json is not found
    verify_config_integrity()

    with open('../json_files/config.json', 'r') as f:
        config = json.load(f)

    # Constants
    discord_token = config["token"]

    if discord_token == "":
        print(Fore.RED + "Default token given. Please change token in config.json")
        sys.exit()

    return config


async def init_components(config):
    # Verify that the required .json files exist
    json_msg = await json_utils.init()
    if json_msg is not True:
        await log_error(json_msg)
        await bot.close()

    await intro.init(config["max_intro_length"])
    await gamble.init(config["gamble_channel"])
    await wordle.init(config["wordle_channel"])
    await server.init(config["server_path"])
    await sounds.init()


def verify_config_integrity():
    # Load config file to obtain the token
    config_integrity = json_utils.verify_file("config")
    if config_integrity is not True:
        print(Fore.RED + config_integrity)
        sys.exit()

    return True


async def set_default_activity(activity):
    game = discord.Game(activity)
    await bot.change_presence(status=discord.Status.online, activity=game)