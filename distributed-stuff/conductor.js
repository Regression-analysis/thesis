const express = require('express');
const app = express();
const port = process.env.PORT || 8080;

function get_machine_ip(req) {
    return req.headers['x-forwarded-for'] || req.connection.remoteAddress;
}

let stat = {
    commits_to_run: [],
    commits_completed: [],
    commits_in_progress: {},
};

app.get('/observe', (req, res) => {
    res.send(stat);
});

app.get('/finished/:commit', (req, res) => {
    const machine_ip = get_machine_ip(req);
    const commit = req.params.commit;
    delete commits_in_progress[commit]
    commits_completed.push({ machine_ip: machine_ip, commit: commit });
});

app.get('/', (req, res) => {
    if(stat.commits_to_run.length < 1) {
        res.send('DONE');
        return;
    }

    const machine_ip = get_machine_ip(req);
    const commit = stat.commits_to_run.shift();
    commits_in_progress[commit] = machine_ip;
    res.send(commit);
});

app.listen(port);
console.log('App listening on port', port);
