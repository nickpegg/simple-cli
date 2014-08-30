# Simple CLI

A CLI tool for interacting with your Simple bank account.

*Note:* This is still under early development. The way argument parsing is handled and the available commands are subject to change before the 0.1.0 release (though it shoudln't change too much!).

## Installation

`sudo pip install https://github.com/nickpegg/simple-cli/archive/master.zip`

## Usage

### Examples
```
# Get last 20 transactions
simple tail -n 20

# Get last 5 transactions and display any new ones as they appear in your account
simple tail -n5 -f

# Check the status of your goals
simple goals

# If you use a command-line password manager, such as password-store,
# you can use it to pass the password into simple-cli via standard input, like this:
pass show simple | simple -u yourusername -p goals
```

### Full Usage
```
Usage: simple [OPTIONS] COMMAND [ARGS]...

Options:
  -u TEXT                     Specify a username
  -p                          Read password from stdin
  -o [human|raw|pprint|json]  Output format
  --version                   Show the version and exit.
  -h                          Show this message and exit.
  --help                      Show this message and exit.

Commands:
  balances  Show your bank balances
  card      Show information about your card
  goals     Show your goals
  payments  Show your upcoming payments
  tail      Show your latest transactions
```

#### Goals
```
Usage: simple goals [OPTIONS]

  Show your goals

Options:
  --archived   Show archived goals
  --completed  Shop completed goals
  -h           Show this message and exit.
  --help       Show this message and exit.
```

#### Tail
```
Usage: simple tail [OPTIONS]

  Show your latest transactions

Options:
  -n INTEGER  Fetch these many transactions
  -f          Display transactions as they're made
  -h          Show this message and exit.
  --help      Show this message and exit.
```