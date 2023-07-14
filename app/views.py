"""OGC Features API backed by CityJSON

Copyright 2022 3DGI <info@3dgi.nl>
"""
import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from sys import getsizeof
from typing import Optional, Tuple

import yaml
from flask import (abort, g, jsonify, make_response, render_template, request,
                   Request, url_for)
from pyproj import Proj, exceptions, transform
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from app import app, auth, db, db_users, index, parser

DEFAULT_LIMIT = 10
DEFAULT_OFFSET = 1

DEFAULT_CRS = "http://www.opengis.net/def/crs/OGC/0/CRS84h"
STORAGE_CRS = "https://www.opengis.net/def/crs/EPSG/0/7415"
DEFAULT_CRS_2D = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
STORAGE_CRS_2D = "http://www.opengis.net/def/crs/EPSG/0/28992"

GLOBAL_LIST_CRS = [DEFAULT_CRS, STORAGE_CRS, DEFAULT_CRS_2D, STORAGE_CRS_2D]

# Populate featureID cache (get all identificatie:tile_id into memory
conn = db.Db(dbfile=app.config["FEATURE_INDEX_GPKG"])
FEATURE_IDX = parser.feature_index(conn) # feature index of (featureId : tile_id)
conn.conn.close()
logging.debug(f"memory size of FEATURE_IDX: {getsizeof(FEATURE_IDX) / 1e6:.2f} Mb")
FEATURE_IDS = tuple(FEATURE_IDX.keys()) # featureID container
# Init empty BBOX cache of featureIDs
bbox_cache = index.BBOXCache()


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


@app.errorhandler(404)
def resource_not_found(e):
    e.description = (
        "The requested resource (or feature) does not exist on the server. "
        "For example, a path parameter had an incorrect value."
    )
    return jsonify(
        code=e.code,
        name=e.name,
        description=e.description
    ), 404


@auth.error_handler
def auth_error(status):
    if status == 401:
        error = dict(
            code=status,
            name="Unauthorized",
            description=(
                "The request requires user authentication. The response includes a "
                "WWW-Authenticate header field containing a challenge applicable to "
                "the requested resource."
            )
        )
    elif status == 403:
        error = dict(
            code=status,
            name="Forbidden",
            description=(
                "The server understood the request, but is refusing to fulfil it. "
                "While status code 401 indicates missing or bad authentication, status "
                "code 403 indicates that authentication is not the issue, but the "
                "client is not authorized to perform the requested operation on the "
                "resource."
            )
        )
    else:
        logging.error(
            "Flask-HTTPAuth error_handler is handling an error that is not 401 or 403.")
        error = dict(
            code=500,
            name="Internal Server Error",
            description=(
                "The server encountered an internal error and was unable to"
                " complete your request. Either the server is overloaded or"
                " there is an error in the application."
            )
        )
    return jsonify(error), status


class Permission(Enum):
    USER = 1
    ADMINISTRATOR = 16


class UserAuth(db_users.Model):
    __tablename__ = "userauth"

    id = db_users.Column(db_users.Integer, primary_key=True)
    username = db_users.Column(db_users.String(80), unique=True, nullable=False)
    # TODO: We should probably generate the API keys with os.urandom(24) as per https://realpython.com/token-based-authentication-with-flask/
    password_hash = db_users.Column(db_users.String(128), nullable=False)
    role = db_users.Column(db_users.Enum(Permission))

    def __init__(self, username, password, role=Permission.USER):
        self.username = username
        # TODO: require at least 12 mixed character long passwords from the user
        self.password = password
        self.role = role

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256:320000")

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_roles(self):
        return self.role


@auth.get_user_roles
def get_user_roles(user):
    return user.get_roles()


@auth.verify_password
def verify_password(username, password):
    if username == "":
        return None
    existing_user = UserAuth.query.filter_by(username=username).first()
    if not existing_user:
        return None
    g.current_user = username
    if existing_user.verify_password(password):
        return existing_user

@dataclass
class Parameters:
    """ Class for holding feature parameters"""
    offset: int
    limit: int
    crs: str
    bbox_crs: str
    bbox: Optional[Tuple[float, float, float, float]] = None


def get_validated_parameters(request: Request) -> Parameters:
    """ Returns the validated query parameters. 
    In case of invalid parameters of parameter values 
    an exception with 400 status code is raised """
    for key in request.args.keys():
        if key not in ["bbox", "offset", "limit", "crs", "bbox-crs"]:
            logging.error("Unknown parameter %s", key)
            abort(400)
    crs = request.args.get("crs", DEFAULT_CRS)
    bbox_crs = request.args.get("bbox-crs", DEFAULT_CRS_2D)
    if crs not in GLOBAL_LIST_CRS:
        logging.error("Unknown crs %s", crs)
        abort(400)
    if bbox_crs not in GLOBAL_LIST_CRS:
        logging.error("Unknown bbox-crs %s", bbox_crs)
        abort(400)
    try :
        limit = int(request.args.get("limit", DEFAULT_LIMIT))
        if limit < 0:
            logging.error("Limit must be an positive integer.")
            abort(400)
        offset = int(request.args.get("offset", DEFAULT_OFFSET))
        bbox=request.args.get("bbox", None)
        if bbox is not None:
            r = bbox.strip().strip("[]").split(',')
            if len(r) != 4:
                logging.error("BBox needs 4 parameters.")
                abort(400)
            bbox = tuple(list(map(float, r)))
        return Parameters(offset=offset, limit=limit, bbox=bbox, crs=crs, bbox_crs =bbox_crs)
    except ValueError as error:
        logging.error("Invalid parameter value")
        logging.error(error)
        abort(400)


def from_WGS84_to_dutchCRS(x: float, y: float)-> Tuple[float, float]:
    """ Transform a point from WGS84 to the Dutch Coordinate system (28992)"""
    return  transform(p1=Proj(init='OGC:CRS84'),
                      p2=Proj(init='epsg:28992'),
                      x=x,
                      y=y,
                      errcheck=True)

def from_dutchCRS_to_WGS84(x: float, y: float)-> Tuple[float, float]:
    """ Transform a point from the Dutch Coordinate system (28992) to WGS84"""
    return  transform(p1=Proj(init='epsg:28992'),
                      p2=Proj(init='OGC:CRS84'),
                      x=x,
                      y=y,
                      errcheck=True)

