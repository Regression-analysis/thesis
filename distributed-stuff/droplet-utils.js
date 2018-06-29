const request = require('request-promise');

TOKEN = process.env.TOKEN;

module.exports = {
    get_account_ssh_keys: () => {
        return request.get({
            url: 'https://api.digitalocean.com/v2/account/keys',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '+TOKEN,
            },
        })
            .then(body => JSON.parse(body))
            .then(body => body.ssh_keys)
    },

    create_droplet: (name, ssh_keys) => {
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
            .then(body => {
                console.log('Created new droplet:',
                    body.droplet.name,
                    body.droplet.id);
                return body.droplet;
            });
    },

    delete_droplet: (droplet_id) => {
        console.log('Destroying droplet', droplet_id);
        return request({
            method: 'DELETE',
            url: 'https://api.digitalocean.com/v2/droplets/'+droplet_id,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '+TOKEN,
            },
        })
    },

    get_droplet: (droplet_id) => {
        return request.get({
            url: 'https://api.digitalocean.com/v2/droplets/'+droplet_id,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '+TOKEN,
            },
        })
            .then(body => JSON.parse(body).droplet);
    },
};
