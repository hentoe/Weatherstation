server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};
    http2 on;
    location /.well-known/acme-challenge/ {
        root /vol/www/;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}