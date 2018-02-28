#!/bin/bash

# Start from master
git checkout master

# trap ctrl-c and call ctrl_c()
trap ctrl_c INT

function ctrl_c() {
    exit 1
}

# Get a list of commits in order from oldest to master
COMMITS=$(git log --reverse | grep "^commit\ [a-zA-Z0-9]*$" | sed 's/commit\ //g')

COMMITS_ARR=($COMMITS)
echo "SHA : RESULT" > results.txt
for sha in "${COMMITS_ARR[@]}"
do
    git checkout $sha
    mvn test > /tmp/thesis_cur_out_stuff.txt 2>&1
	echo "$sha : $?" >> results.txt
done
