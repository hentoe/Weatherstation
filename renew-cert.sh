#!/bin/sh

set -e

cd /home/$USER/sites/Wetterstation
/usr/bin/docker compose -f docker-compose-deploy.yml run --rm certbot certbot renew
