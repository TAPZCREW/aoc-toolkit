from os import walk
from os.path import isdir, isfile
from typing import Tuple, Optional
from logging import getLogger

from anyio import open_file

from ..services.aoc_service import AocService, Day


logger = getLogger(__name__)

_service = AocService()  # TODO : use dependency injection


def _get_latest_local_day(year: Optional[int]) -> Optional[Day]:
    if not isdir("events/"):
        logger.error('Directory "events/" not found')
        return

    if year is None:
        (_, years, _) = next(walk("events/"))
        year = max(years, key=int, default=None)

    if year is None:
        logger.error('Directory "events/" is empty')
        return

    if not isdir(f"events/{year}"):
        logger.error('Directory "events/%s" not found', year)
        return

    (_, days, _) = next(walk(f"events/{year}"))
    day = max(days, key=int, default=None)

    if day is None:
        logger.error("No day available for year %s", year)
        return

    return Day(year, day)


async def _run_day(
    year: int, day: int
) -> Optional[Tuple[Optional[str], Optional[str]]]:
    _day = Day(year, day)

    if not isfile(_day.script_filename):
        logger.warning("%s does not exist", _day.script_filename)
        return

    async with await open_file(_day.script_filename) as f:
        script = await f.read()

    logger.info("Running script %s", _day.script_filename)

    _globals = globals()
    _locals = globals()
    exec(script, _globals, _locals)

    if not all(
        func in _locals for func in ["parse_input", "solve_part_1", "solve_part_2"]
    ):
        logger.warning(
            'Script must implements "parse_input", "solve_part_1" and "solve_part_2" functions'
        )
        return

    _parse_input = _locals["parse_input"]
    _solve_part_1 = _locals["solve_part_1"]
    _solve_part_2 = _locals["solve_part_2"]

    async with await open_file(_day.input_filename) as f:
        _input = _parse_input(await f.read())

    answer_1 = _solve_part_1(_input)
    answer_2 = _solve_part_2(_input)

    return (answer_1, answer_2)


async def _submit_answer(day: Day, answer: str | int, level: int) -> bool:
    # we don't show the answer as it can be quite long sometimes
    logger.info(
        "Submitting answer for year %s, day %s, level %s...", day.year, day.day, level
    )

    if not isinstance(answer, str) or not isinstance(answer, int):
        logger.warning("Answers must be a string or an integer")
        return False

    submitted = await _service.submit_answer(day.year, day.day, answer, level)
    if not submitted:
        logger.warning("Failed to submit answer")
        return False

    logger.info("Answer accepted!")

    return True


async def run(args):
    if args.day is None:
        day = _get_latest_local_day(args.year)
    else:
        day = Day(args.year, args.day)

    if day is None:
        logger.error("No day available to run, run fetch first")
        return

    _run = await _run_day(day.year, day.day)
    if _run is None:
        logger.error("Unable to run script for year %s, day %s", day.year, day.day)
        return

    (answer_1, answer_2) = _run

    logger.info("Answer 1 : %s", str(answer_1)[:80])
    logger.info("Answer 2 : %s", str(answer_2)[:80])

    if not args.submit:
        return

    if answer_1 is None and answer_2 is None:
        logger.error("No answer detected")
        return

    if answer_2 is not None:
        await _submit_answer(day, answer_2, 2)
        return

    await _submit_answer(day, answer_1, 1)
