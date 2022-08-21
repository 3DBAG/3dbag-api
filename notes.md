# Notes

## OGC Features API conformance

Tested with [OGC API - Features Conformance Test Suite](https://cite.opengeospatial.org/teamengine/about/ogcapi-features-1.0/1.0/site/).

However, their test suit sucks and the BBOX query for the /collections fails for whatever reason.
I asked about it in the Features gitter, but didn't get much help (2022 aug 17).
I tried changing the collection bbox coordinates to wgs84, because that's what is required by default, but nothing.
Someone suggested that I should debug the test suit to figure what's going wrong, but fuck that java shit. I rather skip the OGC conformance story.

Additionally, it seems that in order to be OGC conformant, we need to support,

- some WGS84 CRS as the default CRS
- temporal(datetime) queries.

Neither of these make sense for the 3D BAG, because of the location and because there are multiple time fields for each object.

## API authentication

There are two main types of API authentication, *API Keys* and *OAuth 2.0*.

It is simply not possible to hide an API key in a client side code.
Which is fine, if our customer only uses the API in house, for their own work.
If they create a product that uses our API, then either they ask each of their customers to get their own API key, or build their own backend that manages the api calls and hides the API key.
Still, API Keys are still fairly common, even Google Maps has API Keys.

Ref.: https://stackoverflow.com/a/64071013, https://stackoverflow.com/a/67214069.

All in all, I think it is fine if we use API keys, and we don't need to implement OAuth (yet).
Managing the key and keeping it secret is the responsibility of the client.


JWT + API key is possible
but maybe better just to keep things as simple as possible, since we are going to rewrite the api in rust anyway...i think
this includes the authentication too
and store the users in an sqlite database which we periodically backup
https://stackoverflow.com/a/39914013
use the `Authorization` header to pass access tokens
additionally, we can add IP restriction, so that the user can register a IP addresses where the token is allowed

### API keys

Only considered to be secure if used together with other security mechanisms such as HTTPS/SSL.

An additional security that is common with API keys is *key restriction*.
It is to restrict the API key usage to a given set of referer web sites.
For instance this is used [at google maps](https://developers.google.com/maps/documentation/javascript/get-api-key#restrict_key).

MDN resources:

- [HTTP Authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication#authentication_schemes)
- [Basic Authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/WWW-Authenticate#basic_authentication)
- [Configure Nginx for Basic authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication#restricting_access_with_nginx_and_basic_authentication)
- [Authorization](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Authorization)

Examples:

- [How to send API Keys to CARTO](https://carto.com/developers/auth-api/guides/how-to-send-API-Keys/). They prefer the HTTP Basic Authentication in the request header.

### OGC Features and OpenAPI schema

We can require the API key in either the header or as query parameter as well.

See the [OGC Features Security](https://docs.opengeospatial.org/is/17-069r4/17-069r4.html#security) and the [OpenAPI security schema](https://spec.openapis.org/oas/v3.0.3#security-scheme-object). 

