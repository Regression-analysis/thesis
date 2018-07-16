from numpy import std, mean
import math
import csv
import sys


def parse_file(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        iterator = iter(reader)
        headers = next(iterator)
        values = [ [] for h in headers ]
        while True:
            try:
                row = next(iterator)
                for index, value in enumerate(row):
                    if index is 0:
                        values[index].append(value)
                    else:
                        values[index].append(None if value is '' else int(value))
            except StopIteration:
                break

        return headers, values


def calc_std_devs(headers, values):
    std_devs = []
    for index, header in enumerate(headers):
        if header == 'commitsha':
            std_devs.append(None)
        else:
            std_devs.append(std([v for v in values[index] if v is not None]))

    # Turn all to integers
    std_devs = [int(s) if s is not None else s for s in std_devs]

    return std_devs


def significant_change(v, w, std_dev):
    return math.fabs(v - w) > std_dev

def find_significant_changes(headers, values, std_devs):
    significant_changes = []
    for index, header in enumerate(headers):
        if header == 'commitsha':
            significant_changes.append(None)
            continue

        significant_changes.append([])
        i = -1
        for v, w in zip(values[index], values[index][1:]):
            i += 1
            if v is None or w is None:
                continue

            if significant_change(v, w, std_devs[index]):
                significant_changes[index].append((values[0][i], values[0][i+1]))

    return significant_changes


def main():
    headers, values = parse_file(sys.argv[1])
    std_devs = calc_std_devs(headers, values)
    significant_changes = find_significant_changes(headers, values, std_devs)
    for index, change_list in enumerate(significant_changes):
        if change_list is None:
            continue
        print(headers[index], change_list[0], std_devs[index])

if __name__ == '__main__':
    main()
