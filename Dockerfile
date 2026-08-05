FROM tiangolo/uwsgi-nginx-flask:python3.10
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV LISTEN_PORT 3200
EXPOSE 3200
ENV STATIC_URL /static
ENV STATIC_PATH /var/www/3dbag-api/static
COPY pyproject.toml uv.lock /var/www/
WORKDIR /var/www
RUN uv export --no-dev --no-hashes --format requirements-txt > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt
