#!/bin/bash
set -x

apt update
apt install -y make gcc libssl-dev expat libcurl4-openssl-dev libexpat1-dev gettext zip
cpan JSON

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
    rm -rf perf-reports
    mkdir perf-reports
    for filename in t/perf/p*.sh ; do
        if [ filename -eq "perf-lib.sh" ]; then
            continue
        fi

        perf record -e instructions:u "./run . origin/master . $filename"
        if [ "$?" -ne "0" ] ; then
            touch perf-reports/$filename_record_failed
            continue
        fi
        perf report -t , -d git > perf-reports/$filename-perf-report.csv
        if [ "$?" -ne "0" ] ; then
            touch perf-reports/$filename_report_failed
            continue
        fi
    done
    zip $COMMIT-perf-reports.zip -r perf-reports
    mv $COMMIT-perf-reports.zip ~
    cd -


    curl "research.tiks.pw/finished/$COMMIT"
done

curl research.tiks.pw/killme/conductor_said_i_was_done
shutdown -h now
