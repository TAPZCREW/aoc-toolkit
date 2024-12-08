from dataclasses import dataclass, field
from os import getenv
from typing import Any, List, Optional, AsyncGenerator, Generator

import logging
import os.path
import re

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md

import httpx


logger = logging.getLogger(__name__)


@dataclass
class Day:
    year: int
    day: int
    stars: Optional[int] = field(default_factory=int)
    description: Optional[str] = field(default_factory=str)
    input: Optional[str] = field(default_factory=str)  # TODO : lazy-loading
    locked: bool = field(default=False)

    @property
    def directory(self) -> str:
        return os.path.join("events", str(self.year), str(self.day))

    @property
    def script_filename(self) -> str:
        return os.path.join(self.directory, "script.py")

    @property
    def input_filename(self) -> str:
        return os.path.join(self.directory, "input.txt")

    @property
    def description_filename(self) -> str:
        return os.path.join(self.directory, "description.md")

    @property
    def url(self):
        return f"/{self.year}/day/{self.day}"


@dataclass
class Event:
    year: int
    days: List[Day] = field(default_factory=list)
    stars: Optional[int] = field(default_factory=int)

    @property
    def url(self):
        return f"/{self.year}"

    @property
    def available_days(self):
        return (day for day in self.days if not day.locked)

    @property
    def latest_day(self):
        return next(day for day in reversed(self.days) if not day.locked)


def _parse_day_stars(main: Tag) -> int:
    if main.find("form") is None:
        return 2

    if main.find("p", "day-success") is not None:
        return 1

    return 0


def _html_to_markdown(element: Tag) -> str:
    return md(str(element), heading_style="ATX").strip()


def _parse_day_description(main: Tag, day: int) -> str:
    sections = main.select("article.day-desc, article.day-desc + p")
    description = "\n\n".join(_html_to_markdown(section) for section in sections)

    # fix input href
    description = description.replace(f"({day}/input)", "(input.txt)")

    # fix tasks link href
    description = re.sub(
        r"\(\/(\d*)\/day\/(\d*)\)", r"(/events/\1/\2/description.md)", description
    )

    return description


def _parse_event_days(soup: BeautifulSoup, year: int) -> Generator[Day, Any, None]:
    _days = soup.select("pre.calendar > a, pre.calendar > span")

    # calendar might not only contains day elements
    _days = (
        day
        for day in _days
        if any(_class.startswith("calendar-day") for _class in day.attrs["class"])
    )

    # days are not always in ascending order (like in year 2023 or 2020)
    _days = sorted(
        _days, key=lambda day: int(day.find("span", "calendar-day").string.strip())
    )

    for day in _days:
        _day = int(day.find("span", "calendar-day").string.strip())
        locked = day.name == "span"

        stars = 0
        if not locked:
            if "calendar-complete" in day.attrs["class"]:
                stars = 1
            elif "calendar-verycomplete" in day.attrs["class"]:
                stars = 2

        yield Day(year=year, day=_day, stars=stars, locked=locked)


class AocService:
    def __init__(self, session_id: Optional[str] = None):
        # TODO : use dependency injection to get `AOC_SESSION_ID`
        session_id = session_id or getenv("AOC_SESSION_ID")

        self.client = lambda: httpx.AsyncClient(
            base_url="https://adventofcode.com", cookies={"session": session_id}
        )

    async def get_events(self) -> AsyncGenerator[Event, None]:
        async with self.client() as client:
            r = await client.get("/events")
            if r.status_code != httpx.codes.OK:
                logger.warning("Cannot get events")
                return

            soup = BeautifulSoup(r.text, "lxml")

        for event in soup.find_all("div", "eventlist-event"):
            link = event.find("a")
            year = int(link.string.strip("[]"))

            stars = event.find("span", "star-count")
            if stars is None:
                stars = 0
            else:
                stars = int(stars.string.strip("*"))

            yield Event(year=year, stars=stars)

    async def get_event(self, year: int) -> Optional[Event]:
        async with self.client() as client:
            r = await client.get(f"/{year}")
            if r.status_code != httpx.codes.OK:
                logger.warning("Cannot get event for /%s", year)
                return

            soup = BeautifulSoup(r.text, "lxml")

        days = list(_parse_event_days(soup, year))
        stars = sum(day.stars for day in days)

        return Event(year=year, days=days, stars=stars)

    async def get_day(self, year: int, day: int) -> Optional[Day]:
        async with self.client() as client:
            r = await client.get(f"/{year}/day/{day}")
            if r.status_code != httpx.codes.OK:
                logger.warning("Cannot get day for /%s/day/%s", year, day)
                return

            soup = BeautifulSoup(r.text, "lxml")

        main = soup.find("main")

        stars = _parse_day_stars(main)
        description = _parse_day_description(main, day)
        _input = await self.get_day_input(year, day)  # TODO : lazy-loading

        return Day(
            day=day, year=year, stars=stars, description=description, input=_input
        )

    async def get_day_input(self, year: int, day: int) -> Optional[str]:
        async with self.client() as client:
            r = await client.get(f"/{year}/day/{day}/input")
            if r.status_code != httpx.codes.OK:
                logger.warning("Cannot get input for /%s/day/%s", year, day)
                return

            return r.text

    async def submit_answer(
        self, year: int, day: int, answer: str | int, level: int = 1
    ) -> bool:
        if isinstance(answer, str):
            if len(answer) == 0:
                logger.warning("String answer must be non-empty")
                return False

        data = {
            "level": level,
            "answer": answer,
        }

        async with self.client() as client:
            r = await client.post(f"/{year}/day/{day}/answer", data=data)
            if r.status_code != httpx.codes.OK:
                logger.warning(
                    "Cannot submit answer /%s/day/%s/answer", year, day, level
                )
                return False

            soup = BeautifulSoup(r.text, "lxml")

        message = soup.select_one("main > article > p").text

        # should never happen
        if (
            "You need to actually provide an answer before you hit the button."
            in message
        ):
            logger.warning("Empty answer")
            return False

        # already submitted
        if "Did you already complete it?" in message:
            logger.warning("Already solved")
            return False

        # wrong answer
        if "That's not the right answer" in message:
            logger.warning("Invalid answer")

            # TODO : sometimes you can have tips like "answer too low"
            logger.warning("%s", message)

            return False

        # cooldown
        if "You gave an answer too recently" in message:
            [cooldown] = re.findall(r"You have (\d*)s left to wait", message)

            logger.warning("Submission is in cooldown (%ss)", cooldown)
            return False

        # TODO : success

        logger.info("Submit message: %s", repr(message))

        return True
