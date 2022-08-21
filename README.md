# 3D BAG API

## Security

We use HTTP Basic Authentication to secure the API.

The user credentials are the username and password, separated by a colon (`username:password`) and encoded using base64.

### Examples:

#### Curl

```shell
curl -H "Authorization: Basic YmFsYXpzOjEyMzQ=" http://localhost:56733/collections/pand/items
```

## Dockerize the server

https://www.digitalocean.com/community/tutorials/how-to-build-and-deploy-a-flask-application-using-docker-on-ubuntu-20-04

## OGC Features API conformance

Tested with [OGC API - Features Conformance Test Suite](https://cite.opengeospatial.org/teamengine/about/ogcapi-features-1.0/1.0/site/).

### Local testing with docker

Pull the latest docker image

```shell
docker pull ogccite/ets-ogcapi-features10:latest
```

Start the testing service

```shell
docker run \
  -d \
  --name ogc-test \
  -p 8081:8080 \
  ogccite/ets-ogcapi-features10
```

Start the 3D BAG API service (from start.sh)

```shell
server="3dbag-api.test"
docker build -t ${server} .
docker run \
  -d \
  -p 56733:80 \
  --name=${server} \
  -e API_CONFIG="/app/3dbag_api_settings.cfg" \
  -v /data/3DBAGplus:/data/3DBAGplus \
  -v "$(pwd)":/app ${server}
```

Create a new bridge network where we can connect the two containers

```shell
docker network create 3dbag-api-net
```

Then connect the containers on the network

```shell
docker network connect 3dbag-api-net 3dbag-api.test
docker network connect 3dbag-api-net ogc-test
```

Then go to http://localhost:8081/teamengine/ in the browser and:

1. login with user and password 'ogctest'
2. create a new session from the list
3. choose 'OGC' organization then Specification 'OGC API - Features - 1.0'
4. choose the endpoint URL to test. This is http://3dbag-api.test
5. wait test execution and see the results from the validator

Note that in repeated tries, you need to always delete the validation session and restart from scratch, because the test suite caches the results.

## License

All rights reserved by 3DGI v.o.f. You are not allowed to do anything with the repository without explicit agreement from 3DGI.