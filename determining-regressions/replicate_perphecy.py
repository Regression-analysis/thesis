import re
from git import Repo
import pymongo
from pymongo import MongoClient
from determine_significant_changes import determine_significant_changes

def get_commit_list(filename):
    commits = []
    with open(filename) as f:
        for line in f:
            # The file lists them in reverse order
            commits.insert(0, line.strip())

    return commits

def convert_lizard_result_data_into_a_dict(lizard_results_data):
    # Convert to dict: { filename: functions }
    new_dict = {}
    for file_info in lizard_results_data:
        new_dict[file_info["filename"]] = file_info["functions"]
    return new_dict

def make_func_dict(lizard_data):
    """
    Convert stored lizard data from this:
    [
        {
            filename: 'filename_1',
            functions: [
                (func_name_1, start_line, end_line),
                ...
            ]
        },
        ...
    ]
    to:
    {
        filename_1: {
            func_name_1: (func_name, start_line, end_line),
            func_name_2: ...,
        },
        filename_2: {
            ...
        },
    }
    """
    func_dict = {}
    for file_info in lizard_data:
        filename = file_info['filename']
        func_dict[filename] = {}

        for func_tuple in file_info["functions"]:
            funcname = func_tuple[0]
            func_dict[filename][funcname] = func_tuple

    return func_dict

def calc_added_and_deleted_functions(d1, d2):
    added_functions = []
    deleted_functions = []
    for filename in d1:
        if filename not in d2:
            # File was deleted, and thus all functions were deleted
            deleted_functions.extend([(filename, funcname) for funcname in d1[filename]])
        else:
            # File is in both, check functions
            for funcname in d1[filename]:
                if funcname not in d2[filename]:
                    # Function was deleted, add it
                    deleted_functions.append((filename, funcname))
            # Now check for added functions
            for funcname in d2[filename]:
                if funcname not in d1[filename]:
                    added_functions.append((filename, funcname))

    for filename in d2:
        if filename not in d1:
            # File was created, and thus all functions were added
            added_functions.extend([(filename, funcname) for funcname in d2[filename]])
        else:
            # We already handled this case in the previous loop
            pass

    return deleted_functions, added_functions

def ranges_overlap(x1, x2, y1, y2):
    if x1 <= y2 and y1 <= x2:
        # They overlap, but by how much?
        return max(0, min(x2, y2) - max(x1, y1) + 1)
    else:
        # They dont overlap
        return None

def calc_changed_functions(d1, d2, edited_lines):
    changed_functions = []
    for filename in edited_lines:
        fullpath = '/home/kevin/thesis/git/' + filename
        for change_range in edited_lines[filename]:
            if fullpath in d1:
                for funcname in d1[fullpath]:
                    func_info = d1[fullpath][funcname]
                    x1 = change_range['before'][0]
                    x2 = change_range['before'][1]
                    y1 = int(func_info[1])
                    y2 = int(func_info[2])
                    overlap = ranges_overlap(x1, x2, y1, y2)
                    if overlap is not None:
                        # Tuple format: (file, function, and percent change)
                        changed_functions.append(
                                (fullpath, funcname, overlap / (y2-y1+1)))

            if fullpath in d2:
                for funcname in d2[fullpath]:
                    func_info = d2[fullpath][funcname]
                    x1 = change_range['after'][0]
                    x2 = change_range['after'][1]
                    y1 = int(func_info[1])
                    y2 = int(func_info[2])
                    overlap = ranges_overlap(x1, x2, y1, y2)
                    if overlap is not None:
                        # Tuple format: (file, function, and percent change)
                        changed_functions.append(
                                (fullpath, funcname, overlap / (y2-y1+1)))

    return list(set(changed_functions))


def calc_changed_added_and_deleted_functions(data_1, data_2, edited_lines):
    d1 = make_func_dict(data_1)
    d2 = make_func_dict(data_2)

    deleted_functions, added_functions = calc_added_and_deleted_functions(d1, d2)
    changed_functions = calc_changed_functions(d1, d2, edited_lines)
    # Remove deleted/added funcs from changed functions

    changed_functions = [f for f in changed_functions if \
        len([d for d in deleted_functions if d[0] != f[0] or d[1] != f[1]]) > 0 \
        and
        len([a for a in added_functions if a[0] != f[0] or a[1] != f[1]]) > 0]


    return deleted_functions, added_functions, changed_functions


