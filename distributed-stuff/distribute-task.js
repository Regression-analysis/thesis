#!/usr/bin/node
const DO = require('./droplet-utils');
const ssh_utils = require('./ssh-utils');
const fs = require('fs');

let conductor = require('./conductor');

const argv = require('minimist')(process.argv.slice(2));

if(argv.help) {
    console.log(`
        distribute_task.js

        Runs a task across multiple digitalocean servers,
        orchestrating it from this one.

        OPTIONS:
        --workers: the number of digitalocean servers to spawn
        --task: the script to run on each server

        NOTE:
        Make sure that this computer can ssh and has its public key
        associated with your digitalocean account. Also, make sure
        environment variable TOKEN is set with your digitalocean api
        token.
        `);
    process.exit(0);
}

if(!process.env.TOKEN) {
    console.error('You must set the environment variable TOKEN to your digitalocean api token');
    process.exit(1);
}

if(!argv.workers) {
    console.error('You must set the number of workers with --workers');
    process.exit(1);
}
argv.workers = parseInt(argv.workers);
if(isNaN(argv.workers) || argv.workers < 1) {
    console.error('workers must be a positive integer');
    process.exit(1);
}

if(!argv.task) {
    console.error('You must specify a task (bash file) to run using --task');
    process.exit(1);
}
if(!fs.existsSync(argv.task)) {
    console.error(argv.task, 'does not exist');
    process.exit(1);
}


console.log('Creating', argv.workers, 'worker servers to execute', argv.task);

droplets_to_create = [];
for(var i = 1; i <= argv.workers; i++) {
    droplets_to_create.push('Worker-'+i);
}

function wait_for_droplet_to_boot(droplet_id) {
    console.log('Waiting for', droplet_id, 'to boot');
    return new Promise((resolve, reject) => {
        let tries = 60;

        let check_if_active = () => {
            DO.get_droplet(droplet_id)
                .then(droplet => {
                    if(droplet.status === "active") {
                        // Give it another break to calm itself,
                        // then continue
                        console.log(`${droplet.name} booted, waiting 30s`);
                        setTimeout(() => {
                            resolve(droplet)
                        }, 30000);
                    } else {
                        if(tries > 0) {
                            tries--;
                            setTimeout(check_if_active, 1000);
                        } else {
                            reject(droplet);
                        }
                    }
                })
                .catch(e => {
                    console.error(e);
                    if(tries > 0) {
                        tries--;
                        setTimeout(check_if_active, 1000);
                    } else {
                        reject(droplet);
                    }
                });
        };

        check_if_active();
    });
}

function create_droplet_and_wait_for_boot(name, ssh_key_ids) {
    return DO.create_droplet(name, ssh_key_ids)
        .then(droplet => (
            wait_for_droplet_to_boot(droplet.id)
        ));
}

let conductor_finished_callback;
let conductor_finished_promise = new Promise((resolve, reject) => {
    conductor_finished_callback = () => {
        resolve();
    };
});
let droplets = [];
DO.get_account_ssh_keys()
    .then(ssh_keys => ssh_keys.map(k => k.id))
    .then(ssh_key_ids => {
        return Promise.all(
            droplets_to_create.map(name =>
                create_droplet_and_wait_for_boot(name, ssh_key_ids)
            )
        );
    })
    .then(created_droplets => {
        droplets = created_droplets;
    })
    .then(() => {
        return Promise.all(
            droplets.map(droplet => {
                const host = droplet.networks.v4[0].ip_address;
                console.log('Sending files to', droplet.name, 'at', host);
                return ssh_utils.send_file(argv.task, host, 'root', '' );
            })
        );
    })
    .then(() => {
        // Start our conductor server
        conductor.start((req, res) => {
            const ip = conductor.get_machine_ip(req);
            console.log('ip addr', ip, 'requested kill because', req.params.msg);
            let drop = droplets.find(d => d.networks.v4[0].ip_address === ip);
            if(!drop) {
                console.error('Cant find droplet with ip', ip);
                res.status(500).send('I dont know who you are');
                return;
            }
            res.send();
            DO.delete_droplet(drop.id)
                .then(() => {
                    // Remove droplet from our list of droplets
                    droplets = droplets.filter(droplet =>
                        droplet.name !== drop.name)
                });
        }, conductor_finished_callback, require('./commits_to_run_on'));
    })
    .then(() => {
        console.log('Start the scripts on all the clients');
        const cmd = `chmod +x ~/${argv.task} && nohup ~/${argv.task} > task.out 2> task.err < /dev/null &`
        return Promise.all(
            droplets.map(droplet => ssh_utils.start_command(cmd, droplet))
        );
    })
    .then(() => {
        // Wait for the conductor to tell us we are done
        return conductor_finished_promise;
    })
    .catch(err => console.error(err))
    .finally(() => {
        console.log('Deleting the created droplets in 60 seconds');
        return Promise.all(
            droplets.map(droplet => new Promise((resolve, reject) => {
                setTimeout(() => {
                    DO.delete_droplet(droplet.id)
                        .then(resolve)
                        .catch(reject);
                }, 60000);
            }))
        );
    });


process.on('SIGINT', function() {
    console.log("Caught interrupt signal");

    Promise.all(droplets.map(d => DO.delete_droplet(d.id)))
        .then(() => process.exit(1));
});
