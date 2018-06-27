const scpclient = require('scp2');
const { exec } = require('child_process');

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

            scpclient.scp(file, {
                host: host,
                username: user,
                path: destination,
                privateKey: require("fs").readFileSync(process.env.HOME+'/.ssh/id_rsa'),
                //           passphrase: '', //TODO if the key has a passphrase, this must be set
            }, err => {
                if(err) {
                    reject(err)
                } else {
                    resolve()
                }

                exec('ssh-keygen -R '+host);
            });
        });
    });
}


module.exports = {
    send_file: send_file,
};
