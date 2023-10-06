#!/bin/bash
server="3dbag-api.test"
docker container stop ${server} || true
docker build -t ${server} .
docker run \
  --platform linux/amd64\
  --rm \
  --env-file ".env"\
  -p 3200:3200 \
  -p 5433:5433 \
  --name=${server} \
  -v "$(pwd)":/app ${server} 

  
