import re
from os import listdir
from os.path import isfile, join
from subprocess import call

def get_perf_tests_git(source_root_path):
    perf_test_path = source_root_path + '/t/perf'
    files = [f for f in listdir(perf_test_path) if isfile(join(perf_test_path, f))]
    test_file_regex = re.compile(r'p[0-9][0-9][0-9].*\.sh')
    test_files = filter(test_file_regex.match, files)
    return list(test_files)

def run_benchmark_git(source_root_path, benchmark):
    perf_test_path = source_root_path + '/t/perf'
    run = perf_test_path + '/run'
    perf_repo = source_root_path
    # Run the benchmark
    call([run, perf_repo, 'origin/master', perf_repo, benchmark])

    # Now grab the test result files from this benchmark
    results_dir = perf_test_path + '/test-results'
    files = [f for f in listdir(results_dir) if isfile(join(results_dir, f))]
    results_files = []
    for filename in files:
        if benchmark[:-3] in filename and filename[len(filename)-5:] == 'times':
            results_files.append(filename)

    results = {}
    for filename in results_files:
        with open(results_dir + '/' + filename, 'r') as f:
            results[filename] = f.readlines()

    return results
