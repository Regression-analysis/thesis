#!/bin/bash
set -x


cd ~
git clone https://github.com/git/git
cd git

while [ 1 ]
do
    COMMIT=$(curl --fail research.tiks.pw/nextcommit)
    if [ "$?" -ne "0" ] ; then
        echo "Unable to hit tiks.pw. Ill wait and try again"
        sleep 10
        continue
    fi

    if [ "$COMMIT" == "DONE" ]; then
        echo "No more commits, exiting"
        break
    fi

    echo "Checking out $COMMIT"
    git checkout "$COMMIT"
    if [ "$?" -ne "0" ] ; then
        echo "GIT CHECKOUT FAILED FOR COMMIT $COMMIT"
        mkdir -p t/perf/test-results
        touch t/perf/test-results/TEST_MAKE_FAILED
        zip $COMMIT-results.zip -r t/perf/test-results ~/task.out ~/task.err
        mv $COMMIT-results.zip ~
        curl "research.tiks.pw/finished/$COMMIT"
        continue
    fi
    echo "Building $COMMIT"
    make
    if [ "$?" -ne "0" ] ; then
        echo "BUILD MAKE FAILED FOR COMMIT $COMMIT"
    fi

    echo "Testing $COMMIT"
    # Now we need to run each test individually
    cd t/perf
    # BUT first we have to run one test, to guarantee everything is fully built
    # running a test does some make steps, but this will impact our profiler
    # thus, run a small test, then actually do the profiling
    ./run . origin/master . p0000-perf-lib-sanity.sh
    rm -rf perf-reports
    mkdir perf-reports
    files=$(ls | grep "^p.*.sh" | grep -v perf-lib.sh)
    for filename in $files ; do
        echo running $filename
        perf record -e instructions:u ./run . origin/master . $filename
        if [ "$?" -ne "0" ] ; then
            touch perf-reports/$filename-record_failed
            continue
        fi
        perf report -t , -d git > perf-reports/$filename-perf-report.csv
        if [ "$?" -ne "0" ] ; then
            touch perf-reports/$filename-report_failed
            continue
        fi
    done
    zip $COMMIT-results.zip -r perf-reports ~/task.out ~/task.err
    mv $COMMIT-results.zip ~
    cd -


# UNDO curl "research.tiks.pw/finished/$COMMIT"
done

# curl research.tiks.pw/killme/conductor_said_i_was_done
# UNDO shutdown -h now