def transform_bbox(bbox: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    x1, y1 = from_WGS84_to_dutchCRS(bbox[0], bbox[1])
    x2, y2 = from_WGS84_to_dutchCRS(bbox[2], bbox[3])
    return (x1, y1, x2, y2)


def load_cityjsonfeature_meta(featureId):
    parent_id = parser.get_parent_id(featureId)
    tile_id = parser.get_tile_id(parent_id, FEATURE_IDX)
    if tile_id is None:
        logging.debug(f"featureId {parent_id} not found in feature_index")
        abort(404)

    json_path = parser.find_tile_meta_path(app.config["DATA_BASE_DIR"], tile_id)
    if not json_path.exists():
        logging.debug(f"CityJSON metadata file {json_path} not found ")
        abort(404)
    else:
        with json_path.open("r") as fo:
            return json.load(fo)


def load_cityjson_meta():
    json_path = parser.find_meta_path(app.config["DATA_BASE_DIR"])
    if not json_path.exists():
        logging.debug(f"CityJSON metadata file {json_path} not found ")
        abort(404)
    else:
        with json_path.open("r") as fo:
            return json.load(fo)


def load_cityjsonfeature(featureId):
    """Loads a single feature."""
    parent_id = parser.get_parent_id(featureId)
    tile_id = parser.get_tile_id(parent_id, FEATURE_IDX)
    if tile_id is None:
        logging.debug(f"featureId {parent_id} not found in feature_index")
        abort(404)

    json_path = parser.find_co_path(app.config["DATA_BASE_DIR"], parent_id, tile_id)
    if not json_path.exists():
        logging.debug(f"CityJSON file {json_path} not found ")
        abort(404)
    else:
        with json_path.open("r") as fo:
            return json.load(fo)


def get_paginated_features(features, url: str, parameters: Parameters):
    """From https://stackoverflow.com/a/55546722"""

    if parameters.bbox is not None:
        bbox = f"{parameters.bbox[0]},{parameters.bbox[1]},{parameters.bbox[2]},{parameters.bbox[3]}"
    nr_matched = len(features)
    # make response
    links = []
    obj = {"numberMatched": nr_matched}
    # make URLs
    links.append({
        "href": request.url,
        "rel": "self",
        "type": "application/geo+json",
        "title": "this document"
    })
    url_prev = url_next = f"{url}?"
    # make previous URL
    if parameters.offset > 1:
        offset_copy = max(1, parameters.offset - parameters.limit)
        limit_copy = parameters.offset - 1
        ol = f"offset={offset_copy:d}&limit={limit_copy:d}"
        if parameters.bbox is None:
            url_prev += ol
        else:
            url_prev += f"bbox={bbox}&" + ol
        links.append({
            "href": url_prev,
            "rel": "prev",
            "type": "application/geo+json",
        })
    # make next URL
    if parameters.offset + parameters.limit < nr_matched:
        offset_copy = parameters.offset + parameters.limit
        ol = f"offset={offset_copy:d}&limit={parameters.limit:d}"
        if parameters.bbox is None:
            url_next += ol
        else:
            url_next += f"bbox={bbox}&" + ol
        links.append({
            "href": url_next,
            "rel": "next",
            "type": "application/geo+json",
        })
    obj["type"] = 'FeatureCollection'
    obj["links"] = links
    # get features according to bounds
    if not all(features):
        obj["numberReturned"] = 0
        obj["features"] = []
    else:
        res = features[(parameters.offset - 1):(parameters.offset - 1 + parameters.limit)]
        obj["numberReturned"] = len(res)
        obj["features"] = [load_cityjsonfeature(featureId) for featureId in res]
    return obj


@app.get('/')
def landing_page():
    return {
        "title": "3D BAG plus",
        "description": "3D BAG plus is an extended version of the 3D BAG data set. It contains additional information that is either derived from the 3D BAG, or integrated from other data sources.",
        "links": [
            {
                "href": request.url,
                "rel": "self",
                "type": "application/json",
                "title": "this document"
            },
            {
                "href": url_for("api", _external=True),
                "rel": "service-desc",
                "type": "application/vnd.oai.openapi+json;version=3.0",
                "title": "the API definition"
            },
            {
                "href": url_for("api_html", _external=True),
                "rel": "service-doc",
                "type": "text/html",
                "title": "the API documentation"
            },
            {
                "href": url_for("conformance", _external=True),
                "rel": "conformance",
                "type": "application/json",
                "title": "OGC API conformance classes implemented by this server"
            },
            {
                "href": url_for("collections", _external=True),
                "rel": "data",
                "type": "application/json",
                "title": "Information about the feature collections"
            },
        ]
    }


@app.get('/api')
def api():
    rdir = Path(app.root_path).parent / "schemas"
    with (rdir / "3dbagplus_spec.yaml").open("r") as fo:
        f = yaml.full_load(fo)
    return jsonify(f)


@app.get('/api.html')
def api_html():
    return render_template("redoc_ui.html")


@app.get('/conformance')
def conformance():
    return {
        "conformsTo": [
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs",
            "https://www.cityjson.org/specs/1.1.1"
        ]
    }


@app.get('/collections')
def collections():
    return {
        "collections": [
            pand(),
        ],
        "links": [
            {
                "href": url_for("collections", _external=True),
                "rel": "self",
                "type": "application/json",
                "title": "this document"
            },
        ],
        "crs": [
            DEFAULT_CRS,
            STORAGE_CRS,
            DEFAULT_CRS_2D,
            STORAGE_CRS_2D
            ]
    }


@app.get('/collections/pand')
def pand():
    meta = load_cityjson_meta()
    return {
        "id": "pand",
        "title": meta["metadata"]["title"],
        "description": "the 3d bag pand layer",
        "extent": {
            "spatial": {
                "bbox": [
                    [
                        3.3335406283191253,
                        50.72794948839276,
                        7.391791169364946,
                        53.58254841348389
                    ]
                ],
                "crs": DEFAULT_CRS_2D
            },
            "temporal": {
                "interval": [
                    None,
                    "2019-12-31T24:59:59Z"
                ]
            }
        },
        "itemType": "feature",
        "crs":[
                DEFAULT_CRS,
                STORAGE_CRS
            ],
        "storageCrs": STORAGE_CRS,
        "transform": meta["transform"],
        "version": {
            "cityjson": meta["version"],
            "collection": meta["metadata"]["identifier"],
        },
        "referenceDate": meta["metadata"]["referenceDate"],
        "pointOfContact": meta["metadata"]["pointOfContact"],
        "links": [
            {
                "href": url_for("pand", _external=True),
                "rel": "self",
                "type": "application/json",
                "title": "this document"
            },
            {
                "href": url_for("pand_items", _external=True),
                "rel": "items",
                "type": "application/geo+json",
                "title": "Pand items"
            },
            {
                "href": "https://creativecommons.org/licenses/by/4.0/",
                "rel": "license",
                "type": "text/html",
                "title": "CC BY 4.0"
            },
            {
                "href": "https://creativecommons.org/licenses/by/4.0/rdf",
                "rel": "license",
                "type": "application/rdf+xml",
                "title": "CC BY 4.0"
            }
        ]
    }



@app.get('/collections/pand/items')
# @auth.login_required
def pand_items():
    query_params = get_validated_parameters(request)
    conn = db.Db(dbfile=app.config["FEATURE_INDEX_GPKG"])
    if query_params.bbox is not None:
        bbox = query_params.bbox
        try :
            if query_params.bbox_crs == DEFAULT_CRS_2D:
                bbox = transform_bbox(bbox)
            # tiles_matches = [TILES_SHAPELY[id(tile)][1] for tile in TILES_RTREE.query(bbox)]
            logging.debug(f"Query with bbox {bbox}")
            # TODO OPTIMIZE: use a connection pool instead of connecting each time. DB connection is very expensive.
            feature_subset = bbox_cache.get(conn, bbox)
        except exceptions.ProjError as e:
            logging.warning(f"Projection Error")
            logging.warning(e)
            feature_subset = ()
    else:
        feature_subset = FEATURE_IDS
    conn.conn.close()
    response = make_response(jsonify(get_paginated_features(feature_subset,
                                          url_for("pand_items", _external=True),
                                          query_params)), 200)
    response.headers["Content-Crs"] = f"<{query_params.crs}>"

    return response


@app.get('/collections/pand/items/<featureId>')
#@auth.login_required
def get_feature(featureId):
    crs = request.args.get("crs", DEFAULT_CRS)
    if crs not in GLOBAL_LIST_CRS:
        logging.error("Unknown crs %s", crs)
        abort(400)
    cityjsonfeature = load_cityjsonfeature(featureId)

    links = [
        {
            "href": request.url,
            "rel": "self",
            "type": "application/geo+json",
            "title": "this document"
        },
        {
            "href": url_for("pand", _external=True),
            "rel": "collection",
            "type": "application/geo+json"
        },
        {
            "href": f'{url_for("pand", _external=True)}/items/{cityjsonfeature["id"]}',
            "rel": "parent",
            "type": "application/geo+json"
        },
    ]
    for coid in cityjsonfeature["CityObjects"][cityjsonfeature["id"]]["children"]:
        links.append({
            "href": f'{url_for("pand", _external=True)}/items/{coid}',
            "rel": "child",
            "type": "application/geo+json"
        })
    response = make_response(jsonify({
        "id": cityjsonfeature["id"],
        "feature": cityjsonfeature,
        "links": links
    }), 200)
    response.headers["Content-Crs"] = f"<{crs}>"

    return response



@app.get('/collections/pand/items/<featureId>/addresses')
#@auth.login_required
def get_addresses(featureId):
    logging.debug(f"requesting {featureId} addresses")
    parent_id = parser.get_parent_id(featureId)
    tile_id = parser.get_tile_id(parent_id, FEATURE_IDX)
    if tile_id is None:
        logging.debug(f"featureId {parent_id} not found in feature_index")
        abort(404)

    try:
        csv_path = parser.find_addresses_csv_path(app.config["DATA_BASE_DIR"], tile_id)
        addresses_gen = parser.parse_addresses_csv(csv_path)
        # FIXME: here we need the BAG identifiactie, but for the surfaces records we need the 3D BAG building part identificatie
        # FIXME: a bag feature can have multiple childern in the 3d bag, thus we needto  return an array of children
        addresses_record = parser.get_feature_record(parent_id, addresses_gen)
    except BaseException as e:
        logging.exception(e)
        abort(500)

    if addresses_record is None:
        logging.debug(f"featureId {featureId} not found in the addresses records")
        abort(404)

    addresses_record["links"] = [
        {
            "href": request.url,
            "rel": "self",
            "type": "application/json",
            "title": "this document"
        },
        {
            "href": url_for("pand", _external=True),
            "rel": "collection",
            "type": "application/json"
        },
    ]

    return jsonify(addresses_record)


@app.get('/collections/pand/items/<featureId>/surfaces')
#@auth.login_required
def get_surfaces(featureId):
    logging.debug(f"requesting {featureId} surfaces")
    parent_id = parser.get_parent_id(featureId)
    tile_id = parser.get_tile_id(parent_id, FEATURE_IDX)
    if tile_id is None:
        logging.debug(f"featureId {parent_id} not found in feature_index")
        abort(404)

    try:
        csv_path = parser.find_surfaces_csv_path(app.config["DATA_BASE_DIR"], tile_id)
        surfaces_gen = parser.parse_surfaces_csv(csv_path)
        # FIXME: a bag feature can have multiple childern in the 3d bag, thus we needto  return an array of children
        # FIXME: we are querying with parent_ids in the api, not with children-ids, how make this work neatly?
        if featureId.find("-") < 0:
            # we have a parent_id, but we need a child-id, so let's make one...
            featureId += "-0"
        surfaces_record = parser.get_feature_record(featureId, surfaces_gen)
    except BaseException as e:
        logging.exception(e)
        abort(500)

    if surfaces_record is None:
        logging.debug(f"featureId {featureId} not found in the surfaces records")
        abort(404)

    surfaces_record["links"] = [
        {
            "href": request.url,
            "rel": "self",
            "type": "application/json",
            "title": "this document"
        },
        {
            "href": url_for("pand", _external=True),
            "rel": "collection",
            "type": "application/json"
        },
    ]

    return jsonify(surfaces_record)


@app.route("/register", methods=["GET", "POST"])
#@auth.login_required(role=Permission.ADMINISTRATOR)
def register():
    user = UserAuth(**request.json)
    db_users.session.add(user)
    db_users.session.commit()
    return jsonify({"message": f"Registered user: {user.username}"})


if __name__ == '__main__':
    app.run(debug=True)