def calc_reached_del_func(deleted_functions, profile_info):
    reached_del_func_by_benchmark = {} # { b1: [f1, f2], b2: [f1, f2] }
    deleted_function_names = [f[1].split('(')[0] for f in deleted_functions]
    for test in profile_info["tests"]:
        called_functions = [o["symbol"] for o in test["overheads"]]
        reached_del_func_by_benchmark[test["test_name"]] = \
                set(called_functions).intersection(set(deleted_function_names))

    return reached_del_func_by_benchmark

def calc_reached_changed_func(changed_functions, profile_info):
    reached_changed_func_by_benchmark = {} # { b1: [f1, f2], b2: [f1, f2] }
    changed_function_names = [f[1].split('(')[0] for f in changed_functions]
    for test in profile_info["tests"]:
        called_functions = [o["symbol"] for o in test["overheads"]]
        reached_changed_func_by_benchmark[test["test_name"]] = \
                [c for c in changed_functions if c[1].split('(')[0] in called_functions]

    return reached_changed_func_by_benchmark


def get_edited_lines(c1, c2, repo):
    file_header_regex = re.compile('^diff --git.*')
    filename_regex = re.compile('^.*b/(.*)')
    hunk_regex = re.compile('^@@\ [\-\+]([0-9\,]*)\ [\-\+]([0-9\,]*)\ @@.*$')

    # {
    #     filename: [{
    #         before: (start_line, size),
    #         after: (start_line, size),
    #     }, ...]
    # }
    edited_lines = {}

    filename = None
    change_ranges = []

    diff = repo.git.diff(c1, c2, '-U0')

    for line in diff.split('\n'):
        if file_header_regex.match(line) is not None:
            # this is a new hunk
            if filename is not None and len(change_ranges) != 0:
                edited_lines[filename] = change_ranges

            filename = filename_regex.match(line).group(1)
            change_ranges = []
            continue

        hunk_match = hunk_regex.match(line)
        if hunk_match is not None:
            before = hunk_match.group(1).split(',')
            before = [int(n) for n in before]
            after = hunk_match.group(2).split(',')
            after = [int(n) for n in after]
            change_ranges.append({
                "before": (before[0], before[0] + before[1] if len(before) > 1 else before[0]),
                "after": (after[0], after[0] + after[1] if len(after) > 1 else after[0]),
            })

    return edited_lines


def get_top_chg_by_call(changed_funcs, profile_data):
    just_func_names = [k[1].split('(')[0] for k in changed_funcs]

    top_changes_by_call_by_benchmark = {}
    for test_data in profile_data['tests']:
        # Remove unknown symbols
        overheads = [p for p in test_data['overheads'] if '0x0' not in p['symbol']]
        # Remove entries with overhead of 0
        overheads = [p for p in overheads if p['overhead_percent'] is not 0]

        top_changes_by_call_by_benchmark[test_data['test_name']] = \
            [p for p in overheads if p['symbol'] in just_func_names]


    return top_changes_by_call_by_benchmark

def get_static_function_length_change(changed_funcs):
    file_to_func_to_percent_change = {}
    for entry in changed_funcs:
        filename, funcname, percent = entry
        if filename not in file_to_func_to_percent_change:
            file_to_func_to_percent_change[filename] = {}

        file_to_func_to_percent_change[filename][funcname] = percent

    return file_to_func_to_percent_change

