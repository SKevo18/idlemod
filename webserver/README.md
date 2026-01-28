# Idlemod Webserver

This is the (very simple) Flask Idlemod webserver. It is used for packing existing mods present in this repository into a single data file - useful for people that do not want to use the CLI and want to simply play the mods.

You can access it live at [https://idlemod.svit.ac](https://idlemod.svit.ac).

> **Note:** Mod folders starting with dot (`.`) are marked as WIP/temporary, and will be excluded from the webpage's mod list.

## Running it locally (for development)

1. Install Python 3.10+ virtualenv in `./.venv`: `python3 -m venv .venv`;
    - Python 3.12 is recommended;
2. Activate the virtualenv: `source .venv/bin/activate`;
3. Install dependencies: `pip install -r requirements.txt`;
4. `service idlemod start` if running via systemd, or simply `./start.sh`;
    - The webserver operates as a socket file. You can use `systemd` to manage it (see `idlemod.service` for example), or simply run `./start.sh` to start the Flask app.
5. Place your original data files in `../data/` (see `../data/README.md` for more info);

### Caddy

```caddyfile
idlemod.example.com {
    tls /etc/ssl/private/your-cert.pem /etc/ssl/private/your-cert.key

    handle_path /cache/* {
        root * /srv/idlemod/webserver/cache
        file_server
    }

    handle {
        reverse_proxy unix//srv/idlemod/webserver/server.sock
    }
}
```

### nginx

```nginx
server {
    listen 443 ssl;
    server_name idlemod.example.com;

    ssl_certificate /etc/ssl/private/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-cert.key;

    location /cache/ {
        alias /srv/idlemod/webserver/cache/;
        add_header Content-Disposition "attachment";
    }

    location / {
        proxy_pass http://unix:/srv/idlemod/webserver/server.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Apache

Requires `mod_proxy`, `mod_proxy_unix`, and `mod_headers`.

```apache
<VirtualHost *:443>
    ServerName idlemod.example.com

    SSLEngine on
    SSLCertificateFile /etc/ssl/private/your-cert.pem
    SSLCertificateKeyFile /etc/ssl/private/your-cert.key

    Alias /cache/ /srv/idlemod/webserver/cache/
    <Directory /srv/idlemod/webserver/cache/>
        Require all granted
        Header set Content-Disposition "attachment"
    </Directory>

    ProxyPass /cache/ !
    ProxyPass / unix:/srv/idlemod/webserver/server.sock
    ProxyPassReverse / unix:/srv/idlemod/webserver/server.sock
</VirtualHost>
```

**Note**: both the webserver and the idlemod hypercorn server must be run as the same user, or must have the same permissions to access the cache directory.
