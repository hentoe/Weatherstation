FROM python:3.11-alpine3.18
LABEL maintainer="hentoe"

# Environment variables
ENV PYTHONUNBUFFERED 1

COPY ./requirements/base.txt /tmp/base.txt
COPY ./requirements/dev.txt /tmp/dev.txt
COPY ./scripts /scripts
COPY ./app /app
# Workdir: where commands like python manage.py test are run from
WORKDIR /app

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache --virtual .tmp-build-deps-cryptography \
        alpine-sdk libffi-dev python3-dev && \
    /py/bin/pip install cryptography && \
    apk del .tmp-build-deps-cryptography && \
    apk add --update --no-cache jpeg-dev libpq libssl3 && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev gettext musl-dev zlib zlib-dev linux-headers libpq-dev python3-dev && \
    /py/bin/pip install -r /tmp/base.txt && \
    if [ $DEV = true ]; \
        then /py/bin/pip install -r /tmp/dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts

ENV PATH="/scripts:/py/bin:$PATH"

USER django-user

CMD ["run.sh"]