from logging import getLogger
from os import makedirs
from os.path import isfile, dirname, join
from shutil import copyfile
from typing import Optional

import sys

from anyio import open_file

from ..services.aoc_service import AocService, Day


logger = getLogger(__name__)

_service = AocService()  # TODO : use dependency injection


async def save_day(day: Day):
    makedirs(day.directory, exist_ok=True)

    if not isfile(day.script_filename):
        module_path = dirname(sys.modules["__main__"].__file__)
        stub_filepath = join(module_path, "_data/script.py.stub")
        if not isfile(stub_filepath):
            logger.warning("Unable to find script stub %s", stub_filepath)
        else:
            copyfile(stub_filepath, day.script_filename)

            logger.debug("Saved script file %s", day.script_filename)

    # if you saved a day before completing part 1, description
    # won't be up to date, so we update it every time
    async with await open_file(day.description_filename, "w") as f:
        await f.write(day.description)

    logger.debug("Saved description file %s", day.description_filename)

    # input *should* never change
    if not isfile(day.input_filename):
        async with await open_file(day.input_filename, "w") as f:
            await f.write(day.input)  # TODO : lazy-loading

        logger.debug("Saved input file %s", day.input_filename)

    logger.info("Saved day %s of year %s", day.day, day.year)


async def _fetch_day(year: int, day: int):
    day = await _service.get_day(year, day)
    await save_day(day)


async def _fetch_event(year: int):
    event = await _service.get_event(year)
    for day in event.available_days:
        if day.locked:
            continue

        await _fetch_day(day.year, day.day)

    logger.info("Fetched all events of year %s", day.year)


async def _fetch_all(year: Optional[int]):
    if year is not None:
        return await _fetch_event(year)

    async for event in _service.get_events():
        await _fetch_event(event.year)


async def _fetch_latest_day(year: Optional[int]):
    event = await _service.get_event(year)
    latest_day = event.latest_day

    await _fetch_day(latest_day.year, latest_day.day)

    logger.info("Fetched latest day of year %s", latest_day.year)


async def _fetch_latest(year: Optional[int]):
    if year is not None:
        return await _fetch_latest_day(year)

    latest_event = await anext(_service.get_events(), None)
    return await _fetch_latest_day(latest_event.year)


async def fetch(args):
    if args.latest:
        return await _fetch_latest(args.year)

    if args.day is not None:
        if args.year is None:
            logger.error("Year is required to fetch a given day")
            return

        return await _fetch_day(args.year, args.day)

    return await _fetch_all(args.year)
