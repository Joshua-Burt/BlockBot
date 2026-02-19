import calendar
import datetime
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
import requests
from discord.ext import tasks

from bot import bot

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
        volatility_indices.append({'volatility': volatility,'user': puzzle.get("user").name})

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
        help_indices.append({'help': help_index, 'user': puzzle.get("user").name})

    # Find the most volatile
    hel = [result["help"] for result in help_indices]
    hel.sort(reverse=True)
    most_help = hel[0]

    if most_help == 0:
        return None

    return [p for p in help_indices if p.get("help") == most_help]


async def get_oneshots(puzzles):
    oneshot_list = []
    for puzzle in puzzles:
        if await get_number_of_guesses(puzzle.get("puzzle")) != "1":
            continue
            
        oneshot_list.append({'user': puzzle.get("user").name})
    
    return oneshot_list
      


async def get_streaks(daily_messages, playing_users):
    streak_holders_dicts = []
    
    # Only check if there are multi-day streaks if there was a previous daily message from the bot
    if len(daily_messages) > 0:
        daily_message = daily_messages.pop()
        lines_with_days = re.findall(".*[0-9]+ day", daily_message)
        
        # Collect the users who had a streak yesterday
        for line in lines_with_days:
            name = re.search("(?<=> ).*(?=:)", line)
            days = re.search("(?<=: )[0-9]+(?= day)", line)
            
            # Skip this loop when there is no streaks already existing
            if name is None or days is None:
                continue
            
            # Skip this loop if the user didn't play yesterday
            if line[name.start():name.end()] not in playing_users:
                continue
            
            streak_holders_dicts.append(
                {"user": line[name.start():name.end()], "days": int(line[days.start():days.end()]) + 1})
    
    # Add new 1-day streak holders
    for username in list(set(playing_users) - set(streak_dict['user'] for streak_dict in streak_holders_dicts)):
        streak_holders_dicts.append({"user": username, "days": 1})
    
    return streak_holders_dicts

# Returns [0] if there is no extreme outliers (changes of <= -2 or >= 4)
async def get_volatile_index(puzzle):
    lines = await get_lines(puzzle)
    
    if lines is None:
        return [0]
    
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
    return await count_yellow(puzzle)


async def get_number_of_guesses(puzzle) -> str or None:
    x = re.search("([1-6]|X)/6", puzzle)
    if x is None:
        return None

    return puzzle[x.start():x.start()+1]


async def get_lines(puzzle) -> list or None:
    x = re.search("([🟩🟨⬛⬜]+\n*)+", puzzle)
    
    if x is None:
        return None

    return puzzle[x.start():x.end()].splitlines()


async def get_line(puzzle, line_number) -> list or None:
    lines = await get_lines(puzzle)
    
    if lines is None:
        return None
    
    return lines[line_number]


async def count_lines(puzzle) -> int or None:
    lines = await get_lines(puzzle)
    
    if lines is None:
        return None
    
    return len(lines)

# Square Counters
async def count_green(line) -> int:
    return line.count("🟩")

async def count_yellow(line) -> int:
    return line.count("🟨")

async def count_blank(line) -> int:
    # Light mode uses white squares, dark mode uses black squares
    return max(line.count("⬛"), line.count("⬜"))


async def get_puzzle_number(puzzle):
    x = re.search("[0-9]+,[0-9]+", puzzle)
    if x is None:
        return "-1"

    return puzzle[x.start():x.end()]


async def get_yesterdays_puzzle_number():
    # First puzzle was June 20, 2021
    first_day = date(2021, 6, 20)
    today_day = date.today()

    return (today_day - first_day).days.__str__()


async def is_from_yesterday(puzzle):
    yesterday = await get_yesterdays_puzzle_number()
    contender = (await get_puzzle_number(puzzle)).replace(',',"")

    return yesterday == contender


