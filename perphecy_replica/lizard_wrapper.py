import lizard
import re

def run_lizard(file_paths):
    """
    This function runs the lizard tool (https://github.com/terryyin/lizard)
    on the given file paths.

    This tool can calculate number of lines of code, cyclomatic
    complexity, and a couple other metrics.

    It returns a dict like this:
    {
      'my_filename': [FunctionInfo, ...]
    }
    """
    function_infos = {}

    for file_path in file_paths:
        # Filter out anything lizard cant parse
        if not lizard_can_parse(file_path):
#            print('Lizard cant parse', file_path)
            continue

        lizard_analysis = lizard.analyze_file(file_path)
        function_infos[file_path] = lizard_analysis.function_list

    return function_infos


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
    match = re.search(r"\.[0-9a-zA-Z]+$", file_path)
    if match == None:
        return False

    extension = match.group()

    return extension.lower() in parseable_extensions
