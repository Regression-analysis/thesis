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


def calc_std_devs(aggregated_tests):
    std_devs = {}
    for test_name in aggregated_tests:
        test_times = aggregated_tests[test_name]

        if test_name == 'commitsha':
            std_devs[test_name] = None
        else:
            # calc std dev. we must remove all null values first
            s = std([t for t in test_times if t is not None])
            # convert it to an integer value
            std_devs[test_name] = int(s)

    return std_devs


def significant_change(v, w, std_dev):
    return math.fabs(v - w) > std_dev*2 and v < w

def find_significant_changes(aggregated_tests, std_devs, commit_shas):
    significant_changes = {}
    for test_name in aggregated_tests:
        test_times = aggregated_tests[test_name]
        change_list = []

        i = -1
        for t1, t2 in zip(test_times, test_times[1:]):
            i += 1
            if t1 is None or t2 is None:
                continue # skip if we have no value for this test

            if significant_change(t1, t2, std_devs[test_name]):
                change_list.append((commit_shas[i], commit_shas[i+1]))

        significant_changes[test_name] = change_list

    return significant_changes

def print_info(headers, values, std_devs, significant_changes):
    print("There are", len(headers) - 1, "tests total")
    print("run on", len(values[0]), "different commits")
    for index, change_list in enumerate(significant_changes):
        if change_list is None:
            continue
        print(headers[index], len(change_list), std_devs[index])

    regressed_commits = set()
    for change_list in significant_changes:
        for c1, c2 in change_list or []:
            regressed_commits.add(c1)

    print("There are a total of",
            len(regressed_commits),
            "commits that have at least one test regressing")


def aggregate_subtests(headers, values):
    aggregated_tests = {} # add up the subtest times
    for index, header in enumerate(headers):
        if header == "commitsha":
            continue

        base_name = header.split('.')[0]
        if base_name not in aggregated_tests:
            aggregated_tests[base_name] = []
            for v in values[index]:
                aggregated_tests[base_name].append(v)
        else:
            for i in range(0, len(values[index])):
                v1 = aggregated_tests[base_name][i]
                v2 = values[index][i]
                if v1 is None and v2 is None:
                    aggregated_tests[base_name][i] = None
                elif v1 is None:
                    aggregated_tests[base_name][i] = v2
                elif v2 is None:
                    aggregated_tests[base_name][i] = v1
                else:
                    aggregated_tests[base_name][i] = v1 + v2

    return aggregated_tests

def main():
    # Parse csv file
    headers, values = parse_file(sys.argv[1])
    commit_shas = values[0]
    # Aggregate subtests into their total test execution times
    aggregated_tests = aggregate_subtests(headers, values)
    # Calculate std deviation for each test (format is { test_name: std_dev })
    std_devs = calc_std_devs(aggregated_tests)
    # Determine all significant regressions. Format is:
    # { test_name: [ (commit_a, commit_b), (commit_a, commit_b) ] }
    significant_changes = find_significant_changes(
            aggregated_tests,
            std_devs,
            commit_shas)

    for test in significant_changes:
        print(
                test,
                'has',
                len(significant_changes[test]),
                'significant regressions')

if __name__ == '__main__':
    main()
