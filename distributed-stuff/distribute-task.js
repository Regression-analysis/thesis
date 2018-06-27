#!/usr/bin/node

const DO = require('./droplet-utils');

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
    console.log('You must set the environment variable TOKEN to your digitalocean api token');
    process.exit(1);
}

if(!argv.workers) {
    console.log('You must set the number of workers with --workers');
    process.exit(1);
}

if(!argv.task) {
    console.log('You must specify a task (bash file) to run using --task');
    process.exit(1);
}


console.log('Creating', argv.workers, 'worker servers to execute', argv.task);

droplets_to_create = [];
for(var i = 1; i <= argv.workers; i++) {
    droplets_to_create.push('Worker-'+i);
}



function wait_for_droplet_to_boot(droplet_id) {
    return new Promise((resolve, reject) => {
        let tries = 60;

        let check_if_active = () => {
            DO.get_droplet(droplet_id)
                .then(droplet => {
                    if(droplet.status === "active") {
                        resolve(droplet);
                    } else {
                        if(tries > 0) {
                            tries--;
                            setTimeout(check_if_active, 5000);
                        } else {
                            reject(droplet);
                        }
                    }
                });
        };

        check_if_active();
    });
}

function create_droplet_and_wait_for_boot(name, ssh_key_ids) {
    return DO.create_droplet(name, ssh_key_ids)
        .then(droplet => {
            return wait_for_droplet_to_boot(droplet.id);
        });
}

let droplets = [];
DO.get_account_ssh_keys()
    .then(ssh_keys => ssh_keys.map(k => k.id))
    .then(ssh_key_ids => {
        const promises = [];

        droplets_to_create.forEach(name => {
            promises.push( create_droplet_and_wait_for_boot(name, ssh_key_ids) );
        });

        return Promise.all(promises);
    })
    .then(created_droplets => {
        droplets = created_droplets;
        const promises = [];

        created_droplets.forEach(droplet => {
            promises.push( DO.delete_droplet(droplet.id) );
        });

        return Promise.all(promises);
    });
