import json
import os
import random
import shutil

from log import log

price_file = {}
youre_welcomes = {}
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

    with open('../youre_welcome.txt', 'r') as f:
        youre_welcomes_data = f.read().split("\n")

    global users_file
    users_file = user_data

    global price_file
    price_file = price_data

    global youre_welcomes
    youre_welcomes = youre_welcomes_data

    return True


async def reload_files():
    await init()


# USER JSON
def add_user(member_id):
    if get_user_field(member_id, "file_name") is None:
        users_file[str(member_id)] = {
            "file_name": str(member_id) + ".mp3",
            "points": 100,
            "bets": 0,
            "play_on_enter": False
        }

        # Dump into file
        with open('../json_files/users.json', 'w') as f:
            json.dump(users_file, f, indent=4)


def update_user(member_id, field, value):
    if users_file is None:
        raise Exception("users_files in json_utils.py is None")

    json_member = users_file[str(member_id)]

    if json_member is not None:
        users_file[str(member_id)][field] = value

        # Dump into file
        with open('../json_files/users.json', 'w') as f:
            json.dump(users_file, f, indent=4)


def get_user_field(member_id, field):
    if users_file is None:
        raise Exception("users_files in json_utils.py is None")

    if str(member_id) in users_file:
        json_member = users_file[str(member_id)]
        return json_member[field]
    return None


def pick_random_user():
    return random.choice(users_file)


# SOUNDS JSON
def get_sound_price(sound_name):
    """
    :param sound_name: name of sound to be played
    :type sound_name: str
    :returns: price to play the sound with the name
    :rtype: int or None
    """

    if price_file is None:
        raise Exception("price_file in json_utils.py is None")

    if sound_name in price_file:
        return price_file[sound_name]["price"]
    return None


def set_sound_price(sound_name):
    if price_file is None:
        raise Exception("price_file in json_utils.py is None")

    return price_file[sound_name]["price"]


# YOU'RE WELCOME JSON
async def get_random_youre_welcome():
    if youre_welcomes is None:
        raise Exception("price_file in json_utils.py is None")

    return random.choice(youre_welcomes)


def verify_file(fn):
    if os.path.exists("../json_files/" + fn + ".json"):
        return True

    if os.path.exists("../default/" + fn + ".json"):
        print("File ../json_files/" + fn + ".json does not exist. Creating file.")
        shutil.copy("../default/" + fn + ".json", "../json_files/" + fn + ".json")
        return True
    else:
        return "Default file " + fn + " not detected"


async def verify_files():
    # Verify .json files exist
    file_names = ["config", "item_prices", "jackpot", "users"]

    for fn in file_names:
        verify = verify_file(fn)
        if verify is not True:
            return verify

    return True