def calc_indicators(
    del_funcs,
    added_funcs,
    changed_funcs,
    reached_del_func_by_benchmark,
    top_chg_by_call_by_benchmark,
    reached_changed_func_by_benchmark,
    thresholds):

    indicators = {} # { benchmark1: {indicator1: Value }}
    for benchmark in reached_del_func_by_benchmark:
        indicators[benchmark] = {}

        indicators[benchmark]['Del Func >= X'] = \
            len(del_funcs)

        indicators[benchmark]['New Func >= X'] = \
            len(added_funcs)

        indicators[benchmark]['Reached Del Func >= X'] = \
            len(reached_del_func_by_benchmark[benchmark])

        top_percents = [c['overhead_percent'] for c in top_chg_by_call_by_benchmark[benchmark]]
        indicators[benchmark]['Top Chg by Call >= X%'] = \
            max(top_percents) if len(top_percents) > 0 else 0


        over_10_percent = [c[1].split('(')[0] for c in changed_funcs if c[2] >= .1]

        top_over_10 = [c for c in top_chg_by_call_by_benchmark[benchmark] if c['symbol'] in over_10_percent]

        indicators[benchmark]['Top > X% by Call Chg by >= 10%'] = \
                top_over_10[0]['overhead_percent'] if len(top_over_10) > 0 else 0

        indicators[benchmark]['Top Chg by Instr >= X%'] = \
                False #TODO

        indicators[benchmark]['Top Chg Len >= X%'] = \
                max([c[2] for c in changed_funcs]) if len(changed_funcs) > 0 else 0

        indicators[benchmark]['Top Reached Chg Len >= X%'] = \
                max([c[2] for c in reached_changed_func_by_benchmark[benchmark]]) if len(reached_changed_func_by_benchmark[benchmark]) > 0 else 0

    return indicators

def main():
    # Set up the git repo stuff
    repo = Repo("~/thesis/git/")

    # Get the regressions. This acts as our truth.
    significant_changes = determine_significant_changes("results.csv")

    # Run perphecy on the commits
    commits = get_commit_list("commits_in_order")

    client = MongoClient()
    db = client.research

    headers = []
    first_time = True

    for c1, c2 in zip(commits, commits[1:]):
        most_recent_profile = db.commitprofiles.find_one({
            "commitsha": c1
        })
        if most_recent_profile == None:
            print("No profile for ", c1)
            continue

        lizard1 = db.lizard_results.find_one({ "commitsha": c1 })
        lizard2 = db.lizard_results.find_one({ "commitsha": c2 })
        edited_lines = get_edited_lines(c1, c2, repo)

        del_funcs, added_funcs, changed_funcs = \
                calc_changed_added_and_deleted_functions(
                        lizard1["data"],
                        lizard2["data"],
                        edited_lines)

        reached_del_func_by_benchmark = \
                calc_reached_del_func(del_funcs, most_recent_profile)

        reached_changed_func_by_benchmark = \
                calc_reached_changed_func(changed_funcs, most_recent_profile)

        top_chg_by_call_by_benchmark = \
                get_top_chg_by_call(changed_funcs, most_recent_profile)

        indicators = calc_indicators(
                del_funcs,
                added_funcs,
                changed_funcs,
                reached_del_func_by_benchmark,
                top_chg_by_call_by_benchmark,
                reached_changed_func_by_benchmark,
                get_thresholds())




        # Now just print it out
        if 'Commit A' not in headers:
            headers.append('Commit A')
        if 'Commit B' not in headers:
            headers.append('Commit B')
        if 'Benchmark' not in headers:
            headers.append('Benchmark')
        for benchmark in indicators:
            for indicator in indicators[benchmark]:
                if indicator not in headers:
                    headers.append(indicator)

        if first_time:
            first_time = False
            print(','.join(headers))

        for benchmark in indicators:
            print(c1[:8], end=',')
            print(c2[:8], end=',')
            print(benchmark, end='')
            for indicator in indicators[benchmark]:
                print(','+str(indicators[benchmark][indicator]), end='')
            print('')


def get_thresholds():
    return {
        'Del Func X': 0,
        'New Func X': 0,
        'Reached Del Func X': 0,
        'Top Chg by Call X': 0,
        'Top X% by Call Chg by >= 10%': 0,
        'Top Chg by Instr X': 0,
        'Top Chg Len X': 0,
        'Top Reached Chg Len X': 0,
    }


if __name__ == '__main__':
    main()
