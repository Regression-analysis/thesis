#!/usr/bin/python

from lizard_wrapper import run_lizard
from git import Repo
from git_helpers import get_changed_files, get_tracked_files
from perf_test_runner import *

class Config():
    def __init__(self, del_func_X=1, new_func_X=1, top_chg_len_X=1):
        self.del_func_X = del_func_X
        self.new_func_X = new_func_X
        self.top_chg_len_X = top_chg_len_X


class Analysis():
    cur_analysis = {}
    prev_analysis = {}

    def __init__(self, repo_path, num_commits=1000, branch='master', config=Config()):
        self.config = config
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        self.commits = list(self.repo.iter_commits('master', max_count=num_commits))
        self.commits.reverse()

        self.commit_iter = iter(self.commits)
        self.cur_commit = next(self.commit_iter)
        self.prev_commit = None

        self.repo.git.checkout(self.cur_commit.hexsha)
        self.analyze_current_commit(first_time=True)
        #self.run_benchmarks()

    def run_benchmarks(self):
        compile_git(self.repo_path)
        self.cur_analysis['benchmarks'] = {}
        benchmarks = get_perf_tests_git(self.repo_path)
        for benchmark in benchmarks:
            self.cur_analysis['benchmarks'][benchmark] = run_benchmark_git(self.repo_path, benchmark)

    def step(self):
        """
        Analyze the next commit
        """
        self.prev_commit = self.cur_commit
        self.cur_commit = next(self.commit_iter)
        self.repo.git.checkout(self.cur_commit.hexsha)
        print('Checked out', self.cur_commit.hexsha)

        self.prev_analysis = self.cur_analysis
        self.cur_analysis = {}

        self.analyze_current_commit()
        #self.run_benchmarks()

        indicators = self.calculate_indicators()
        print(indicators)
        return (self.cur_commit.hexsha, indicators)

    def analyze_current_commit(self, first_time=False):
        if first_time:
            # Run lizard on all files
            all_files = get_tracked_files([self.repo.tree()])
            self.cur_analysis['lizard_results'] = run_lizard(all_files)
            return

        changed_files = get_changed_files(self.cur_commit)
        changed_files = [self.repo_path + f for f in changed_files]
        new_lizard_results = run_lizard(changed_files)
        self.cur_analysis['new_lizard_results'] = new_lizard_results
        self.cur_analysis['lizard_results'] = self.prev_analysis['lizard_results']
        for key, value in new_lizard_results.items():
            self.cur_analysis['lizard_results'][key] = value


    def calculate_indicators(self):
        """
        Returns a dict with the indicator name as key and value as value
        """
        indicators = {}
        indicators['Del Func >= X'] = self.del_func_indicator()
        indicators['New Func >= X'] = self.new_func_indicator()
        indicators['Top Chg Len >= X%'] = self.top_change_length_indicator()

        return indicators

    def top_change_length_indicator(self):
        return self.calc_top_function_change_length_percent() > self.config.top_chg_len_X

    def calc_top_function_change_length_percent(self):
        top = 0
        functions_with_different_length = []
        for filename, functions in self.cur_analysis['new_lizard_results'].items():
            if filename not in self.prev_analysis['lizard_results']:
                continue

            # Put functions into a hash so we dont do this in O(n^2)
            functions_we_maybe_changed = {}
            for function in functions:
                functions_we_maybe_changed[function.long_name] = function
                import ipdb; ipdb.set_trace()

            for function in self.prev_analysis['lizard_analysis'][filename]:
                if function.long_name in functions_we_maybe_changed:
                    if function.nloc != functions_we_maybe_changed[function.long_name].nloc:
                        functions_with_different_length.append(function.long_name)

        return top

    def del_func_indicator(self):
        return len(self.calc_deleted_functions()) >= self.config.del_func_X

    def new_func_indicator(self):
        return len(self.calc_new_functions()) >= self.config.new_func_X

    def calc_deleted_functions(self):
        deleted_functions = []

        for old_file, old_functions in self.prev_analysis['lizard_results'].items():
            if old_file not in self.cur_analysis['lizard_results']:
                deleted_functions.extend(old_functions)
            else:
                for old_function in old_functions:
                    new_functions = self.cur_analysis['lizard_results'][old_file]
                    if old_function not in new_functions:
                        deleted_functions.append(old_function)

        return deleted_functions

    def calc_new_functions(self):
        added_functions = []

        for new_file, new_functions in self.cur_analysis['lizard_results'].items():
            if new_file not in self.prev_analysis['lizard_results']:
                added_functions.extend(new_functions)
            else:
                for new_function in new_functions:
                    old_functions = self.prev_analysis['lizard_results'][new_file]
                    if new_function not in old_functions:
                        added_functions.append(new_function)

        return added_functions

def main():
    print('Perphecy Replica')
    repo_path = "/home/kevin/thesis/git/"
    a = Analysis(repo_path)
    with open('perphecy_replica_results.txt', 'w+') as f:
        while True:
            try:
                indicators = a.step()
                f.write(str(indicators)+'\n')
                f.flush()
            except StopIteration:
                break


if __name__ == "__main__":
    main()
