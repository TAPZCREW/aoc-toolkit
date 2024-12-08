# Advent of Code Toolkit

`aoc-toolkit` is an Advent of Code toolkit to get, run and submit problems

## CLI

This tool is mainly designed to be used as a CLI.

```
usage: aoc-toolkit [-h] {fetch,f,run,r} ...

positional arguments:
  {fetch,f,run,r}  subcommands
    fetch (f)      fetch days and save them locally
    run (r)        run day script

options:
  -h, --help       show this help message and exit
```

### fetch

Fetch problems and save them locally.

`fetch` will send a request to Advent of Code and extract problems description and input. It will 3 create files :

- `description.md` will contains the problem description in Markdown format.
- `input.txt` will contains your problem input in text format.
- `script.py` is a boilerplate to run script with `run` command (see [below](#run)).

```
usage: aoc-toolkit fetch [-h] [-l] [-d DAY] [-y YEAR]

options:
  -h, --help            show this help message and exit
  -l, --latest          latest
  -d DAY, --day DAY     day
  -y YEAR, --year YEAR  year
```

#### Fetch all days of all years

```
$ aoc-toolkit fetch
$ aoc-toolkit f
```

#### Fetch all days of a given year

```
$ aoc-toolkit fetch --year 2016
$ aoc-toolkit f -y 2016
```

#### Fetch a day of a given year

```
$ aoc-toolkit fetch --year 2016 --day 7
$ aoc-toolkit f -y 2016 --day 7
```

#### Fetch latest day of latest year

```
$ aoc-toolkit fetch --latest
$ aoc-toolkit f -l
```

#### Fetch latest day of a given year

```
$ aoc-toolkit fetch --latest --year 2016
$ aoc-toolkit f -l -y 2016
```

### run

Run a day script.

> Note : Be sure to `fetch` before trying to run a script.

> Note : `run` does not make requests to Advent of Code (except for [submitting answers](#submitting-answers)). It navigates the filesystem and finds available scripts. Anything with "latest" wording will try to find the latest script in the filesystem.


```
usage: aoc-toolkit run [-h] [-l] [-y YEAR] [-d DAY] [-s]

options:
  -h, --help            show this help message and exit
  -y YEAR, --year YEAR  year
  -d DAY, --day DAY     day
  -s, --submit          submit answers
```


#### Run latest day of latest year

```
$ aoc-toolkit run
$ aoc-toolkit r
```

#### Run latest day of a given year

```
$ aoc-toolkit run --year 2016
$ aoc-toolkit r -y 2016
```

#### Run a day of a given year

```
$ aoc-toolkit run --year 2016 --day 7
$ aoc-toolkit r -y 2016 -d 7
```

#### Submitting answers

```
$ aoc-toolkit run --submit
$ aoc-toolkit run --year 2016 --submit
$ aoc-toolkit run --year 2016 --day 7 --submit
$ aoc-toolkit r -s
$ aoc-toolkit r -y 2016 -s
$ aoc-toolkit r -y 2016 -d 7 -s
```

## Running scripts

Running scripts is as simple as running a command :

```
$ aoc-toolkit r -y 2015 -d 17
```

A script must be composed of three functions :
- `parse_input` that is responsible for parsing the problem input.
- `solve_part_1` and `solve_part_2` that are responsible for solving the problem by returning the answer.

The two `solve_part_` functions take a single argument, `_input` that is the data returned by the `parse_input` function (type-hinting is recommended). They must return an optional string or integer representing the answer.

Here is an example for day 17 of 2015 (`events/2015/17/script.py`) :

```python
from itertools import combinations
from typing import List, Optional


# Year    : 2015
# Day     : 17
# Problem : No Such Thing as Too Much


EGGNOG_VOLUME = 150


def parse_input(_input: str) -> List[int]:
    return [int(line) for line in _input.splitlines()]


def solve_part_1(containers: List[int]) -> Optional[str | int]:
    result = 0

    for i in range(1, len(containers)):
        result += sum(
            1 for _ in combinations(containers, r=i) if sum(_) == EGGNOG_VOLUME
        )

    return result


def solve_part_2(containers: List[int]) -> Optional[str | int]:
    pass
```

## Submitting answers

```
$ aoc-toolkit r -y 2016 -d 7 -s
```

When using answer submission (`--submit`), `aoc-toolkit` will check if any of the two `solve_part_*` functions return a string or an integer and submit it. If a function returns `None`, answer will be ignored and not submitted.

> Note : Only one answer will be submitted at a time. Part 1 answer will only be submitted if `solve_part_2` returned `None`.
