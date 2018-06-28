#!/bin/bash
set -e

apt update
apt install -y make gcc libssl-dev expat libcurl4-openssl-dev libexpat1-dev gettext zip
cpan JSON

cd ~
git clone https://github.com/git/git
cd git

while [ 1 ]
do
    COMMIT=$(curl research.tiks.pw/nextcommit)
    if [ "$COMMIT" -eq "DONE" ]; then
        echo "No more commits, exiting"
        break
    fi

    echo "Checking out $COMMIT"
    git checkout "$COMMIT"
    if [ "$?" -ne "0" ] ; then
        curl research.tiks.pw/killme/git_checkout_failed
        exit 1
    fi
    echo "Building $COMMIT"
    make
    echo "Testing $COMMIT"
    cd t/perf
    ./run . origin/master . p3400-rebase.sh
    cd -
    #make -C t/perf
    zip $COMMIT-results.zip -r t/perf/test-results ~/task.out ~/task.err
    mv $COMMIT-results.zip ~

    curl "research.tiks.pw/finished/$COMMIT"
done

curl research.tiks.pw/killme/conductor_said_i_was_done
shutdown -h now
