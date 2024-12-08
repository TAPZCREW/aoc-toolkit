from argparse import ArgumentParser

import logging
import logging.config

from anyio import run
from dotenv import load_dotenv

import yaml

from .commands import fetch_command
from .commands import run_command


logger = logging.getLogger(__name__)


def setup_logging():
    with open("logging.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file.read())

    logging.config.dictConfig(config)
    logging.captureWarnings(True)


async def main():
    setup_logging()

    load_dotenv()

    parser = ArgumentParser(prog="aoc-toolkit")

    subparsers = parser.add_subparsers(help="subcommands", required=True)

    parser_fetch = subparsers.add_parser(
        "fetch", help="fetch days and save them locally", aliases=["f"]
    )
    parser_fetch.add_argument("-l", "--latest", help="latest", action="store_true")
    parser_fetch.add_argument("-y", "--year", help="year", type=int)
    parser_fetch.add_argument("-d", "--day", help="day", type=int)
    parser_fetch.set_defaults(func=fetch_command)

    parser_run = subparsers.add_parser("run", help="run day script", aliases=["r"])
    parser_run.add_argument("-y", "--year", help="year", type=int)
    parser_run.add_argument("-d", "--day", help="day", type=int)
    parser_run.add_argument(
        "-s", "--submit", help="submit answers", action="store_true"
    )
    parser_run.set_defaults(func=run_command)

    args = parser.parse_args()
    await args.func(args)


if __name__ == "__main__":
    run(main)
