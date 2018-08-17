import pymongo
from pymongo import MongoClient
from lizard_wrapper import run_lizard
from git import Repo
from git_helpers import get_changed_files, get_tracked_files

def get_commit_list():
    with open('commits_in_reverse_order') as f:
        return [c.strip() for c in f]

def main():
    client = MongoClient()
    db = client.research
    commits = get_commit_list()
    repo_path = '/home/kevin/thesis/git'
    repo = Repo(repo_path)

    commits_already_done = db.lizard_results.find({}, { "commitsha": True })
    commits_already_done = [c["commitsha"] for c in commits_already_done]

    for i, commit in enumerate(commits):
        print("(", i+1, "/", len(commits), ")", commit)
        if commit in commits_already_done:
            continue
        repo.git.checkout(commit)
        x = run_lizard(get_tracked_files([repo.tree()]))

        cleaned_data = []
        for key in x:
            cleaned_data.append({
                "filename": key,
                "functions": [ (
                    f.long_name, f.start_line, f.end_line
                ) for f in x[key] ],
            })


        db.lizard_results.insert_one({ "commitsha": commit, "data": cleaned_data})

if __name__ == '__main__':
    main()
