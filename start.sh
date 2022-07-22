#!/bin/bash
server="3dbag-api.test"
docker build -t ${server} .
docker run -d -p 56733:80 \
  --name=${server} \
  -e API_CONFIG="/app/3dbag_api_settings.cfg" \
  -v /data/3DBAGplus:/data/3DBAGplus \
  -v "$(pwd)":/app ${server}
