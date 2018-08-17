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
    rm -rf t/perf/test-results
    make -C t/perf
    if [ "$?" -ne "0" ] ; then
        echo "TEST MAKE FAILED FOR COMMIT $COMMIT"
        mkdir -p t/perf/test-results
        touch t/perf/test-results/TEST_MAKE_FAILED
        continue
    fi
    zip $COMMIT-results.zip -r t/perf/test-results ~/task.out ~/task.err
    mv $COMMIT-results.zip ~

    curl "research.tiks.pw/finished/$COMMIT"
done

curl research.tiks.pw/killme/conductor_said_i_was_done
shutdown -h now
