#!/bin/bash
server="3dbag-api.test"
docker build -t ${server} .
docker run -d -p 56733:80 \
  --name=${server} \
  -e APP_CONFIG="/app/3dbag_api_settings_godzilla_docker.cfg" \
  -v /data/work/bdukai/3dbag:/data \
  -v "$(pwd)":/app ${server}