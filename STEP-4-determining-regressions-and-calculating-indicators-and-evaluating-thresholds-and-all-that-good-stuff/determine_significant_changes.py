from numpy import std, mean
from scipy.stats import ttest_ind
import math
import csv
import sys
import collections


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
                        if value is '':
                            values[index].append(None)
                        else:
                            str_arr = value[1:-2].split('|')
                            num_arr = [float(s) for s in str_arr]
                            values[index].append(num_arr)
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
            std_devs[test_name] = int(float(s))

    return std_devs


def mean(nums):
    return float(sum(nums)) / max(len(nums), 1)

alpha = 0.05
def significant_change(v1, v2):
    stuff = ttest_ind(v1, v2)
    if not stuff.pvalue < alpha:
        return False

    # Return true if it slowed down - i.e. the average for v2 is higher than v1
    return mean(v1) < mean(v2)

def find_significant_changes(aggregated_tests, commit_shas):
    significant_changes = {}

    for test_name in aggregated_tests:
        test_times = aggregated_tests[test_name]
        change_list = []

        i = -1
        past_runs = collections.deque(maxlen=10)
        for t1, t2 in zip(test_times, test_times[1:]):

            i += 1
            if t1 is None or t2 is None:
                continue # skip if we have no value for this test

            past_runs.append(t1)
            flattened = [item for sublist in past_runs for item in sublist]
            if significant_change(flattened, t2):
                change_list.append((commit_shas[i], commit_shas[i+1]))

        significant_changes[test_name] = change_list

    return significant_changes


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
                    aggregated_tests[base_name][i] = \
                        [v1[a] + v2[a] for a in range(0, len(v1))]

    return aggregated_tests


def print_significant_changes(significant_changes):
    for test in significant_changes:
        print(
                test,
                'has',
                len(significant_changes[test]),
                'significant regressions')


def determine_significant_changes(results_file):
    # Parse csv file
    headers, values = parse_file(results_file)
    commit_shas = values[0]
    # Aggregate subtests into their total test execution times
    aggregated_tests = aggregate_subtests(headers, values)
    # Calculate std deviation for each test (format is { test_name: std_dev })
    # std_devs = calc_std_devs(aggregated_tests)
    # Determine all significant regressions. Format is:
    # { test_name: [ (commit_a, commit_b), (commit_a, commit_b) ] }
    significant_changes = find_significant_changes(
            aggregated_tests,
    #       std_devs,
            commit_shas)

    return significant_changes


def main():
    if sys.argv[1] is None:
        print("You need to give the path to the results csv file")

    significant_changes = determine_significant_changes(sys.argv[1])
    print_significant_changes(significant_changes)


if __name__ == '__main__':
    main()
