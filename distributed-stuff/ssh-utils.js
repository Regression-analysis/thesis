const sequest = require('sequest')
const scpclient = require('scp2');
const { exec } = require('child_process');
const fs = require('fs');
const private_key = fs.readFileSync(process.env.HOME + '/.ssh/id_rsa')

function send_file(file, host, user, destination) {
    return new Promise((resolve, reject) => {
        let cmd =
            'ssh-keyscan -H '+host+' >> '+process.env.HOME+'/.ssh/known_hosts';
        console.log(cmd);
        exec(cmd, (error, stdout, stderr) => {
            if (error) {
                console.error(`exec error: ${error}`);
                reject(error);
                return;
            }

            console.log(stdout);
            console.error(stderr);

            scpclient.scp(file, {
                host: host,
                username: user,
                path: destination,
                privateKey: private_key
                //           passphrase: '', //TODO if the key has a passphrase, this must be set
            }, err => {
                if(err) {
                    reject(err)
                } else {
                    resolve()
                }
            });
        });
    });
}

function get_file(remote_filepath, host, user, local_destination) {
    return new Promise((resolve, reject) => {
        scpclient.scp({
            host: host,
            username: user,
            path: remote_filepath,
            privateKey: private_key
            //           passphrase: '', //TODO if the key has a passphrase, this must be set
        }, local_destination, err => {
            if(err) {
                reject(err)
            } else {
                resolve()
            }
        });
    });
}

function start_command(cmd, droplet) {
    return new Promise((resolve, reject) => {
        const host = droplet.networks.v4[0].ip_address;
        sequest(`root@${host}`, {
            command: cmd,
            privateKey: private_key,
        }, function(e, stdout) {
            if(e) {
                reject(e);
            } else {
                console.log(stdout.split('\n'));
                resolve();
            }
        });
    })
}


module.exports = {
    send_file: send_file,
    get_file: get_file,
    start_command: start_command,
};
