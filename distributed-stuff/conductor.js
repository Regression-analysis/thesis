const ssh_utils = require('./ssh-utils');
const express = require('express');
const app = express();
const port = process.env.PORT || 8080;

function get_machine_ip(req) {
    return req.headers['x-forwarded-for'] || req.connection.remoteAddress;
}

let commits_to_run = [];
let commits_completed = [];
let commits_in_progress = {};

let finished_callback; // Call this when everything is all over

app.get('/observe', (req, res) => {
    res.send({
        commits_to_run: commits_to_run,
        commits_completed: commits_completed,
        commits_in_progress: commits_in_progress,
    });
});

app.get('/finished/:commit', (req, res) => {
    const machine_ip = get_machine_ip(req);
    const commit = req.params.commit;

    if(!commits_in_progress[commit]) {
        console.error(machine_ip, 'trying to complete', commit, 'which is not in progress');
        res.status(500).send('Invalid commit SHA');
        return;
    }
    
    if(commits_in_progress[commit].machine !== machine_ip) {
        console.error('Incorrect machine trying to submit commit deets:', machine_ip, commit);
        res.status(500).send('You are not assigned that commit');
        return;
    }

    console.log(machine_ip, 'completed', commit);

    //Now grab the zip file of the results
    ssh_utils.get_file(commit+'-results.zip', machine_ip, 'root', './results/')
        .then(() => {

            let start_time = commits_in_progress[commit].start_time;
            delete commits_in_progress[commit]
            commits_completed.push({
                machine_ip: machine_ip,
                commit: commit,
                start_time: start_time,
                end_time: new Date(),
            });
            res.send();

            if(commits_to_run.length === 0 &&
                Object.keys(commits_in_progress).length === 0) {
                console.log('All commits have been completed');
                finished_callback();
            }
        })
        .catch(err => {
            console.error('Unable to retrieve', commit, 'from', machine_ip);
            console.error(err);
        });
});

app.get('/nextcommit', (req, res) => {
    if(commits_to_run.length < 1) {
        res.send('DONE');
        return;
    }

    const machine_ip = get_machine_ip(req);
    const commit = commits_to_run.shift();
    commits_in_progress[commit] = { machine: machine_ip, start_time: new Date() };
    res.send(commit);

    console.log(machine_ip, 'is handling', commit);
});

module.exports = {
    start: (kill_instance_handler, finished_cb, all_commits) => {
        app.get('/killme/:msg', kill_instance_handler);
        finished_callback = finished_cb;
        commits_to_run = all_commits;

        app.listen(port);
        console.log('App listening on port', port);
    },
    get_machine_ip: get_machine_ip,
};
