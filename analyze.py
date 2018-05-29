#!/usr/bin/python3
import sys
import numpy as np
from inspect import signature
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory

data = {} # key: header, value: array of all values
passed_data = {}
failed_data = {}

def parse_files(filenames):
    headers = []
    for filename in filenames:
        with open(filename, 'r') as f:
            headers = f.readline()
            headers = headers[:-1]
            headers = headers.split(',')
            for header in headers:
                data[header] = []
                passed_data[header] = []
                failed_data[header] = []

            for line in f.readlines():
                line = line[:-1]
                line_values = line.split(',')
                i = 0
                for header in headers:
                    value = convert_if_possible(line_values[i])
                    i += 1
                    data[header].append(value)
                    if line_values[0] == 'failed':
                        failed_data[header].append(value)
                    elif line_values[0] == 'passed':
                        passed_data[header].append(value)

    return data, passed_data, failed_data

def execute_command(raw_string):
    split_string = raw_string.split(' ')
    command = split_string[0]
    args = split_string[1:]

    if command not in commands:
        print('Invalid command:', command)
        return False

    desired_fn = commands[command]
    if len(signature(desired_fn).parameters) != len(args):
        print('Invalid args:', args)
        print('Expected', len(signature(desired_fn).parameters), 'arguments')
        return False

    if len(args) == 0:
        commands[command]()
    else:
        commands[command](args)

    return True

def build_completer():
    return WordCompleter(list(commands.keys()))

def enter_prompt():
    completer = build_completer()
    history = InMemoryHistory()
    session = PromptSession(
        history=history,
        completer=completer,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=True)

    data, passed_data, failed_data = parse_files(sys.argv[1:])
    while True:
        try:
            execute_command(session.prompt('> '))
        except KeyboardInterrupt:
            pass #Ctrl-C pressed

def main():
    enter_prompt()

def print_averages_and_stuff(args=None):
    to_print = data
    key_wanted = None
    if args:
        if args[0] == "passed":
            to_print = passed_data
        elif args[0] == "failed":
            to_print = failed_data
    for key in to_print:
        if isinstance(to_print[key][0], float) :
            print(key, ':', np.mean(to_print[key]))

def show_help():
    """ Shows help info """
    print('Available commands:')
    for key in commands:
        print(key, commands[key].__doc__ or '')

def exit():
    sys.exit(0)

def convert_if_possible(string_value):
    try:
        return float(string_value)
    except:
        return string_value

commands = {
    'mean': print_averages_and_stuff,
    'exit': exit,
    'help': show_help,
}

if __name__ == "__main__":
    main()
