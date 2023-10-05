#!/bin/bash
server="3dbag-api.test"
docker container stop ${server} || true
docker build -t ${server} .
docker run \
  --platform linux/amd64\
  --rm \
  -p 3200:3200 \
  -p 5433:5433 \
  --name=${server} \
  -e APP_CONFIG="/app/3dbag_api_settings.cfg" \
  -v ${HOME}/data/3DBAGplus:/data/3DBAGplus \
  -v "$(pwd)":/app ${server} 
  
