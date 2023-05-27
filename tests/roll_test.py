import pytest
import roll

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
async def test_roll_no_modifier():
    assert (1 <= await roll.roll_using_notation("d10") <= 10)
    assert (2 <= await roll.roll_using_notation("2d4") <= 8)


@pytest.mark.asyncio
async def test_roll_with_modifier():
    assert (6 <= await roll.roll_using_notation("2d4+4") <= 12)
    assert (1 <= await roll.roll_using_notation("2d4-1") <= 7)


@pytest.mark.asyncio
async def test_invalid_roll():
    assert await roll.roll_using_notation("2") is False
    assert await roll.roll_using_notation("2+1") is False
    assert await roll.roll_using_notation("2d") is False
    assert await roll.roll_using_notation("d") is False


@pytest.mark.asyncio
async def test_roll_object():
    roll_object = await roll.prepare_roll("5d7")
    assert roll_object.num_of_rolls == 5
    assert roll_object.faces == 7
    assert roll_object.modifier == 0

    roll_object_2 = await roll.prepare_roll("10d3+4")
    assert roll_object_2.num_of_rolls == 10
    assert roll_object_2.faces == 3
    assert roll_object_2.modifier == 4
