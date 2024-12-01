import calendar
import datetime
from collections import Counter, defaultdict

from discord.ext import tasks

from bot import bot
import re

wordle_channel_id = -1

async def init(wordle_channel):
    global wordle_channel_id
    wordle_channel_id = wordle_channel

async def get_quickest(puzzles):
    puzzle_results = []
    for puzzle in puzzles:
        guesses = await get_number_of_guesses(puzzle.get("puzzle"))
        puzzle_results.append({'guesses': guesses,'user': puzzle.get("user").name})

    # Find the fastest guess(es)
    guesses = [result["guesses"] for result in puzzle_results]
    guesses.sort()
    fastest = guesses[0]

    return [p for p in puzzle_results if p.get("guesses") == fastest]

async def get_most_volatile(puzzles):
    volatility_indices = []
    for puzzle in puzzles:
        volatility = await get_volatile_index(puzzle.get("puzzle"))
        volatility_indices.append({'volatility': volatility ,'user': puzzle.get("user").name})

    # Find the most volatile
    vol = [result["volatility"] for result in volatility_indices]
    vol.sort(reverse=True)
    most_volatile = vol[0]

    if most_volatile == 0:
        return None

    return [p for p in volatility_indices if p.get("volatility") == most_volatile]

async def get_most_helped(puzzles):
    help_indices = []
    for puzzle in puzzles:
        help_index = await get_help_index(puzzle.get("puzzle"))
        help_indices.append({'help': help_index , 'user': puzzle.get("user").name})

    # Find the most volatile
    hel = [result["help"] for result in help_indices]
    hel.sort(reverse=True)
    most_help = hel[0]

    if most_help == 0:
        return None

    return [p for p in help_indices if p.get("help") == most_help]


# Returns [0] if there is no extreme outliers (changes of <= -2 or >= 4)
async def get_volatile_index(puzzle):
    lines = await get_lines(puzzle)
    outliers = [0]
    for i in range(len(lines) - 1):
        line_1 = lines[i]
        line_2 = lines[i + 1]

        line_1_count = await count_yellow(line_1) + await count_green(line_1)
        line_2_count = await count_yellow(line_2) + await count_green(line_2)

        if line_2_count - line_1_count <= -2 or line_2_count - line_1_count >= 4:
            outliers.append(abs(line_2_count - line_1_count))

    return max(outliers)

async def get_help_index(puzzle):
    if await get_number_of_guesses(puzzle) == "X":
        return -1

    return await count_yellow(puzzle)


async def get_number_of_guesses(puzzle):
    x = re.search("([1-6]|[X])/6", puzzle)
    if x is None:
        return -1

    return puzzle[x.start():x.start()+1]


async def get_lines(puzzle):
    x = re.search("([🟩🟨⬛⬜]+\n*)+", puzzle)
    if x is None:
        return None

    return puzzle[x.start():x.end()].splitlines()


async def get_line(puzzle, line_number):
    return get_lines(puzzle)[line_number]


# Square Counters
async def count_green(line):
    return line.count("🟩")

async def count_yellow(line):
    return line.count("🟨")

async def count_blank(line):
    # Light mode uses white squares, dark mode uses black squares
    return max(line.count("⬛"), line.count("⬜"))


async def get_puzzle_number(puzzle):
    x = re.search("[0-9]+,[0-9]+", puzzle)
    if x is None:
        return "-1"

    return puzzle[x.start():x.end()]


async def get_yesterdays_puzzle_number():
    # First puzzle was June 20, 2021
    first_day = datetime.date(2021, 6,20)
    today_day = datetime.date.today()

    return (today_day - first_day).days.__str__()


async def is_from_yesterday(puzzle):
    yesterday = await get_yesterdays_puzzle_number()
    contender = (await get_puzzle_number(puzzle)).replace(',',"")

    return yesterday == contender

async def is_valid_puzzle(contender):
    square_count = await count_green(contender) + await count_yellow(contender) + await count_blank(contender)
    square_modulo = square_count % 5
    total_guesses = await get_number_of_guesses(contender)
    is_yesterday = await is_from_yesterday(contender)

    return square_count > 0 and square_modulo == 0 and total_guesses != -1 and is_yesterday


