# Simple CLI

A CLI tool for interacting with your Simple bank account.

## Installation

`sudo pip install https://github.com/nickpegg/simple-cli/archive/master.zip`

## Usage
```
Usage:
    simple [options] tail [-n <num>] [-f]
    simple [options] goals [--archived] [--completed]
    simple (-h | --help)
    simple --version

Options:
    -u <username>   Specify a Simple username to use
    -p              Supply a password via stdin
    -o [format]     Use <format> to output data [default: human]

Commands:
    tail            Display a number of your latest transactions
    goals           Display your goals

Tail Options:
    -n <num>        Get the <num> latest transactions [default: 10]
    -f              Display transactions as they're made, similar to the `tail -f` command

Goals Options:
    --archived      Show archived goals
    --completed     Show completed goals

Formats:
    human   Human-friendly output of the most important parts of the data
    raw     Raw output of the data
    pprint  Pretty-printed output of the data
    json    JSON dump of the data
```
