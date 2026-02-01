import random
import re as regex
from discord import option

from bot import bot


class Roll:
    def __init__(self, num_of_rolls, operation, modifier, faces):
        self.num_of_rolls = num_of_rolls
        self.operation = operation
        self.modifier = modifier
        self.faces = faces


@bot.slash_command(name="roll", description="Roll a number of various sided dice")
@option(
    "modifier",
    description="How much to add/subtract from the total roll",
    required=False,
    default=0
)
async def roll(ctx, number_of_dice, number_of_faces, modifier):
    if int(modifier) == 0:
        roll_str = f"{number_of_dice}d{number_of_faces}"
    elif int(modifier) > 0:
        roll_str = f"{number_of_dice}d{number_of_faces} + {modifier}"
    else:
        roll_str = f"{number_of_dice}d{number_of_faces} - {abs(int(modifier))}"

    result = await roll_using_notation(roll_str)
    await ctx.respond(f"> {roll_str} = {str(result)}")


async def roll_using_notation(raw_roll):
    roll_obj = await prepare_roll(raw_roll.replace(" ", ""))
    modified_num = 0
    num = 0

    # Generate a random number using the max roll as many times as there are rolls. Add each roll together.
    if not roll_obj:
        return False

    for i in range(0, roll_obj.num_of_rolls):
        random_num = random.randint(1, roll_obj.faces)
        num += random_num

    # Add or subtract the modifier value from the random number, and set it to a new variable.
    if roll_obj.operation == '+':
        modified_num = num + roll_obj.modifier
    elif roll_obj.operation == '-':
        modified_num = num - roll_obj.modifier

    # send the message containing the roll info if there was a specified modifier. Otherwise, just respond the result.
    if roll_obj.modifier != 0:
        return modified_num

    return num


# Inputs a string in the format of a D&D roll (e.g. 2d20 + 2) and extracts the information and finally returns an object
# of type Roll that contains all the important information. In the case of invalid input, returns false.
async def prepare_roll(raw_roll):
    # Find where the 'd' in the message is to use as an anchor
    d_pos = raw_roll.find('d')

    # If the 'd' exists, and it's not the last character of the message
    if d_pos != -1 and len(raw_roll) > d_pos + 1:
        # Checking if there are multiple rolls by seeing if the first character is a digit or not
        if raw_roll[0].isdigit():
            num_of_rolls = int(regex.match('\\d+(?=d)', raw_roll)[0])
        elif raw_roll[0] == "d":
            num_of_rolls = 1
        else:
            return False
    else:
        return False

    # Finds the maximum number that comes before + or -
    faces = int(regex.findall('(?<=d)\\d+(?=$|\\D)', raw_roll)[0])

    matches = ['+', '-']

    if any(x in raw_roll for x in matches):
        # Finds the operation, either + or -
        operation = regex.findall('\\W', raw_roll)[0]
        # Finds the modifier that comes after + or -
        modifier = int(regex.findall('(?<=\\W)\\d+', raw_roll)[0])
    else:
        # Sets the operator and modifier to +0, as there was no specified modifier
        operation = "+"
        modifier = 0

    roll_obj = Roll(num_of_rolls, operation, modifier, faces)

    return roll_obj
