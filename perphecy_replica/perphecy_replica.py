#!/usr/bin/python

from lizard_wrapper import run_lizard
from git import Repo
from git_helpers import get_tracked_files

class CommitDetails:
    def __init__(self, sha, functions):
        self.sha = sha
        self.functions = functions

class Analysis():
    cur_analysis = {}
    prev_analysis = {}

    def __init__(self, repo_path, num_commits=1000, branch='master'):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        self.commits = list(self.repo.iter_commits('master', max_count=num_commits))
        self.commits.reverse()

        self.commit_iter = iter(self.commits)
        self.cur_commit = next(self.commit_iter)
        self.prev_commit = None

        self.analyze_current_commit()

    def step(self):
        """
        Analyze the next commit
        """
        self.prev_commit = self.cur_commit
        self.cur_commit = next(self.commit_iter)
        print('Checked out', self.cur_commit.hexsha)

        self.prev_analysis = self.cur_analysis
        self.cur_analysis = {}

        self.analyze_current_commit()

        indicators = self.calculate_indicators()
        print(indicators)

    def analyze_current_commit(self):
        files = get_tracked_files([self.repo.tree()])
        self.cur_analysis['lizard_results'] = run_lizard(files)

    def calculate_indicators(self):
        """
        Returns a dict with the indicator name as key and value as value
        """
        indicators = {}
        indicators['Del Func >= X'] = self.calc_deleted_functions()

        return indicators

    def calc_deleted_functions(self):
        deleted_functions = []

        for old_file, old_functions in self.prev_analysis['lizard_results'].items():
            if old_file not in self.cur_analysis['lizard_results']:
                print(old_file, 'was deleted')
                deleted_functions.extend(old_functions)
            else:
                for old_function in old_functions:
                    new_functions = self.cur_analysis['lizard_results'][old_file]
                    if old_function not in new_functions:
                        print(old_function, 'was deleted')

        return deleted_functions

def main():
    print('Perphecy Replica')
    repo_path = "~/thesis/git/"
    a = Analysis(repo_path)
    for x in range(1,1000):
        a.step()


if __name__ == "__main__":
    main()
