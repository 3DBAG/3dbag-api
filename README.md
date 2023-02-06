# 3D BAG API

## Development server

To start a development server, you need data, and you need to configure the flask app.

Test data is available at https://data.3dgi.xyz/3dbag-api-test-data/3DBAGplus.tar.xz

Set the configuration with `APP_CONFIG="3dbag_api_settings.cfg"` environment variable.

The `start.sh` script starts a server in a docker container.

## User management

We store our users in database(s).
Probably PostgreSQL in production and SQLite for development.

We use [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/#a-minimal-application) for the ORM.

Create all the tables in the schema:

```python
import os
from app import db
os.environ["APP_CONFIG"] = "3dbag_api_settings.cfg"
db.create_all()
# db.drop_all()
```

### Schema

#### UserAuth

Stores the data for authenticating a user.

| Field name | Field type              | Constraints      |
|------------|-------------------------|------------------|
| id         | int                     | PK               |
| username   | string(80)              | unique, not null |
| password   | string(128)             | not null         |
| role       | enum(USER,ADMINSTRATOR) |                  |

New users are registered at the `/register` endpoint.
Only administrators can add new users, so you need to authorize as an admin (see *Security* below).

```shell
curl \
  --header "Content-Type: application/json" \
  --header "Authorization: Basic YmFsYXpzOjEyMzQ=" \
  --request POST \
  --data '{"username":"somebody", "password":"1234"}' \
  http://localhost:56733/register
```

New adminstrators are added in a python session.

```python
import os
from app import views, db
os.environ["APP_CONFIG"] = "3dbag_api_settings.cfg"
b = views.UserAuth(username="balazs", password="1234", role=views.Permission.ADMINISTRATOR)
db.session.add(b)
db.session.commit()
```

#### UserRegister

Stores additional information about a user that we use for analytics and user management.

| Field name      | Field type  | Constraints     |
|-----------------|-------------|-----------------|
| id              |             | PK              |
| userauth_id     |             | FK(userauth:id) |
| name            |             |                 |
| email           |             | not null        |
| date_registered | timestamptz | not null        |


## Security

We use HTTP Basic Authentication to secure the API.
The *Basic* authentication scheme (or "challenge") requires that the user credentials are the username and password, separated by a colon (`username:password`) and encoded using base64.
The base64 encoded credentials are sent in the `Authorisation` header, together with the authentication scheme.

The username and password string `balazs:1234` is `YmFsYXpzOjEyMzQ=` in base64.

In Python, base64 encoding works like this:

```python
import base64
base64.b64encode("balazs:1234".encode("utf-8"))
```

### Examples:

#### Curl

```shell
curl --header "Authorization: Basic YmFsYXpzOjEyMzQ=" http://localhost:56733/collections/pand/items
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
  -e APP_CONFIG="/app/3dbag_api_settings.cfg" \
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

## Performance

**Measurement methods** 

- Manual query in Firefox, refresh a couple of times. Check Firefox's Request Timing, [`Waiting` stage](https://firefox-source-docs.mozilla.org/devtools-user/network_monitor/request_details/#request-timing). Guesstimage the average Waiting time.
- Use the [`yappi`](https://github.com/sumerc/yappi) (or CProfile) profiler for profiling the instructions within endpoints (by running the tests).

### `/collections/pand/items?bbox`

*2022-08-24 f6cba0a6* – bbox: *75877.011,446130.034,92446.593,460259.369*, very large area in Den Haag, 234117167m2, 284462 features. Profiler: 3.3s because the test setup is very slow, because it needs to read things into memory (feature index etc), but these are one-time costs at starting up the application (600ms features_in_bbox). Firefox: ~1.3s on first query, 500ms on paging the response (10 features/page).

### `/collections/pand/items/{featureId}/surfaces`

*2022-08-25 c30c8b72* – featureId: *NL.IMBAG.Pand.1655100000548671-0* (last record in the surfaces csv). Profiler: ~240ms (40ms get_surfaces, but it can be as low as 6ms for features that are at the beginning of the csv), same performance on local and godzilla. Firefox: 400-500ms.

## License

All rights reserved by 3DGI v.o.f. You are not allowed to do anything with the repository without explicit agreement from 3DGI.