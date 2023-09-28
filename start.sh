#!/bin/bash
server="3dbag-api.test"
docker build -t ${server} .
docker run \
  --rm \
  -p 56733:80 \
  --name=${server} \
  -e APP_CONFIG="/app/3dbag_api_settings.cfg" \
  -v ${HOME}/data/3DBAGplus:/data/3DBAGplus \
  -v "$(pwd)":/app ${server} 
