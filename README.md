# Weatherstation

Educational project to learn building a web app with django.

## Installation

- Clone the repository
- Build the docker image
- Run the docker container

```bash
    git clone git@github.com:hentoe/Weatherstation.git
    docker compose build
    docker compose up
```

## Run tests

```bash
    docker compose run --rm app coverage run -m pytest
```

## Frontend

The frontend is built with Vue3 and found in a separate [repository](https://github.com/hentoe/WeatherstationUI).