async def get_yesterdays_answer():
    yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
    url = f"https://www.nytimes.com/svc/wordle/v2/{yesterday}.json"
    
    # Requires setting Referer to bypass some security measures
    headers = {'Referer': 'https://www.nytimes.com/games/wordle/index.html'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return str(response.json()['solution']).upper()
    else:
        return None

async def is_valid_puzzle(contender):
    square_count = await count_green(contender) + await count_yellow(contender) + await count_blank(contender)
    total_guesses = await get_number_of_guesses(contender)
    line_count = await count_lines(contender)
    is_yesterday = await is_from_yesterday(contender)
    
    # Either #/6 or 🟩🟨⬛⬜ is missing from the contender
    if total_guesses is None or line_count is None:
        return False

    return (square_count > 0
            and square_count % 5 == 0
            and (total_guesses == "X" or total_guesses == str(line_count))
            and is_yesterday)


async def generate_daily_message(speed_dicts, volatility_dicts, help_dicts, oneshot_dicts, streak_dicts):
    message = f"**Results of Yesterday's Wordle ({int(await get_yesterdays_puzzle_number()):,d}):**"
    
    yesterdays_answer = await get_yesterdays_answer()
    if yesterdays_answer is not None:
        message += "\nYesterday's word was **" + yesterdays_answer + "**"

    if speed_dicts is not None:
        for i in range(len(speed_dicts)):
            message += f"\n> Fastest{' ' + str(i+1)+'/'+str(len(speed_dicts)) if len(speed_dicts) > 1 else ''}: {speed_dicts[i]['user']} with {speed_dicts[i]['guesses']} guesses"

    if volatility_dicts is not None:
        for i in range(len(volatility_dicts)):
            message += f"\n> Most Volatile{' ' + str(i + 1) + '/' + str(len(volatility_dicts)) if len(volatility_dicts) > 1 else ''}: {volatility_dicts[i]['user']}"

    if help_dicts is not None:
        for i in range(len(help_dicts)):
            message += f"\n> Required Most Help{' ' + str(i + 1) + '/' + str(len(help_dicts)) if len(help_dicts) > 1 else ''}: {help_dicts[i]['user']} with {help_dicts[i]['help']} 🟨"

    if oneshot_dicts is not None:
        for i in range(len(oneshot_dicts)):
            message += f"\n> One-Shot{' ' + str(i + 1) + '/' + str(len(oneshot_dicts)) if len(oneshot_dicts) > 1 else ''}: {oneshot_dicts[i]['user']}"

    if streak_dicts is not None and len(streak_dicts) > 0:
        message += "\n\n**Streaks:**"
        for streak_dict in sorted(streak_dicts, key=lambda x: x['days'], reverse=True):
            message += f"\n> { streak_dict['user'] }: { streak_dict['days'] } {'days' if streak_dict['days'] > 1 else 'day'}"

    return message


async def generate_monthly_message(stats):
    message = "**Monthly Wordle Recap:**"

    for key, value in stats.items():
        message += f"\n\n**{key.title().replace('_', ' ')}**"
        
        for sub_key, sub_value in sorted(value.items(), key=lambda x: int(x[1]), reverse=True):
            message += f"\n> {sub_key}: {sub_value}"

    return message


async def collect_stats(results):
    fastest_names = re.findall("(?:(?<=Fastest \\d/\\d: )|(?<=Fastest: ))[a-z0-9_.]+", results)
    most_help_names = re.findall("(?:(?<=Required Most Help \\d/\\d: )|(?<=Required Most Help: ))[a-z0-9_.]+", results)
    most_volatile_names = re.findall("(?:(?<=Most Volatile \\d/\\d: )|(?<=Most Volatile: ))[a-z0-9_.]+", results)
    oneshot_names = re.findall("(?:(?<=One-Shot \\d/\\d: )|(?<=One-Shot: ))[a-z0-9_.]+", results)

    return {'fastest_names': fastest_names, 'most_help_names': most_help_names, 'most_volatile_names': most_volatile_names, 'oneshot_names': oneshot_names}


async def count_stats(stats):
    fastest_count = dict(zip(Counter(stats['fastest_names']).keys(), Counter(stats['fastest_names']).values()))
    help_count = dict(zip(Counter(stats['most_help_names']).keys(), Counter(stats['most_help_names']).values()))
    volatile_count = dict(zip(Counter(stats['most_volatile_names']).keys(), Counter(stats['most_volatile_names']).values()))
    oneshot_count = dict(zip(Counter(stats['oneshot_names']).keys(), Counter(stats['oneshot_names']).values()))

    return {'fastest_count': fastest_count, 'help_count': help_count, 'volatile_count': volatile_count, 'oneshot_count': oneshot_count}


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

    return user_stats


@tasks.loop(time=datetime.time(7, 30, 0, tzinfo=datetime.datetime.now().astimezone().tzinfo), reconnect=True)
async def wordle_loop():
    await bot.wait_until_ready()

    # Collect all the messages from the Wordle channel in the past two days
    channel = bot.get_channel(wordle_channel_id)
    messages = await channel.history(after=datetime.datetime.now() - datetime.timedelta(days=2)).flatten()

    puzzles = []
    bot_messages = []
    
    # Collect all yesterday's puzzles and bot messages
    for message in messages:
        if await is_valid_puzzle(message.content):
            puzzles.append({'user': message.author, 'puzzle': message.content})
        elif message.author == bot.user and "Results of Yesterday's Wordle" in message.content:
            bot_messages.append(message.content)

    # Exit if no Wordle messages were submitted
    if len(puzzles) == 0:
        return

    fastest_solve = await get_quickest(puzzles)
    most_volatile = await get_most_volatile(puzzles)
    most_help = await get_most_helped(puzzles)
    oneshots = await get_oneshots(puzzles)
    
    # Pass in the names of the users that participated in yesterday's wordle
    streaks = await get_streaks(bot_messages, list(set([puzzle['user'].name for puzzle in puzzles])))

    output = await generate_daily_message(fastest_solve, most_volatile, most_help, oneshots, streaks)
    await channel.send(output)

    # Generate a summary of the previous month if it's the 1st of the month
    if datetime.date.today().day == 1:
        user_stats = await summarize_month()
        monthly_output = await generate_monthly_message(user_stats)
        await channel.send(monthly_output)