async def generate_daily_message(speed_dicts, volatility_dicts, help_dicts):
    message = f"**Results of Yesterday's Wordle ({int(await get_yesterdays_puzzle_number()):,d}):**"

    if speed_dicts is not None:
        for i in range(len(speed_dicts)):
            message += f"\n> Fastest{' ' + str(i+1)+'/'+str(len(speed_dicts)) if len(speed_dicts) > 1 else ''}: {speed_dicts[i]['user']} with {speed_dicts[i]['guesses']} guesses"

    if volatility_dicts is not None:
        for volatility_dict in volatility_dicts:
            message += f"\n> Most Volatile: {volatility_dict['user']}"

    if help_dicts is not None:
        for help_dict in help_dicts:
            message += f"\n> Required Most Help: {help_dict['user']} with {help_dict['help']} 🟨"

    return message


async def generate_monthly_message(stats):
    message = "**Monthly Wordle Recap:**"

    for key, value in stats.items():
        message += f"\n\n**{key.title().replace('_', ' ')}**"
        for sub_key, sub_value in value.items():
            message += f"\n> {sub_key}: {sub_value}"

    return message


async def collect_stats(results):
    fastest_names = re.findall("(?:(?<=Fastest \d/\d: )|(?<=Fastest: ))[a-z0-9_.]+", results)
    most_help_names = re.findall("(?:(?<=Required Most Help \d/\d: )|(?<=Required Most Help: ))[a-z0-9_.]+", results)
    most_volatile_names = re.findall("(?:(?<=Most Volatile \d/\d: )|(?<=Most Volatile: ))[a-z0-9_.]+", results)

    return {'fastest_names': fastest_names, 'most_help_names': most_help_names, 'most_volatile_names': most_volatile_names}


async def count_stats(stats):
    fastest_count = dict(zip(Counter(stats['fastest_names']).keys(), Counter(stats['fastest_names']).values()))
    help_count = dict(zip(Counter(stats['most_help_names']).keys(), Counter(stats['fastest_names']).values()))
    volatile_count = dict(zip(Counter(stats['most_volatile_names']).keys(), Counter(stats['fastest_names']).values()))

    return {'fastest_count': fastest_count, 'help_count': help_count, 'volatile_count': volatile_count}


async def summarize_month():
    yesterdays_date = datetime.datetime.now() - datetime.timedelta(days=1)
    num_days_last_month = calendar.monthrange(yesterdays_date.year, yesterdays_date.month)[1]

    # Get all the messages from the Wordle channel in the past month
    channel = bot.get_channel(wordle_channel_id)
    messages = await channel.history(after=datetime.datetime.now() - datetime.timedelta(days=num_days_last_month + 1)).flatten()

    # Has the form {'fastest_count': {'user1': ##, 'user2': ##}, 'help_count': {...}, 'volatile_count': {...}}
    user_stats = defaultdict(lambda: defaultdict(int))

    for message in messages:
        if message.author == bot.user and "Results of Yesterday's Wordle" in message.content:
            users = await collect_stats(message.content)
            # Count how many "fastest", "most help", etc. stats each user has on this message
            counted_stats = await count_stats(users)

            # Add the current message's stats to the totals
            for d in counted_stats.items():
                key, value = d
                for sub_key, sub_value in value.items():
                    user_stats[key][sub_key] += sub_value

    # Convert back to regular dict
    user_stats = {key: dict(sub_dict) for key, sub_dict in user_stats.items()}

    await channel.send(await generate_monthly_message(user_stats))

    return user_stats


# TODO: Convert local time to UTC
@tasks.loop(time=datetime.time(10,30,0), reconnect=True)
async def wordle_loop():
    await bot.wait_until_ready()

    # Get all the messages from the Wordle channel in the past two days
    channel = bot.get_channel(wordle_channel_id)
    messages = await channel.history(after=datetime.datetime.now() - datetime.timedelta(days=2)).flatten()

    puzzles = []

    for message in messages:
        if await is_valid_puzzle(message.content):
            puzzles.append({'user': message.author, 'puzzle': message.content})

    # Exit if no Wordle messages were submitted
    if len(puzzles) == 0:
        return

    fastest_solve = await get_quickest(puzzles)
    most_volatile = await get_most_volatile(puzzles)
    most_help = await get_most_helped(puzzles)

    output = await generate_daily_message(fastest_solve, most_volatile, most_help)
    await channel.send(output)

    if datetime.date.today().day == 1:
        user_stats = await summarize_month()
        monthly_output = await generate_monthly_message(user_stats)
        await channel.send(monthly_output)
