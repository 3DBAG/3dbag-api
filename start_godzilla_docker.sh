#!/bin/bash
api="3dbag-api"
docker container stop ${api} || true
docker build -t ${api} .
docker run \
  --platform linux/amd64\
  --rm \
  -d \
  --env-file ".env"\
  --network="host" \
  --name=${api} \
  -v "$(pwd)":/app ${api}