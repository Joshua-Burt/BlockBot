import json
import os
import random
import shutil

import discord

from bot import bot

item_prices_file = {}
sayings = {}
users_file = {}


async def init():
    valid_files = await verify_files()

    # Tell main that the files are not valid, and bot needs to be logged out
    if valid_files is not True:
        return valid_files

    with open('../json_files/users.json', 'r') as f:
        user_data = json.load(f)

    with open('../json_files/item_prices.json', 'r') as f:
        price_data = json.load(f)

    with open('../json_files/sayings.json', 'r') as f:
        sayings_data = json.load(f)

    global users_file
    users_file = user_data

    global item_prices_file
    item_prices_file = price_data

    global sayings
    sayings = sayings_data

    return True


@bot.slash_command(name="reload", description="Reload internal files")
async def reload_files(ctx):
    await init()
    await ctx.respond("Reloaded internal files", ephemeral=True)


# USER JSON

@bot.slash_command(name="add_user", description="Add a user to the internal files")
async def add_new_user(ctx, username):
    if len(username) > 0:
        try:
            user = await ctx.guild.fetch_member(username.strip("<@!>"))

        # Intercepts an exception when a user does not provide a snowflake.
        except discord.errors.HTTPException:
            await ctx.respond("Please include the '@' at the start of the name of the user you wish to change",
                              ephemeral=True)

        else:
            if await get_user_field(user.id, "file_name") is None:
                await add_user(user.id)
                await ctx.respond("User added to system", ephemeral=True)
            else:
                await ctx.respond("User is already in the system", ephemeral=True)


async def add_user(member_id):
    if await get_user_field(member_id, "file_name") is None:
        users_file[str(member_id)] = {
            "file_name": f"{str(member_id)}.mp3",
            "points": 1000,
            "bets": 0,
            "play_on_enter": False
        }

        # Dump into file
        with open('../json_files/users.json', 'w') as f:
            json.dump(users_file, f, indent=4)


async def update_user(member_id, field, value):
    if users_file is None:
        raise Exception("users_files in json_utils.py is None")

    json_member = users_file[str(member_id)]

    if json_member is not None:
        users_file[str(member_id)][field] = value

        # Dump into file
        with open('../json_files/users.json', 'w') as f:
            json.dump(users_file, f, indent=4)


async def get_user_field(member_id, field):
    if users_file is None:
        raise Exception("users_files in json_utils.py is None")

    if str(member_id) in users_file:
        json_member = users_file[str(member_id)]
        return json_member[field]
    return None


async def pick_random_user():
    return random.choice(users_file)


# SOUNDS JSON
async def get_sound_price(sound_name):
    """
    :param sound_name: name of sound to be played
    :type sound_name: str
    :returns: price to play the sound with the name
    :rtype: int or None
    """

    if item_prices_file is None:
        raise Exception("price_file in json_utils.py is None")

    if sound_name in item_prices_file:
        return item_prices_file[sound_name]["price"]
    return None


async def set_sound_price(sound_name, price):
    if item_prices_file is None:
        raise Exception("price_file in json_utils.py is None")

    item_prices_file[sound_name]["price"] = price

    # Dump into file
    with open('../json_files/item_prices.json', 'w') as f:
        json.dump(item_prices_file, f, indent=4)


async def add_sound_uses(sound_name):
    if item_prices_file is None:
        raise Exception("price_file in json_utils.py is None")

    item_prices_file[sound_name]["times_used"] = item_prices_file[sound_name]["times_used"] + 1

    # Dump into file
    with open('../json_files/item_prices.json', 'w') as f:
        json.dump(item_prices_file, f, indent=4)


async def add_sound(sound_name: str, price: int):
    if item_prices_file is None:
        raise Exception("price_file in json_utils.py is None")

    item_prices_file[sound_name] = {
        "price": price,
        "times_used": 0
    }

    with open('../json_files/item_prices.json', 'w') as f:
        json.dump(item_prices_file, f, indent=4)


def verify_file(fn):
    if os.path.exists("../json_files/" + fn + ".json"):
        return True

    # Verify the folder exists
    if not os.path.exists("../json_files/"):
        os.mkdir("../json_files/")

    # Checks if the default version of the file exists
    if os.path.exists("../default/" + fn + ".json"):
        print("File json_files/" + fn + ".json does not exist. Creating file.")
        shutil.copy("../default/" + fn + ".json", "../json_files/" + fn + ".json")
        return True
    else:
        return "Default file " + fn + " not detected"


async def verify_files():
    # Verify .json files exist
    file_names = ["config", "item_prices", "jackpot", "users", "sayings"]

    for fn in file_names:
        verify = verify_file(fn)
        if verify is not True:
            return verify

    return True


async def get_saying_from_trigger(message):
    # Convert the message to lowercase, as all triggers should be lowercase
    msg = message.content.lower()

    # Check each of the sayings to see if the message matches the trigger word
    # We are looking for complete matches, not just a substring of a sentence for instance
    for saying_id in sayings:
        if msg in sayings[saying_id]["trigger"]:
            # Return the id of the saying if the message exists in the trigger list
            return saying_id
    return None


async def get_random_response(saying_id):
    if saying_id is None:
        return

    return random.choice(sayings[saying_id]["response"])


async def get_user_from_id(user_id: str):
    """
    :param user_id: ID of the requested user.
    :returns: User with the corresponding ID.
    :rtype: discord.Member or None
    """
    
    # Attempt to find the user in cache
    name = bot.get_user(user_id)

    # Attempt to find the user with an API call
    if name is None:
        try:
            name = await bot.fetch_user(user_id)

        # Intercepts an exception when a user does not provide a snowflake.
        except discord.errors.HTTPException:
            name = None

    return name
