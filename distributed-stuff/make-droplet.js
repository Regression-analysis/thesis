const request = require('request-promise');

TOKEN = process.env.TOKEN;

function get_account_ssh_keys() {
    return request.get({
        url: 'https://api.digitalocean.com/v2/account/keys',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+TOKEN,
        },
    })
    .then(body => JSON.parse(body))
    .then(body => body.ssh_keys)
}

function create_droplet(name, ssh_keys) {
    const droplet_details = {
        name: name,
        region: 'nyc1',
        size: 's-1vcpu-1gb',
        image: 'ubuntu-16-04-x64',
        ssh_keys: ssh_keys,
    };

    const create_droplet_post = {
        url: 'https://api.digitalocean.com/v2/droplets',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+TOKEN,
        },
        json: droplet_details,
    }

    return request.post(create_droplet_post)
        .then(body => JSON.parse(body));
}

function delete_droplet(droplet_id) {
    return request({
        method: 'DELETE',
        url: 'https://api.digitalocean.com/v2/droplets/'+droplet_id,
    })
}

droplets_to_create = [
    'Worker1',
    'Worker2',
];

get_account_ssh_keys()
    .then(ssh_keys => ssh_keys.map(k => k.id))
    .then(ssh_key_ids => {
        const promises = [];

        droplets_to_create.forEach(name => {
            promises.push( create_droplet(name, ssh_key_ids) );
        });

        return promises;
    })
    .then(created_droplets => {
        console.log(created_droplets);
        const promises = [];

        created_droplets.forEach(droplet => {
            promises.push( delete_droplet(droplet.id) );
        });

        return promises;
    });
