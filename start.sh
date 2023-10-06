#!/bin/bash
api="3dbag-api"
docker container stop ${api} || true
docker build -t ${api} .
docker run \
  --platform linux/amd64\
  --rm \
  --env-file ".env"\
  -p 3200:3200 \
  -p 5433:5433 \
  --name=${api} \
  -v "$(pwd)":/app ${api} 

  
