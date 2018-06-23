#!/bin/bash
set -x

rm -rf ~/RESULTS/
mkdir ~/RESULTS

cd ~/git
git reset --hard
git clean -ffdx
git checkout master
COMMITS_IN_REVERSE=($(git rev-list HEAD --reverse))

echo ${#COMMITS_IN_REVERSE[@]} commits to test

sleep 3

count=0
for commit in "${COMMITS_IN_REVERSE[@]}"
do
    (( count++ ))
    if [ "$count" -lt "43000" ]; then
        echo "Skipping $count: $commit"
        continue
    fi
    git checkout $commit
    ls ~/git/t/perf
    if [ "$?" -ne "0" ] ; then
        echo "No perf tests for $count: $commit"
        continue
    fi
    echo "($count/${#COMMITS_IN_REVERSE[@]}): Testing commit $commit"
    mkdir ~/RESULTS/$count-$commit
    cd ~/git
    make > ~/RESULTS/$count-$commit/build_output.txt 2>&1
    if [ "$?" -ne "0" ]; then
        echo "Build make failed" > ~/RESULTS/$count-$commit/BUILDMAKEFAILED
        continue
    fi
    cd ~/git/t/perf
    rm -rf test-results/
    make > ~/RESULTS/$count-$commit/test_output.txt 2>&1
    if [ "$?" -ne "0" ]; then
        echo "Test make failed" > ~/RESULTS/$count-$commit/TESTMAKEFAILED
        continue
    fi
    cp test-results/*.times ~/RESULTS/$count-$commit
done
