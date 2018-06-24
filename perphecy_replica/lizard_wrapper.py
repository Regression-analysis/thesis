import lizard
import re

def run_lizard(file_paths, root_path, diff):
    """
    " This function runs the lizard tool (https://github.com/terryyin/lizard)
    " on the given file paths.
    "
    " This tool can calculate number of lines of code, cyclomatic
    " complexity, and a couple other metrics.
    "
    " The lizard tool runs on files, and so it returns metrics for functions
    " that we may not have touched. We use the diff to determine
    " whether we actually edited a given function. That way we ignore
    " functions that lizard analyzes but we dont care about
    """
    highest_complexity = 0
    total_complexity = 0
    for file_path in file_paths:
        # Filter out anything lizard cant parse
        if not lizard_can_parse(file_path):
            next
        end

        # Figure out which lines we actually touched in our diff.
        lizard_analysis = lizard.analyze_file(root_path+'/'+file_path)
        for func_info in lizard_analysis.function_list:

            cc = func_info.__dict__['cyclomatic_complexity']
            fn_start = func_info.__dict__['start_line']
            fn_end = func_info.__dict__['end_line']

            # Did we actually touch this function?
            if diff_touched_lines(diff, file_path, fn_start, fn_end):
                total_complexity += cc
                # Is this complexity higher than our current highest?
                if cc > highest_complexity:
                    highest_complexity = cc
    return highest_complexity, total_complexity


def lizard_can_parse(file_path):
    """
    Returns true if lizard can parse the file extension in the given file path
    """
    parseable_extensions = [
        '.c',
        '.h',
        '.cpp',
        '.hpp',
        '.java',
        '.cs',
        '.js',
        '.m',
        '.mm',
        '.swift',
        '.py',
        '.rb',
        '.ttcn',
        '.php',
        '.scala',
        '.tscn',
    ]
    match = re.match(r"\.[0-9a-zA-Z]+$", file_path)
    if match == None:
        return False

    extension = match.group()

    return extension.lower() in parseable_extensions
