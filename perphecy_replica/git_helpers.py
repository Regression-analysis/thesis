def get_tracked_files(trees):
    paths = []
    for tree in trees:
        for blob in tree.blobs:
            paths.append(blob.abspath)
    if tree.trees:
        paths.extend(get_tracked_files(tree.trees))
    return paths
