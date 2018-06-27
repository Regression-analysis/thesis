def get_tracked_files(trees):
    paths = []
    for tree in trees:
        for blob in tree.blobs:
            paths.append(blob.abspath)
    if tree.trees:
        paths.extend(get_tracked_files(tree.trees))
    return paths

def get_changed_files(commit):
    diff_files = []
    for parent in commit.parents:
        diff_files += [x.b_path for x in commit.diff(parent)]

    return diff_files
