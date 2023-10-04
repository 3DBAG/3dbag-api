"""OGC Features API backed by CityJSON

Copyright 2022 3DGI <info@3dgi.nl>
"""
import json
import logging
from pathlib import Path
from typing import List

import yaml
from cjdb.modules.exporter import Exporter
from flask import (abort, jsonify, make_response, render_template,
                   request, url_for)

from app import app, auth, db, db_users, index, parser
from app.parameters import Parameters, DEFAULT_CRS, STORAGE_CRS, DEFAULT_BBOX
from app.authentication import UserAuth, Permission

DEFAULT_LIMIT = 100
DEFAULT_OFFSET = 1

bbox_cache = index.BBOXCache()

conn = db.Db()
logging.debug("Collecting all available object ids.")
DEFAULT_FEATURE_SET = index.get_all_object_ids(conn)
conn.conn.close()


def load_cityjsonfeature_meta(featureId, connection):
    with Exporter(
        connection=connection.conn,
        schema="cjdb",
        sqlquery="SELECT object_id from cjdb.city_object limit 1",
        output=None,
    ) as exporter:
        exporter.get_data()
        metadata = exporter.get_metadata()
        logging.info(metadata)
    # TODO fix the BBOX
    return metadata


def load_cityjsonfeature(featureId, connection) -> str:
    """Loads a single feature."""
    with Exporter(
        connection=connection.conn,
        schema="cjdb",
        sqlquery=f"SELECT '{featureId}' as object_id",
        output=None,
    ) as exporter:
        exporter.get_data()
        feature = exporter.get_features()
    return json.loads(feature[0])


def load_cityjsonfeatures(featureIds: List[str], connection) -> str:
    """Loads a group of features."""
    feature_ids_str = str(
        [[x] for x in featureIds])[1:-1].replace("[", "(").replace("]", ")")
    print(feature_ids_str)
    with Exporter(
        connection=connection.conn,
        schema="cjdb",
        sqlquery=f"""VALUES {feature_ids_str}""",
        output=None,
    ) as exporter:
        exporter.get_data()
        features = exporter.get_features()
    return [json.loads(feature) for feature in features]


def get_paginated_features(features,
                           url: str,
                           connection,
                           parameters: Parameters
                           ):
    """From https://stackoverflow.com/a/55546722"""
    logging.debug(
        f"""Pagination started with limit {parameters.limit}
        and offset {parameters.offset}""")
    if parameters.bbox is not None:
        bbox = f"{parameters.bbox[0]},{parameters.bbox[1]},{parameters.bbox[2]},{parameters.bbox[3]}" # noqa
    nr_matched = len(features)
    # make response
    links = []
    obj = {"numberMatched": nr_matched}
    # make URLs
    links.append({
        "href": request.url,
        "rel": "self",
        "type": "application/city+json",
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
            "type": "application/city+json",
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
            "type": "application/city+json",
        })
    obj["type"] = 'FeatureCollection'
    obj["links"] = links
    # get features according to bounds
    if not all(features):
        obj["numberReturned"] = 0
        obj["features"] = []
    else:
        res = features[
            (parameters.offset - 1):(
                parameters.offset - 1 + parameters.limit)]
        logging.info(f"length {len(res)}")
        obj["numberReturned"] = len(res)
        obj["features"] = load_cityjsonfeatures(res, connection)
    return obj


@app.get('/')
def landing_page():
    return {
        "title": "3DBAG API",
        "description": "3DBAG is an extended version of the 3D BAG data set. It contains additional information that is either derived from the 3D BAG, or integrated from other data sources.", # noqa
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
                "title": "OGC API conformance classes implemented by this server" # noqa
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
    rdir = Path(app.root_path) / "schemas"
    with (rdir / "3dbagapi_spec.yaml").open("r") as fo:
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
            "https://www.cityjson.org/specs/1.1.1/"
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
            STORAGE_CRS
        ]
    }


@app.get('/collections/pand')
def pand():
    return {
        "id": "pand",
        "title": "Pand",
        "description": "3D building models based on the 'pand' layer of the BAG data set.",
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
                "crs": DEFAULT_CRS
            },
            "temporal": {
                "interval": [
                    None,
                    "2019-12-31T24:59:59Z"
                ]
            }
        },
        "itemType": "feature",
        "crs": [
            DEFAULT_CRS,
            STORAGE_CRS
        ],
        "storageCrs": STORAGE_CRS,
        "version": {
            "collection": "v2023.08.09",
            "api": "0.1"
        },
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
    # Validation
    for key in request.args.keys():
        if key not in ["bbox", "offset", "limit", "crs", "bbox-crs"]:
            error_msg = "Unknown parameter %s", key
            logging.error(error_msg)
            abort(400)

    query_params = Parameters(
        offset=request.args.get("offset", DEFAULT_OFFSET),
        limit=request.args.get("limit", DEFAULT_LIMIT),
        crs=request.args.get("crs", DEFAULT_CRS),
        bbox_crs=request.args.get("bbox-crs", DEFAULT_CRS),
        bbox=request.args.get("bbox", None)
    )
    conn = db.Db()

    if query_params.bbox:
        logging.debug("Getting Features inbbox")
        feature_subset = bbox_cache.get(conn, query_params.bbox)
        logging.debug("Got Features in bbox")

    else:
        logging.debug("Getting Features")
        feature_subset = DEFAULT_FEATURE_SET
        logging.debug("Got Features")

    logging.debug(f" Selection of {len(feature_subset)}  features.")
    response = make_response(jsonify(get_paginated_features(
        feature_subset,
        url_for("pand_items", _external=True), conn,
        query_params)), 200)
    response.headers["Content-Crs"] = f"<{query_params.crs}>"
    conn.conn.close()
    return response


@app.get('/collections/pand/items/<featureId>')
# @auth.login_required
def get_feature(featureId):
    for key in request.args.keys():
        if key not in ["crs"]:
            error_msg = """Unknown parameter %s.
                            For GET requests for specifics features
                            (/collections/pand/items/<featureId>)
                            only 'crs' is available.""", key
            logging.error(error_msg)
            abort(400)

    query_params = Parameters(
        offset=request.args.get("offset", DEFAULT_OFFSET),
        limit=request.args.get("limit", DEFAULT_LIMIT),
        crs=request.args.get("crs", DEFAULT_CRS),
        bbox_crs=request.args.get("bbox-crs", DEFAULT_CRS),
        bbox=request.args.get("bbox", None)
    )
    connection = db.Db()
    cityjsonfeature = load_cityjsonfeature(featureId, connection)

    links = [
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
        {
            "href": f'{url_for("pand", _external=True)}/items/{cityjsonfeature["id"]}',# noqa
            "rel": "parent",
            "type": "application/city+json"
        },
    ]
    for coid in cityjsonfeature["CityObjects"][cityjsonfeature["id"]]["children"]: # noqa
        links.append({
            "href": f'{url_for("pand", _external=True)}/items/{coid}',
            "rel": "child",
            "type": "application/city+json"
        })
    response = make_response(jsonify({
        "id": cityjsonfeature["id"],
        "feature": cityjsonfeature,
        "links": links
    }), 200)
    response.headers["Content-Crs"] = f"<{query_params.crs}>"

    return response


@app.route("/register", methods=["GET", "POST"])
# @auth.login_required(role=Permission.ADMINISTRATOR)
def register():
    user = UserAuth(**request.json)
    db_users.session.add(user)
    db_users.session.commit()
    return jsonify({"message": f"Registered user: {user.username}"})


if __name__ == '__main__':
    app.run(debug=True)
